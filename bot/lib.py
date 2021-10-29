import os
from typing import Callable


def create_folders_in_path(path: str, fail_delegate: Callable[[], any] = None):
    index = path.find('/')
    if index != -1:
        folders = path[0: index]
        if not os.path.exists(folders):
            try:
                os.makedirs(folders)
            except FileExistsError:
                print("Unable to create " + folders + " dirs", flush = True)
                if fail_delegate is not None:
                    fail_delegate()
