
from datetime import datetime
from io import BytesIO
import os
import shutil
import time
import zipfile
from django.core.files.base import ContentFile
from myapp.models import ZippedFolder


def get_user_directory(username) -> str:
    if '_' in username:
        username = username.split('_')[0]
    return f"user_databases/{username}/"

def get_user_suffix(username) -> str:
    if '_' in username and not username.endswith('_admin'):
        return username.split('_')[1]
    return ''


def zip_and_save_directory(directory_path:str, delete:bool=True, storeToDB:bool=False) -> ContentFile:
    # Create a zip file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                abs_path = os.path.join(root, file)
                relative_path = os.path.relpath(abs_path, start=directory_path)
                zipf.write(abs_path, arcname=relative_path)
    memory_file.seek(0)

    # Save to model
    if(storeToDB):
        zipped = ZippedFolder(name=directory_path)
        zipped.zip_file.save(f"{directory_path}export.zip", ContentFile(memory_file.read()))
        zipped.save()

    if delete:
        try:
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path) 
        except Exception as e:
            print(f"Error removing directory: {e}")
    
    return ContentFile(memory_file.read())

def restore_zip_to_directory(target_directory) -> bool:
    try:
        # Fetch the zip entry from the DB
        zipped = ZippedFolder.objects.get(pk=target_directory)
        zip_path = zipped.zip_file.path

        if os.path.exists(target_directory):
            shutil.rmtree(target_directory)  # Remove existing directory if it exists

        # Ensure target directory exists
        os.makedirs(target_directory, exist_ok=True)

        # Extract zip contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_directory)
        os.remove(zip_path)  # Remove the zip file after extraction

        return True
    except ZippedFolder.DoesNotExist:
        print("Zip record not found in database.")
        return False
    except Exception as e:
        print(f"Error during restoration: {e}")
        return False
    

def get_directory_tree_with_sizes(directory) -> list[dict[str, str]]:
    tree = []

    sum_size = 0
    last = ''

    for root, dirs, files in os.walk(directory):
        #dirs.append(directory)
        for name in dirs:
            dir_path = os.path.join(root, name)
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(dir_path)
                for filename in filenames
            )
            sum_size += size
            last_edited = datetime.fromtimestamp(os.path.getmtime(dir_path)).strftime('%Y-%m-%d %H:%M')
            if last_edited > last:
                last = last_edited
            size_kb = str(round(size / 1000, 1)) +' kB' 
            tree.append({'type': 'directory', 'name': name, 'size': size_kb, 'last_modified': last_edited})
    
    tree.insert(0,{'type': 'directory', 'name': '_SUMME_', 'size': str(round(sum_size / 1000000, 1))+' MB', 'last_modified': last})
    #tree.sort()
        #for name in files:
        #    file_path = os.path.join(root, name)
        #    size = os.path.getsize(file_path)
        #    last_edited = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        #    size_kb = round(size / 1024, 2)
        #    tree.append({'type': 'file', 'name': name, 'size': size_kb, 'last_modified': last_edited})
    return tree


def sqllock_get(dir) -> None:
    lockfile_name = f'{dir}/lockfile'
    while os.path.exists(lockfile_name):
        time.sleep(0.1)
    lockFile = open(f'{dir}/lockfile', 'w')
    lockFile.close()

def sqllock_release(dir) -> None:
    lockfile_name = f'{dir}/lockfile'
    if os.path.exists(lockfile_name):
        os.remove(lockfile_name)

def fullpath(dir:str,file:str) -> str:
    normalizedPath = os.path.normpath(os.path.join(dir, file))
    if not normalizedPath.startswith(os.path.normpath(dir)):
        raise Exception("Invalid file path. Access denied.")
    return normalizedPath
