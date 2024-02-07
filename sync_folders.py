'''
This script implement a synch between two folders.

Synchronization must be one-way: after the synchronization content of the
replica folder should be modified to exactly match content of the source
folder.

Synchronization should be performed periodically.
File creation/copying/removal operations should be logged to a file and to the
console output.

Folder paths, synchronization interval and log file path should be provided
using the command line arguments.

It is undesirable to use third-party libraries that implement folder
synchronization.

It is allowed (and recommended) to use external libraries implementing other
well-known algorithms. For example, there is no point in implementing yet
another function that calculates MD5 if you need it for the task and it is
perfectly acceptable to use a third-party (or built-in) library.
'''

import os
import sys
import time
import shutil
import hashlib

def sync_folders(source_folder, destination_folder, log_file, sync_interval):
    # Check if source folder exists
    if not os.path.exists(source_folder):
        with open(log_file, 'a') as f:
            f.write(f"Error: Source folder {source_folder} does not exist.\n")
        return

    with open(log_file, 'a') as log:
        log.write(f"Sync Parameters: Source Folder - {source_folder}, Destination Folder - {destination_folder}, Sync Interval - {sync_interval} seconds\n")

    while True:
        create_count = 0
        modify_count = 0
        delete_count = 0
        source_dirs = []
        source_files = []

        # First, replicate the directory structure
        for root, dirs, _ in os.walk(source_folder):
            for dir_ in dirs:
                source_dir_path = os.path.join(root, dir_)
                dest_dir_path = source_dir_path.replace(source_folder, destination_folder)
                source_dirs.append(source_dir_path)
                
                if not os.path.exists(dest_dir_path):
                    os.makedirs(dest_dir_path)
                    create_count += 1

        # Then, copy the files
        for root, _, files in os.walk(source_folder):
            for file in files:
                source_file_path = os.path.join(root, file)
                dest_file_path = source_file_path.replace(source_folder, destination_folder)
                source_files.append(source_file_path)

                if not os.path.exists(dest_file_path) or os.path.getmtime(source_file_path) > os.path.getmtime(dest_file_path):
                    shutil.copy2(source_file_path, dest_file_path)
                    if os.path.exists(dest_file_path):
                        modify_count += 1
                    else:
                        create_count += 1

        destination_dirs = [os.path.join(root, dir_) for root, dirs, _ in os.walk(destination_folder) for dir_ in dirs]
        for dir_ in destination_dirs:
            if dir_.replace(destination_folder, source_folder) not in source_dirs:
                shutil.rmtree(dir_)
                delete_count += 1

        for root, dirs, files in os.walk(destination_folder):
            for file in files:
                dest_file_path = os.path.join(root, file)
                if dest_file_path.replace(destination_folder, source_folder) not in source_files:
                    os.remove(dest_file_path)
                    delete_count += 1

        with open(log_file, 'a') as log:
            log.write(f"Operations: Created {create_count} files/directories, Modified {modify_count} files, Deleted {delete_count} files/directories\n")
            for file in source_files:
                dest_file_path = file.replace(source_folder, destination_folder)
                with open(file, 'rb') as f:
                    source_hash = hashlib.md5(f.read()).hexdigest()
                with open(dest_file_path, 'rb') as f:
                    dest_hash = hashlib.md5(f.read()).hexdigest()
                log.write(f"MD5 Validation: File {file} - Source: {source_hash}, Destination: {dest_hash}\n")

        print(f"Operations: Created {create_count} files/directories, Modified {modify_count} files, Deleted {delete_count} files/directories")
        for file in source_files:
            dest_file_path = file.replace(source_folder, destination_folder)
            with open(file, 'rb') as f:
                source_hash = hashlib.md5(f.read()).hexdigest()
            with open(dest_file_path, 'rb') as f:
                dest_hash = hashlib.md5(f.read()).hexdigest()
            print(f"MD5 Validation: File {file} - Source: {source_hash}, Destination: {dest_hash}\n")

        time.sleep(sync_interval)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python sync_folders.py <source_folder> <destination_folder> <log_file> <sync_interval>")
        sys.exit(1)
    
    source_folder = sys.argv[1]
    destination_folder = sys.argv[2]
    log_file = sys.argv[3]
    sync_interval = int(sys.argv[4])
    
    if not all([source_folder, destination_folder, log_file, sync_interval]):
        print("All command line arguments are required")
        print("Usage: python sync_folders.py <source_folder> <destination_folder> <log_file> <sync_interval>")
        sys.exit(1)
    
    sync_folders(source_folder, destination_folder, log_file, sync_interval)