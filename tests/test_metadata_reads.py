from nearuplib.util import (
    latest_deployed_release_branch,
    latest_deployed_release_commit,
    latest_deployed_release_commit_has_changed,
    latest_deployed_release_time,
    latest_genesis_md5sum,
)


def test_latest_deployed_release_commit():
    assert latest_deployed_release_commit('betanet')


def test_latest_deployed_release_commit_has_changed():
    commit = ""
    assert not latest_deployed_release_commit_has_changed('betanet', commit)

    commit = None
    assert not latest_deployed_release_commit_has_changed('betanet', commit)

    commit = latest_deployed_release_commit('betanet')
    assert not latest_deployed_release_commit_has_changed('betanet', commit)

    commit = 'aaaaaaaaaaaaaaaaaaaaaaaaaaa'
    assert latest_deployed_release_commit_has_changed('betanet', commit)


def test_latest_deployed_release_branch():
    assert latest_deployed_release_branch('betanet')


def test_latest_deployed_release_time():
    assert latest_deployed_release_time('betanet')


def test_latest_genesis_md5sum():
    assert latest_genesis_md5sum('betanet')
