"""Which db-user may see which query (issue #76).

The settings live in the project folder, in ACCESS_FILE, so they travel with the
project (zip export/import, review copies):

    {"Preisliste": "*", "Bestellungen": ["leser", "kasse"]}

Keys are query names (file names without '.sql'), values are either ALL or a list of
db-user short names (the part after '<base>_' in the username). Queries that are not
listed are only visible to the db-admin. This replaces the old file-name convention
('leser_Bestellungen.sql' was only visible to '<base>_leser').
"""
import json
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager

from myapp.utils.sqlite_connector import DB_FILE, backup_db
from myapp.utils.directories import USER_DB_ROOT, fullpath, sqllock_get, sqllock_release

ACCESS_FILE = '_zugriff.json'
ALL = '*'
SQL_EXT = '.sql'
BACKUP_EXT = '.sql_bak'
DEFAULT_CATEGORY = 'Allgemein'


@contextmanager
def _locked(directory, lock_held=False):
    """Hold the folder lock while access settings or query names change.
    Callers that already hold it (e.g. api_sql, api_sql_list) pass lock_held=True; the lock is not reentrant."""
    if lock_held:
        yield
        return
    sqllock_get(directory)
    try:
        yield
    finally:
        sqllock_release(directory)


def _query_path(directory, name) -> str:
    return fullpath(directory, name + SQL_EXT)


def query_name(filename: str) -> str:
    """'Bestellungen.sql' -> 'Bestellungen'."""
    return filename[:-len(SQL_EXT)] if filename.endswith(SQL_EXT) else filename


def split_category(name):
    """'Kunden - Liste' -> ('Kunden', 'Liste'); 'Liste' -> ('Allgemein', 'Liste')."""
    if ' - ' in name:
        category, label = name.split(' - ', 1)
        return category, label
    return DEFAULT_CATEGORY, name


def list_queries(directory) -> list:
    """All query names of a project, sorted. Does not convert old projects (see list_converted_queries)."""
    if not os.path.isdir(directory):
        return []
    return sorted(query_name(f) for f in os.listdir(directory) if f.endswith(SQL_EXT))


# --------------------------------------------------------------------------------------
# Reading and writing the access file
# --------------------------------------------------------------------------------------

def _normalize(access) -> dict:
    """Keep only well-formed entries: ALL or a list of short names."""
    result = {}
    if not isinstance(access, dict):
        return result
    for query, value in access.items():
        if value == ALL:
            result[query] = ALL
        elif isinstance(value, list):
            names = sorted({n for n in value if isinstance(n, str) and n})
            if names:
                result[query] = names
    return result


def load_access(directory, lock_held=False) -> dict:
    """The access settings of a project. Old projects are converted on first read (under the folder lock)."""
    if not os.path.isdir(directory):
        return {}
    path = os.path.join(directory, ACCESS_FILE)
    if not os.path.exists(path):
        return convert_legacy_prefixes(directory, lock_held)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return _normalize(json.load(f))
    except (OSError, ValueError) as e:
        # A broken file hides everything (safe default). It is not converted again,
        # because that would rename the queries a second time.
        print(f"Reading {path} failed: {e}")
        return {}


def save_access(directory, access) -> dict:
    """Write the access settings. Entries for queries that no longer exist are dropped."""
    existing = set(list_queries(directory))
    access = {q: v for q, v in _normalize(access).items() if q in existing}
    path = os.path.join(directory, ACCESS_FILE)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(access, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)  # atomic: readers never see a half-written file
    return access


def list_converted_queries(directory) -> list:
    """All query names, after converting an old project (the db-admin then sees the new names)."""
    load_access(directory)
    return list_queries(directory)


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------

def can_see(access, query, short_name) -> bool:
    value = access.get(query)
    return value == ALL or (isinstance(value, list) and short_name in value)


def visible_queries(directory, short_name) -> list:
    """The query names a db-user may see."""
    access = load_access(directory)
    return [q for q in list_queries(directory) if can_see(access, q, short_name)]


# --------------------------------------------------------------------------------------
# Keeping the file in sync with the queries
# --------------------------------------------------------------------------------------

def rename_query(directory, old, new, lock_held=False):
    """Rename a query file and move its access entry along."""
    old, new = query_name(old), query_name(new)
    src, dst = _query_path(directory, old), _query_path(directory, new)
    with _locked(directory, lock_held):
        if not os.path.exists(src):
            raise FileNotFoundError(old)
        if os.path.exists(dst):
            raise FileExistsError(new)
        access = load_access(directory, lock_held=True)
        os.rename(src, dst)
        if old in access:
            access[new] = access.pop(old)
        save_access(directory, access)


def remove_query(directory, name, lock_held=False):
    """Drop the access entry of a deleted query (the file itself is deleted by the caller)."""
    with _locked(directory, lock_held):
        access = load_access(directory, lock_held=True)
        if access.pop(query_name(name), None) is not None:
            save_access(directory, access)


# --------------------------------------------------------------------------------------
# Conversion of the old file-name convention
# --------------------------------------------------------------------------------------

def _plan_legacy_renames(names):
    """Returns (access, renames) for the old convention.

    'X'        -> visible to all
    'P_Rest'   -> renamed to 'Rest', visible to 'P'
    If 'Rest' is already taken, the query keeps its old name (still only visible to 'P').
    """
    access = {}
    renames = {}
    taken = set(names)
    for name in names:
        if '_' not in name:
            access[name] = ALL
            continue
        prefix, rest = name.split('_', 1)
        if not prefix or not rest:
            continue  # '_x' / 'x_' were visible to nobody but the db-admin; stays that way
        if rest in taken:
            access[name] = [prefix]
        else:
            taken.add(rest)
            renames[name] = rest
            access[rest] = [prefix]
    return access, renames


def _backup(directory, name, backed_up):
    """Copy '<name>.sql' to '<name>.sql_bak' once (an existing backup is never overwritten)."""
    if name in backed_up:
        return
    target = fullpath(directory, name + BACKUP_EXT)
    if not os.path.exists(target):
        shutil.copy2(_query_path(directory, name), target)
    backed_up.add(name)


def _rewrite_subquery_references(directory, renames, backed_up):
    """'<<P_Rest>>' (or '<<P_Rest.sql>>') -> '<<Rest>>' in every query."""
    for name in list_queries(directory):
        path = _query_path(directory, name)
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        new_sql = sql
        for old, new in renames.items():
            new_sql = new_sql.replace(f'<<{old}{SQL_EXT}>>', f'<<{new}>>').replace(f'<<{old}>>', f'<<{new}>>')
        if new_sql != sql:
            _backup(directory, name, backed_up)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_sql)


def convert_legacy_prefixes(directory, lock_held=False) -> dict:
    """Turn the old file-name convention into an access file (runs once per project).

    Every file is backed up as '<name>.sql_bak' before it is renamed or changed.
    Runs under the folder lock (lock_held=True if the caller has it already). After taking
    the lock it checks again whether another request has converted the project meanwhile.
    """
    with _locked(directory, lock_held):
        if os.path.exists(os.path.join(directory, ACCESS_FILE)):
            return load_access(directory, lock_held=True)
        access, renames = _plan_legacy_renames(list_queries(directory))
        backed_up = set()
        for old, new in renames.items():
            _backup(directory, old, backed_up)
            os.rename(_query_path(directory, old), _query_path(directory, new))
            backed_up.add(new)  # its content is already backed up under the old name
        if renames:
            _rewrite_subquery_references(directory, renames, backed_up)
        return save_access(directory, access)


# --------------------------------------------------------------------------------------
# Import of a project zip
# --------------------------------------------------------------------------------------

def _read(path) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def _safe_extract(zip_ref, target):
    """Extract a zip into `target`; entries that would leave the folder (zip slip) are refused."""
    base = os.path.abspath(target) + os.sep
    for info in zip_ref.infolist():
        if not os.path.abspath(os.path.join(target, info.filename)).startswith(base):
            raise ValueError(f"Invalid path in zip: {info.filename}")
    zip_ref.extractall(target)


def import_zip(directory, zip_file):
    """Import a project zip into `directory`, under the folder lock.

    - The zip is extracted into a temp folder first. A zip without access file (old project)
      is converted there, so only its queries are renamed, never the existing ones.
    - An existing query that the zip overwrites with different content is saved as '<name>.sql_bak'
      (replacing an older backup).
    - Access entries are merged: existing ones stay, the zip's entries win for its own queries.
    """
    os.makedirs(directory, exist_ok=True)
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        os.makedirs(USER_DB_ROOT, exist_ok=True)
        temp = tempfile.mkdtemp(prefix='~import_', dir=USER_DB_ROOT)  # '~' never collides with a user folder
        try:
            _safe_extract(zip_ref, temp)
            if ACCESS_FILE not in zip_ref.namelist():
                convert_legacy_prefixes(temp, lock_held=True)  # nobody else can see the temp folder
            with _locked(directory):
                _merge_import(temp, directory)
        finally:
            shutil.rmtree(temp, ignore_errors=True)


def _merge_import(temp, directory):
    """Copy the extracted zip over the project and merge the access files (caller holds the lock)."""
    zip_access = load_access(temp, lock_held=True)
    access = load_access(directory, lock_held=True)
    for root, _dirs, files in os.walk(temp):
        for file in files:
            source = os.path.join(root, file)
            relative = os.path.relpath(source, temp)
            if relative in (ACCESS_FILE, 'lockfile'):
                continue  # the access file is merged below, the lockfile belongs to this server
            target = fullpath(directory, relative)
            if relative.endswith(SQL_EXT) and os.path.exists(target) and _read(target) != _read(source):
                shutil.copy2(target, target[:-len(SQL_EXT)] + BACKUP_EXT)
            if relative == DB_FILE:
                backup_db(directory)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
    access.update(zip_access)
    save_access(directory, access)
