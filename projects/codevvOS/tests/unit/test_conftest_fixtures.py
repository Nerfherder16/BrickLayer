from pathlib import Path


def test_jwt_token_is_nonempty_string(jwt_token):
    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0


def test_tmp_workspace_is_existing_directory(tmp_workspace):
    assert isinstance(tmp_workspace, Path)
    assert tmp_workspace.exists()
    assert tmp_workspace.is_dir()
