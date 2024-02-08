import schedule
import os
import sys
import time
import shutil
import hashlib
import logging
from pathlib import Path

def compute_hash(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The SHA-256 hash of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If an error occurs while opening or reading the file.
    """
    try:
        with open(file_path, 'rb') as f:
            hash_sha256 = hashlib.sha256()
            for chunk in iter(lambda: f.read(8192), b''):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Invalid file path: {file_path}") from e
    except OSError as e:
        logging.error(f"Error computing SHA-256 for file {file_path}: {str(e)}")
        raise e

def copy_new_files(source_folder, destination_folder):
    """
    Copy new files from the source folder to the destination folder.

    Args:
        source_folder (str): The path to the source folder.
        destination_folder (str): The path to the destination folder.

    Returns:
        tuple: A tuple containing the count of newly created files and modified files.

    Raises:
        None

    """
    create_count = 0
    modify_count = 0
    for root, dirs, files in os.walk(source_folder):
        for dir in dirs:
            source_dir_path = Path(root) / dir
            dest_dir_path = Path(destination_folder) / source_dir_path.relative_to(source_folder)
            if not dest_dir_path.exists():
                dest_dir_path.mkdir(parents=True, exist_ok=True)
                create_count += 1
        for file in files:
            source_file_path = Path(root) / file
            dest_file_path = Path(destination_folder) / source_file_path.relative_to(source_folder)
            if not dest_file_path.exists():
                shutil.copy2(source_file_path, dest_file_path)
                create_count += 1    # increment create_count when a new file is copied
            elif source_file_path.stat().st_mtime > dest_file_path.stat().st_mtime:
                shutil.copy2(source_file_path, dest_file_path)
                modify_count += 1    # increment modify_count when an existing file is modified
    return create_count, modify_count

def delete_removed_files(source_folder, destination_folder):
    """
    Delete files and directories in the destination folder that do not exist in the source folder.

    Parameters:
    - source_folder (str): The path to the source folder.
    - destination_folder (str): The path to the destination folder.

    Returns:
    - delete_count (int): The number of files and directories deleted.

    """
    source_folder_path = Path(source_folder)
    if not source_folder_path.exists():
        return 0
    
    delete_count = 0
    for root, dirs, files in os.walk(destination_folder, topdown=False):
        for file in files:
            dest_file_path = Path(root) / file
            source_file_path = Path(source_folder) / dest_file_path.relative_to(destination_folder)
            if not source_file_path.exists():
                dest_file_path.unlink()
                delete_count += 1
        for dir in dirs:
            dest_dir_path = Path(root) / dir
            source_dir_path = Path(source_folder) / dest_dir_path.relative_to(destination_folder)
            if not source_dir_path.exists():
                os.rmdir(dest_dir_path)
                delete_count += 1
    return delete_count

def sync_folders(source_folder, destination_folder, sync_interval, log_file):
    """
    Synchronize folders by copying new files, deleting removed files, and performing MD5 validation.

    Args:
        source_folder (str): The path to the source folder.
        destination_folder (str): The path to the destination folder.
        sync_interval (int): The interval in seconds at which to synchronize the folders.
        log_file (str): The path to the log file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the source folder or destination folder does not exist.
    """
    source_folder = Path(source_folder)
    destination_folder = Path(destination_folder)
    
    if not source_folder.exists():
        logging.error(f"Source folder {source_folder} does not exist.")
        print(f"Source folder {source_folder} does not exist.")
        raise FileNotFoundError(f"Source folder {source_folder} does not exist.")
    if not destination_folder.exists():
        logging.error(f"Destination folder {destination_folder} does not exist.")
        print(f"Destination folder {destination_folder} does not exist.")
        raise FileNotFoundError(f"Destination folder {destination_folder} does not exist.")

    logging.basicConfig(filename=log_file, level=logging.INFO)

    def sync_job():
        create_count, modify_count = copy_new_files(source_folder, destination_folder)
        delete_count = delete_removed_files(source_folder, destination_folder)
    
        log_message = f"Operations: Created {create_count} files/directories, Modified {modify_count} files, Deleted {delete_count} files/directories"
        logging.info(log_message)
        print(log_message)
    
        for file in source_folder.rglob('*'):
            if file.is_file():
                dest_file_path = destination_folder / file.relative_to(source_folder)
                if dest_file_path.exists():
                    source_hash = compute_hash(file)
                    dest_hash = compute_hash(dest_file_path)
                    if source_hash != dest_hash:
                        log_message = f"MD5 Validation: File {file} - Source: {source_hash}, Destination: {dest_hash}"
                        logging.info(log_message)
                        print(log_message)

    schedule.every(sync_interval).seconds.do(sync_job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python sync_folders.py <source_folder> <destination_folder> <sync_interval> <log_file>")
        sys.exit(1)
    
    source_folder = sys.argv[1]
    destination_folder = sys.argv[2]
    log_file = sys.argv[4]
    try:
        sync_interval = int(sys.argv[3])
    except ValueError:
        print("Sync interval must be an integer.")
        sys.exit(1)
    
    sync_folders(source_folder, destination_folder, sync_interval, log_file)
