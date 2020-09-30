import pytest

from nearuplib.exceptions import NetworkError, capture_as


def test_capture_as():
    @capture_as(NetworkError)
    def raises_exception():
        raise Exception("oops")

    @capture_as(NetworkError)
    def raises_no_exception():
        return "some result"

    # should raise as new exception
    with pytest.raises(NetworkError):
        raises_exception()

    # should NOT raise as new exception
    try:
        assert raises_no_exception() == "some result"
    except NetworkError:
        print("should not have raised exception!")
        assert False
