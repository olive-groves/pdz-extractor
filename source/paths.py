import os
from pathlib import Path


class Folder:
    """Represent a folder as a directory and filenames associated with that folder."""
    def __init__(self, directory: str=None, filenames: list=[]):
        self.directory = directory
        self.filenames = filenames


def create_folders(paths: list=[]):
    """Create a list of Folder objects from a list of filepaths.

    Args:
        paths (list of str): Absolute paths of files.

    Returns:
        folders (list of Folder): Folders of files with Folder.directory and Folder.filenames.
    """
    paths = sorted(paths)  # Sort paths in alphabetical order to group paths by directory 
    folders = []

    i = 0
    its = 0
    while i < len(paths) and its < 10000:  # Loop over all paths and assign their directory and filenames
        starting_path = paths[i]
        filenames = []
        directory = starting_path if os.path.isdir(starting_path) else os.path.dirname(starting_path)
        ii = i
        while ii < len(paths):  # Loop over paths starting at current path and get all filenames with the current path's directory
            path = paths[ii]
            path_dir = path if os.path.isdir(path) else os.path.dirname(path)
            if directory.replace('\\', '').replace('/', '') != path_dir.replace('\\', '').replace('/', ''):
                if ii == i:  # If the directory is not found in the starting path itself, then something has gone wrong and we need to move to the next path
                    i += 1
                break

            if os.path.isfile(path): filenames.append(os.path.basename(path))
            ii += 1
        
        i = ii
        folders.append(Folder(directory, filenames))
        its += 1

    return folders


def get_filepaths_with_extension_in_directory(path: str=None,
                                              extension: str=None):
    """Find files of an extension in a directory.
    
    If given a file, the directory of that file is used.
    
    Args:
        path (str): Absolute path of directory or file.
        extension (str): Extension of the files to find.

    Returns:
        filepaths (list of str): Absolute paths of found files.
    """

    if os.path.isdir(path):
        directory = path
    else:
        directory = os.path.dirname(path)

    filepaths = []

    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(extension):
                filepaths.append(os.path.join(directory, file))

    return filepaths


def get_likenamed_filepaths_with_extension(path: str=None, extension: str=None):
    """Find like-named files of an extension in the directory of a file.

    Args:
        path (str): Absolute path of file.
        extension (str): Extension of like-named files to find.
        
    Returns:
        filepaths (list of str): Absolute paths of found files.
    """

    stem = Path(path).stem
    all_filepaths = get_filepaths_with_extension_in_directory(path=path, extension=extension)

    filepaths = []
    for filepath in all_filepaths:
        if stem in filepath:
            filepaths.append(filepath)

    return filepaths
