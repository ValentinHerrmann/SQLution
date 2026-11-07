"""Tests for the folder lock (sqllock_get / sqllock_release)."""
import os
import time

import pytest

import myapp.utils.directories as directories


def test_lock_creates_and_releases_lockfile(tmp_path):
    directories.sqllock_get(str(tmp_path))
    assert (tmp_path / 'lockfile').exists()
    directories.sqllock_release(str(tmp_path))
    assert not (tmp_path / 'lockfile').exists()


def test_lock_is_exclusive_and_times_out(tmp_path):
    directories.sqllock_get(str(tmp_path))
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        directories.sqllock_get(str(tmp_path), timeout=0.3)
    assert time.monotonic() - start < 3
    assert (tmp_path / 'lockfile').exists()  # the holder's lock is untouched


def test_stale_lock_is_removed(tmp_path):
    lockfile = tmp_path / 'lockfile'
    lockfile.write_text('')
    old = time.time() - 60
    os.utime(lockfile, (old, old))
    directories.sqllock_get(str(tmp_path), timeout=1)
    assert lockfile.exists()
    assert time.time() - os.stat(lockfile).st_mtime < 30  # a fresh lockfile now
