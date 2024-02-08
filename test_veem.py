import os
import time
import shutil
import pytest
import hashlib
import multiprocessing
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from sync_folders import compute_md5 , copy_new_files, delete_removed_files, sync_folders


class TestComputeMD5:
    def test_compute_md5_correct_hash(self):
        # Create a temporary file with known content
        with NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"Hello, world!")
            tmpfile_path = tmpfile.name

        # Compute MD5 hash of the temporary file
        expected_hash = hashlib.md5(b"Hello, world!").hexdigest()
        computed_hash = compute_md5(tmpfile_path)

        # Clean up the temporary file
        os.unlink(tmpfile_path)

        assert computed_hash == expected_hash, "MD5 hash does not match for the given file content."

    def test_compute_md5_non_existent_file(self):
        with pytest.raises(FileNotFoundError):
            compute_md5("non_existent_file.txt")

    def test_compute_md5_large_file(self):
        # Create a large temporary file
        with NamedTemporaryFile(delete=False) as tmpfile:
            # Writing 1GB of zeros to the file
            tmpfile.write(b"\0" * 1024 * 1024 * 1024)
            tmpfile_path = tmpfile.name

        # Attempt to compute MD5 hash of the large file
        try:
            compute_md5(tmpfile_path)
            assert True, "Successfully computed MD5 hash for a large file without running out of memory."
        except MemoryError:
            pytest.fail("Failed to compute MD5 hash for a large file due to memory error.")
        finally:
            # Clean up the temporary file
            os.unlink(tmpfile_path)

class TestCopyNewFiles:
    def setup_method(self):
        self.temp_dir = TemporaryDirectory()
        self.source_folder = Path(self.temp_dir.name, "source")
        self.destination_folder = Path(self.temp_dir.name, "destination")
        self.source_folder.mkdir()
        self.destination_folder.mkdir()

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_copy_new_files(self):
        # Create a new file in the source folder
        new_file_path = self.source_folder / "new_file.txt"
        new_file_path.write_text("This is a new file.")

        # Run the function
        create_count, modify_count = copy_new_files(str(self.source_folder), str(self.destination_folder))

        # Check if the file was copied
        assert (self.destination_folder / "new_file.txt").exists()
        assert create_count == 1
        assert modify_count == 0

    def test_copy_modified_files(self):
        # Create a file and copy it to the destination folder
        existing_file_path = self.source_folder / "existing_file.txt"
        existing_file_path.write_text("Original content.")
        shutil.copy2(existing_file_path, self.destination_folder)

        # Modify the file in the source folder
        existing_file_path.write_text("Modified content.")

        # Run the function
        create_count, modify_count = copy_new_files(str(self.source_folder), str(self.destination_folder))

        # Check if the file was modified
        with open(self.destination_folder / "existing_file.txt", "r") as f:
            content = f.read()
        assert content == "Modified content."
        assert create_count == 0
        assert modify_count == 1

    def test_handle_non_existent_source_files(self):
        # Point to a non-existent source folder
        non_existent_source = self.source_folder / "non_existent"

        # Run the function
        create_count, modify_count = copy_new_files(str(non_existent_source), str(self.destination_folder))

        # Since the source folder does not exist, no files should be copied or modified
        assert create_count == 0
        assert modify_count == 0
        
    def test_copy_new_directory(self):
        # Create a new directory in the source folder
        new_dir_path = self.source_folder / "new_dir"
        new_dir_path.mkdir()

        # Run the function
        create_count, modify_count = copy_new_files(str(self.source_folder), str(self.destination_folder))

        # Check if the directory was copied
        assert (self.destination_folder / "new_dir").exists()
        assert create_count == 1
        assert modify_count == 0

    def test_copy_new_directory_with_files(self):
        # Create a new directory with a file in the source folder
        new_dir_path = self.source_folder / "new_dir"
        new_dir_path.mkdir()
        new_file_path = new_dir_path / "new_file.txt"
        new_file_path.write_text("This is a new file.")

        # Run the function
        create_count, modify_count = copy_new_files(str(self.source_folder), str(self.destination_folder))

        # Check if the directory and file were copied
        assert (self.destination_folder / "new_dir").exists()
        assert (self.destination_folder / "new_dir" / "new_file.txt").exists()
        assert create_count == 2
        assert modify_count == 0

    def test_copy_nested_directories(self):
        # Create nested directories with a file in the source folder
        nested_dir_path = self.source_folder / "dir1" / "dir2"
        nested_dir_path.mkdir(parents=True)
        new_file_path = nested_dir_path / "new_file.txt"
        new_file_path.write_text("This is a new file.")

        # Run the function
        create_count, modify_count = copy_new_files(str(self.source_folder), str(self.destination_folder))

        # Check if the nested directories and file were copied
        assert (self.destination_folder / "dir1" / "dir2").exists()
        assert (self.destination_folder / "dir1" / "dir2" / "new_file.txt").exists()
        assert create_count == 3
        assert modify_count == 0

class TestDeleteRemovedFiles:
    def setup_method(self):
        self.temp_dir = TemporaryDirectory()
        self.source_folder = Path(self.temp_dir.name, "source")
        self.destination_folder = Path(self.temp_dir.name, "destination")
        self.source_folder.mkdir()
        self.destination_folder.mkdir()

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_delete_removed_files_happy_path(self):
        # Setup
        (self.source_folder / "keep_file.txt").touch()
        (self.destination_folder / "keep_file.txt").touch()
        (self.destination_folder / "delete_file.txt").touch()
        (self.destination_folder / "delete_folder").mkdir()
        assert len(list(self.destination_folder.iterdir())) == 3  # 2 files, 1 folder

        # Exercise
        delete_count = delete_removed_files(str(self.source_folder), str(self.destination_folder))

        # Verify
        assert delete_count == 2  # 1 file, 1 folder deleted
        assert len(list(self.destination_folder.iterdir())) == 1  # Only "keep_file.txt" should remain

    def test_delete_removed_files_no_deletion(self):
        # Setup
        (self.source_folder / "keep_file.txt").touch()
        (self.destination_folder / "keep_file.txt").touch()
        assert len(list(self.destination_folder.iterdir())) == 1

        # Exercise
        delete_count = delete_removed_files(str(self.source_folder), str(self.destination_folder))

        # Verify
        assert delete_count == 0  # No files should be deleted
        assert len(list(self.destination_folder.iterdir())) == 1  # "keep_file.txt" should remain

    def test_delete_removed_files_no_source_folder(self):
        # Setup
        (self.destination_folder / "delete_file.txt").touch()
        assert len(list(self.destination_folder.iterdir())) == 1

        # Exercise
        delete_count = delete_removed_files(str(Path(self.temp_dir.name, "non_existent_source")), str(self.destination_folder))

        # Verify
        assert delete_count == 0  # No files should be deleted as source folder does not exist
        assert len(list(self.destination_folder.iterdir())) == 1  # "delete_file.txt" should remain
    
    def test_delete_removed_files_with_directories(self):
        # Setup
        (self.source_folder / "keep_dir").mkdir()
        (self.destination_folder / "keep_dir").mkdir()
        (self.destination_folder / "delete_dir").mkdir()
        assert len(list(self.destination_folder.iterdir())) == 2  # 2 directories

        # Exercise
        delete_count = delete_removed_files(str(self.source_folder), str(self.destination_folder))

        # Verify
        assert delete_count == 1  # 1 directory deleted
        assert len(list(self.destination_folder.iterdir())) == 1  # Only "keep_dir" should remain

    def test_delete_removed_files_with_nested_directories(self):
        # Setup
        (self.source_folder / "keep_dir" / "nested_dir").mkdir(parents=True)
        (self.destination_folder / "keep_dir" / "nested_dir").mkdir(parents=True)
        (self.destination_folder / "delete_dir" / "nested_dir").mkdir(parents=True)
        assert len(list(self.destination_folder.iterdir())) == 2  # 2 directories at root level

        # Exercise
        delete_count = delete_removed_files(str(self.source_folder), str(self.destination_folder))

        # Verify
        assert delete_count == 2  # 2 directories deleted ("delete_dir" and "delete_dir/nested_dir")
        assert len(list(self.destination_folder.iterdir())) == 1  # Only "keep_dir" should remain
        assert len(list((self.destination_folder / "keep_dir").iterdir())) == 1  # "nested_dir" should remain in "keep_dir"

@pytest.fixture
def setup_folders(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    source_folder.mkdir()
    destination_folder.mkdir()
    return source_folder, destination_folder

@pytest.fixture
def create_test_files(setup_folders):
    source_folder, _ = setup_folders
    (source_folder / "test_file.txt").write_text("This is a test file.")
    (source_folder / "subfolder").mkdir()
    (source_folder / "subfolder/test_file_in_subfolder.txt").write_text("This is another test file in a subfolder.")

class TestSyncFolders:
    def test_sync_folders_happy_path(self, setup_folders, create_test_files, tmp_path):
        source_folder, destination_folder = setup_folders
        log_file = tmp_path / "sync.log"

        # Run sync_folders in a separate process
        p = multiprocessing.Process(target=sync_folders, args=(str(source_folder), str(destination_folder), 1, str(log_file)))
        p.start()

        # Allow sync_folders to run for a certain amount of time
        time.sleep(5)

        # Terminate the process
        p.terminate()

        assert (destination_folder / "test_file.txt").exists()
        assert (destination_folder / "subfolder/test_file_in_subfolder.txt").exists()

    def test_sync_folders_source_folder_not_exist(self, setup_folders, tmp_path):
        _, destination_folder = setup_folders
        non_existent_source_folder = "non_existent_folder"
        log_file = tmp_path / "sync.log"
        with pytest.raises(FileNotFoundError):
            sync_folders(non_existent_source_folder, str(destination_folder), 1, str(log_file))

    def test_sync_folders_destination_folder_not_exist(self, setup_folders, tmp_path):
        source_folder, _ = setup_folders
        non_existent_destination_folder = "non_existent_folder"
        log_file = tmp_path / "sync.log"
        with pytest.raises(FileNotFoundError):
            sync_folders(str(source_folder), non_existent_destination_folder, 1, str(log_file))