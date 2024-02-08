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
    # Computes the MD5 hash of an existing file and returns it as a string.
    def test_compute_md5_returns_string_with_existing_file(self):
        # Arrange
        file_path = "existing_file.txt"
        expected_md5 = "8f072930202d3c7211dff0688e9cddf5"

        # Create the existing file
        with open(file_path, 'w') as f:
            f.write("This is an existing file")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert isinstance(result, str)
        assert result == expected_md5
        
    # Handles valid file paths and returns the correct MD5 hash.
    def test_compute_md5_valid_file_path(self):
        # Arrange
        file_path = "test_file.txt"
        expected_md5 = "c785060c866796cc2a1708c997154c8e"

        # Create the test file
        with open(file_path, 'w') as f:
            f.write("test file content")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert result == expected_md5
    
    # Handles files with different sizes and returns the correct MD5 hash.
    def test_compute_md5_different_sizes(self):
        # Arrange
        file_path1 = "test_file1.txt"
        file_path2 = "test_file2.txt"
    
        # Create two files with different sizes
        with open(file_path1, 'w') as f1:
            f1.write("This is a test file.")
        with open(file_path2, 'w') as f2:
            f2.write("This is a test file. It has a longer content.")
    
        # Act
        result1 = compute_md5(file_path1)
        result2 = compute_md5(file_path2)
    
        # Assert
        assert result1 != result2

    # Raises FileNotFoundError if the file does not exist.
    def test_compute_md5_file_not_found(self):
        # Arrange
        file_path = "nonexistent_file.txt"
    
        # Act and Assert
        with pytest.raises(FileNotFoundError):
            compute_md5(file_path)
   
    # Handles files with short paths and returns the correct MD5 hash.
    def test_compute_md5_short_paths_with_file_creation(self):
        # Arrange
        file_path = "test_file.txt"
        expected_md5 = "a4d83b950999f569f7fee8d96fb31900"

        # Create the file at the specified path
        with open(file_path, 'w') as f:
            f.write("This is a test file\n")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert result == expected_md5
    
    # Handles files with binary content and returns the correct MD5 hash.
    def test_handles_files_with_binary_content(self):
        # Arrange
        file_path = "binary_file.bin"
        expected_md5 = "d15ae53931880fd7b724dd7888b4b4ed"

        # Create the binary file
        with open(file_path, 'wb') as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert isinstance(result, str)
        assert result == expected_md5
    
    # Handles files with different contents and returns the correct MD5 hash.
    def test_handles_files_with_different_contents(self):
        # Arrange
        file_path = "file1.txt"
        expected_md5 = "e1d1faab91eb551b9a566eead319a012"

        # Create the file with different contents
        with open(file_path, 'w') as f:
            f.write("This is file 1")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert isinstance(result, str)
        assert result == expected_md5
    
    # Handles files with special characters in the name and returns the correct MD5 hash.
    def test_handles_files_with_special_characters(self):
        # Arrange
        file_path = "file@#$%.txt"
        expected_md5 = "44c53aafa5da17311de19d6fd76717a1"

        # Create the file with special characters in the name
        with open(file_path, 'w') as f:
            f.write("This is a file with special characters")

        # Act
        result = compute_md5(file_path)

        # Assert
        assert isinstance(result, str)
        assert result == expected_md5
    
    # Handles files with no content and returns the correct MD5 hash.
    def test_handles_files_with_no_content(self):
        # Arrange
        file_path = "empty_file.txt"
        expected_md5 = "d41d8cd98f00b204e9800998ecf8427e"

        # Create an empty file
        Path(file_path).touch()

        # Act
        result = compute_md5(file_path)

        # Assert
        assert isinstance(result, str)
        assert result == expected_md5

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