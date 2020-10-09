from nearuplib.tailer import next_logname


def test_next_logname():
    assert next_logname(
        'test-data/incrementlog.log') == 'test-data/incrementlog.log.2'
    assert next_logname('test-data/justlog.log') == 'test-data/justlog.log.1'
    assert next_logname(
        'test-data/nonexistinglog.log') == 'test-data/nonexistinglog.log'
