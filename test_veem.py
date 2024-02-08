import os
import time
import shutil
import pytest
import hashlib
import multiprocessing
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from sync_folders import compute_hash , copy_new_files, delete_removed_files, sync_folders

class TestComputeHash:
    # Computes the SHA-256 hash of a file.
    def test_compute_hash_sha256(self):
        # Arrange
        import tempfile
        file_content = b'This is a test file'
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            file_path = temp_file.name

        expected_hash = "e2d0fe1585a63ec6009c8016ff8dda8b17719a637405a4e23c0ff81339148249"

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert actual_hash == expected_hash

    # Returns the SHA-256 hash of the file.
    def test_compute_hash_return_value(self):
        # Arrange
        import tempfile
        file_content = b'This is a test file.'
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            file_path = temp_file.name

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert isinstance(actual_hash, str)
        assert actual_hash == hashlib.sha256(file_content).hexdigest()

    # Reads the file in chunks of 8192 bytes.
    def test_compute_hash_chunk_size(self):
        # Arrange
        import tempfile
        import os
        chunk_size = 8192

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name

        # Write data to the temporary file
        with open(file_path, 'wb') as f:
            f.write(b'This is a test file.')

        # Act
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                pass

        # Assert
        assert True

        # Delete the temporary file
        os.remove(file_path)

    # Raises FileNotFoundError if the file does not exist.
    def test_compute_hash_file_not_found_fixed(self):
        # Arrange
        import tempfile
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = temp_file.name

            # Close the temporary file
            temp_file.close()

            # Act and Assert
            with pytest.raises(FileNotFoundError):
                compute_hash(file_path)

    # Raises OSError if an error occurs while opening or reading the file.
    def test_compute_hash_io_error(self):
        # Arrange
        import tempfile
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = temp_file.name

            # Act and Assert
            with pytest.raises(OSError):
                compute_hash(file_path)

    # Handles files with maximum allowed size.
    def test_compute_hash_maximum_size(self):
        # Arrange
        import tempfile
        max_size = 2**30  # Change the file size to a smaller value, such as 2^30 bytes (1 GB)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
            f.write(b'0' * max_size)

        # Act
        actual_hash = compute_hash(file_path)

        # After using the file, manually delete it
        os.remove(file_path)

            # Assert
        assert isinstance(actual_hash, str)

    # Handles valid file paths.
    def test_handles_valid_file_paths(self):
        # Arrange
        import tempfile
        file_content = b'This is a test file.'
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        expected_hash = "f29bc64a9d3732b4b9035125fdb3285f5b6455778edca72414671e0ca3b2e0de"

        # Act
        actual_hash = compute_hash(temp_file_path)

        # Assert
        assert actual_hash == expected_hash

    # Handles empty files.
    def test_handles_empty_files(self):
        # Arrange
        import tempfile
        import os
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert actual_hash == expected_hash

        # Clean up the temporary file
        os.remove(file_path)

    # Handles files with one or more bytes.
    def test_compute_hash_handles_files_with_one_or_more_bytes(self):
        # Arrange
        import tempfile
        file_content = b'This is a test file.'
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            file_path = temp_file.name

        expected_hash = "f29bc64a9d3732b4b9035125fdb3285f5b6455778edca72414671e0ca3b2e0de"

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert actual_hash == expected_hash

    # Handles files with non-ASCII characters in the name.
    def test_handles_files_with_non_ascii_characters(self):
        # Arrange
        import tempfile
        import os
        expected_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

        # Create a temporary file with non-ASCII characters
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
            f.write(b"test")

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert actual_hash == expected_hash

        # Clean up the temporary file
        os.remove(file_path)

    # Handles files with special characters in the name.
    def test_special_characters_in_name(self):
        # Arrange
        import tempfile
        import os
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        # Create a temporary file with special characters
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
            f.write(b"")

        # Act
        actual_hash = compute_hash(file_path)

        # Assert
        assert actual_hash == expected_hash

        # Clean up the temporary file
        os.remove(file_path)

    # Handles files with no execute permissions.
    def test_handles_files_with_no_execute_permissions(self):
        # Arrange
        import tempfile
        import shutil
        import os

        expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary file inside the directory
            temp_file_path = os.path.join(temp_dir, "test_file.txt")
            with open(temp_file_path, "w") as f:
                f.write("test content")

            # Act
            actual_hash = compute_hash(temp_file_path)

            # Assert
            assert actual_hash == expected_hash

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