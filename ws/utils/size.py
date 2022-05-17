# this code is inspired by pydantic type ByteSize
def get_readable_size(size: int) -> str:
    divisor = 1024
    units = ['B', 'KB', 'MB']
    final_unit = 'GB'

    for unit in units:
        if size < divisor:
            return f'{size:.1f} {unit}'
        size /= divisor

    return f'{size:.1f} {final_unit}'
