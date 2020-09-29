import pytest

from nearuplib.util import NetworkError, capture_and_raise


def test_capture_and_raise():
    @capture_and_raise(NetworkError)
    def raises_exception():
        raise Exception("oops")

    @capture_and_raise(NetworkError)
    def raises_no_exception():
        pass

    # should raise as new exception
    with pytest.raises(NetworkError):
        raises_exception()

    # should NOT raise as new exception
    try:
        raises_no_exception()
    except NetworkError:
        print("should not have raised exception!")
        assert False
