# Task Context

This script implements a synch between two folders.

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

## Sync Folders

The sync_folders.py script is a utility for synchronizing the contents of two directories. It ensures that the destination directory is an exact copy of the source directory by copying any files from the source to the destination, and removing any files from the destination that are not present in the source.

### How to Run

To run sync_folders.py, you need to provide the source directory, destination directory, log file path and sync interval as command-line arguments:

```python
python sync_folders.py <source_directory> <destination_directory> <log_file> <sync_interval>
```

The sync_interval is the time in seconds between each synchronization operation.

### Testing

The test_veem.py script contains a suite of unit tests for sync_folders.py. These tests cover various scenarios, including file creation, modification, and deletion, as well as handling of errors.

To run the tests, you can use the following command:

```python
python -m unittest test_veem.py
```
