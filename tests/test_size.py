import pytest

from ws.utils.size import get_readable_size


@pytest.mark.parametrize(
    ('size', 'formatted_string'),
    [
        (100, '100.0 B'),
        (1048, '1.0 KB'),
        (2 * 1024 * 1024, '2.0 MB'),
        (3 * 1024 * 1024 * 1024, '3.0 GB'),
        (15 * 1024 * 1024 * 1024 * 1024, '15360.0 GB'),
    ],
)
def test_should_print_formatted_size_given_size_integer_as_input(size, formatted_string):
    assert get_readable_size(size) == formatted_string
