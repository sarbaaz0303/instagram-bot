import os
from typing import NewType
AnyPath = NewType('AnyPath', os.PathLike[str])


'''create folder'''
def create_folder(path: AnyPath) -> AnyPath:
    if not os.path.isdir(path):
        os.mkdir(path)