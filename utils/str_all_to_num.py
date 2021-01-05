from typing import Any


def str_all_to_num(data: Any, count: int, exceed: int) -> int:
    if type(data) == int:
        if data > exceed:
            print(f'[*] This is a big list. It might take some time'.title())
        return data
    elif data == 'all':
        data = count
        if data > exceed:
            print(f'[*] This is a big list. It might take some time'.title())
        return data
    else:
        raise ValueError(f'{data} is not a valid argument')

