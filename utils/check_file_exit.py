import os
from typing import NewType
AnyPath = NewType('AnyPath', os.PathLike[str])

'''check if file exits in a given path'''
def check_file_exit(path: AnyPath) -> bool:
    return os.path.isfile(path)