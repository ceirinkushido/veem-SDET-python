import os
from tempfile import TemporaryDirectory
import time
import pytest
import sync_folders
import hashlib
import shutil
from multiprocessing import Process
from pathlib import Path
from tempfile import TemporaryDirectory

@pytest.fixture
def setup_folders():
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        source_folder = temp_dir / 'source'
        destination_folder = temp_dir / 'destination'
        log_file = temp_dir / 'log.txt'
        sync_interval = 1

        source_folder.mkdir()
        destination_folder.mkdir()

        yield str(source_folder), str(destination_folder), str(log_file), sync_interval


def run_sync_folders(source_folder, destination_folder, log_file, sync_interval):
    p = Process(target=sync_folders.sync_folders, args=(source_folder, destination_folder, log_file, sync_interval))
    p.start()

    # Wait for the sync interval to pass and then terminate the process
    time.sleep(sync_interval + 1)
    p.terminate()
    p.join()

def test_md5_validation(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a file in the source folder
    source_file_path = os.path.join(source_folder, "file1.txt")
    with open(source_file_path, 'w') as f:
        f.write("Test content")

    # Calculate MD5 hash of the source file
    with open(source_file_path, 'rb') as f:
        source_file_hash = hashlib.md5(f.read()).hexdigest()

    # Run sync_folders
    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Calculate MD5 hash of the copied file in the destination folder
    destination_file_path = os.path.join(destination_folder, "file1.txt")
    with open(destination_file_path, 'rb') as f:
        destination_file_hash = hashlib.md5(f.read()).hexdigest()

    # Check that the MD5 hash of the source and destination files are the same
    assert source_file_hash == destination_file_hash, "MD5 hash of source and destination files do not match"

def test_log_file_is_created(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Check if log file is created and has content
    assert os.path.exists(log_file)
    assert open(log_file).read() != ""

def test_files_are_updated(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Modify a file in source folder
    open(os.path.join(source_folder, "file1.txt"), 'w').write("new content")

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Check if file is updated in destination folder
    assert open(os.path.join(destination_folder, "file1.txt")).read() == "new content"

def test_files_are_removed(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a file in the destination folder
    destination_file_path = os.path.join(destination_folder, "file1.txt")
    with open(destination_file_path, 'w') as f:
        f.write("Test content")

    # Run sync_folders
    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Check that the file has been removed from the destination folder
    assert not os.path.exists(destination_file_path), "sync_folders did not remove the file from the destination folder"

def calculate_md5(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def test_files_are_copied(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a file in the source folder
    with open(os.path.join(source_folder, "file1.txt"), 'w') as f:
        f.write("Test content")

    # Run sync_folders
    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Check that the file has been copied to the destination folder
    with open(os.path.join(destination_folder, "file1.txt"), 'r') as f:
        assert f.read() == "Test content", "sync_folders did not copy the file from the source to the destination folder"

def test_empty_source_directory(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Make source directory empty
    for filename in os.listdir(source_folder):
        os.remove(os.path.join(source_folder, filename))

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Assert that destination directory is also empty
    assert not os.listdir(destination_folder)

def test_large_files(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a large file in source directory
    with open(os.path.join(source_folder, "large_file.txt"), 'w') as f:
        f.write('0' * 1024 * 1024 * 10)  # 10 MB

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Assert that large file is copied to destination directory
    assert os.path.exists(os.path.join(destination_folder, "large_file.txt"))

def test_many_files(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create many files in source directory
    for i in range(1000):
        with open(os.path.join(source_folder, f"file{i}.txt"), 'w') as f:
            f.write(str(i))

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Assert that all files are copied to destination directory
    assert len(os.listdir(destination_folder)) == 1000

def test_non_existent_source_directory(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Remove source directory
    shutil.rmtree(source_folder)

    # Assert that running sync_folders doesn't raise an exception
    try:
        run_sync_folders(source_folder, destination_folder, log_file, sync_interval)
    except Exception:
        assert False, "sync_folders raised an exception with a non-existent source directory"

def test_non_existent_destination_directory(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Remove destination directory
    shutil.rmtree(destination_folder)

    # Assert that running run_sync_folders doesn't raise an exception
    try:
        run_sync_folders(source_folder, destination_folder, log_file, sync_interval)
    except Exception:
        assert False, "run_sync_folders raised an exception with a non-existent destination directory"

def test_same_name_different_content(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a file in the source folder
    with open(os.path.join(source_folder, "file1.txt"), 'w') as f:
        f.write("hello")

    # Create a file in destination directory with the same name as a source file, but different content
    with open(os.path.join(destination_folder, "file1.txt"), 'w') as f:
        f.write("different content")

    # Run sync_folders
    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Assert that destination file is overwritten with source file
    with open(os.path.join(destination_folder, "file1.txt")) as f:
        assert f.read() == "different content", "Destination file was not overwritten with source file"

def test_read_only_files(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a read-only file in source directory
    read_only_file = os.path.join(source_folder, "read_only_file.txt")
    with open(read_only_file, 'w') as f:
        f.write("read only")
    os.chmod(read_only_file, 0o444)

    # Assert that running sync_folders doesn't raise an exception
    try:
        run_sync_folders(source_folder, destination_folder, log_file, sync_interval)
    except Exception:
        assert False, "sync_folders raised an exception with a read-only source file"

def test_files_being_used(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Create a file in the source folder
    with open(os.path.join(source_folder, "file1.txt"), 'w') as f:
        f.write("Test content")

    # Open a source file
    f = open(os.path.join(source_folder, "file1.txt"))

    # Assert that running sync_folders doesn't raise an exception
    try:
        run_sync_folders(source_folder, destination_folder, log_file, sync_interval)
    except Exception:
        assert False, "sync_folders raised an exception with a file being used"

    # Close the file
    f.close()

def test_error_logging(setup_folders):
    source_folder, destination_folder, log_file, sync_interval = setup_folders

    # Remove source directory to cause an error
    shutil.rmtree(source_folder)

    run_sync_folders(source_folder, destination_folder, log_file, sync_interval)

    # Assert that an error message was logged
    with open(log_file, 'r') as f:
        log_contents = f.read()
    assert f"Error: Source folder {source_folder} does not exist." in log_contents

def test_file_creation():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a file in the source_folder
            with open(os.path.join(source_folder, 'test.txt'), 'w') as f:
                f.write('test')

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if file was created in destination_folder
            assert os.path.exists(os.path.join(destination_folder, 'test.txt'))

def test_file_modification():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a file in the source_folder
            with open(os.path.join(source_folder, 'test.txt'), 'w') as f:
                f.write('test')

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Modify the file in the source_folder
            with open(os.path.join(source_folder, 'test.txt'), 'w') as f:
                f.write('modified test')

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if file was modified in destination_folder
            with open(os.path.join(destination_folder, 'test.txt'), 'r') as f:
                assert f.read() == 'modified test'

def test_file_deletion():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a file in the source_folder
            with open(os.path.join(source_folder, 'test.txt'), 'w') as f:
                f.write('test')

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Delete the file in the source_folder
            os.remove(os.path.join(source_folder, 'test.txt'))

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if file was deleted in destination_folder
            assert not os.path.exists(os.path.join(destination_folder, 'test.txt'))

def test_nested_directory_deletion():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a nested directory in the source_folder
            os.makedirs(os.path.join(source_folder, 'dir1', 'dir2'))

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Delete the nested directory in the source_folder
            shutil.rmtree(os.path.join(source_folder, 'dir1', 'dir2'))

            # Perform synchronization
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if nested directory was deleted in destination_folder
            assert not os.path.exists(os.path.join(destination_folder, 'dir1', 'dir2'))
            
def test_nested_directory_creation():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a nested directory in the source_folder
            os.makedirs(os.path.join(source_folder, 'dir1', 'dir2'))

            # Run sync_folders
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if nested directory was created in destination_folder
            assert os.path.exists(os.path.join(destination_folder, 'dir1', 'dir2')), "Nested directory was not created in destination folder"

def test_nested_directory_modification():
    with TemporaryDirectory() as source_folder:
        with TemporaryDirectory() as destination_folder:
            # Create a nested directory in the source_folder
            os.makedirs(os.path.join(source_folder, 'dir1', 'dir2'))

            # Run sync_folders
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Rename the nested directory in the source_folder
            os.rename(os.path.join(source_folder, 'dir1', 'dir2'), os.path.join(source_folder, 'dir1', 'dir3'))

            # Run sync_folders
            run_sync_folders(source_folder, destination_folder, 'log.txt', 1)

            # Check if nested directory was renamed in destination_folder
            assert os.path.exists(os.path.join(destination_folder, 'dir1', 'dir3')), "Nested directory was not renamed in destination folder"