import pytest
from fastapi import HTTPException

from app.dependencies.path_security import verify_path_in_workspace


@pytest.mark.unit
class TestVerifyPathInWorkspace:
    def test_valid_path_within_workspace_returns_resolved_path(self, tmp_path):
        subdir = tmp_path / "project" / "file.txt"
        subdir.parent.mkdir(parents=True, exist_ok=True)
        subdir.touch()
        result = verify_path_in_workspace(str(subdir), str(tmp_path))
        assert result == str(subdir.resolve())

    def test_path_traversal_raises_400(self, tmp_path):
        malicious = str(tmp_path) + "/../../etc/passwd"
        with pytest.raises(HTTPException) as exc_info:
            verify_path_in_workspace(malicious, str(tmp_path))
        assert exc_info.value.status_code == 400

    def test_null_byte_in_path_raises_400(self, tmp_path):
        with pytest.raises(HTTPException) as exc_info:
            verify_path_in_workspace("/workspace/file\x00.txt", str(tmp_path))
        assert exc_info.value.status_code == 400

    def test_url_encoded_traversal_raises_400_or_resolves_safely(self, tmp_path):
        encoded = str(tmp_path) + "/%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        try:
            result = verify_path_in_workspace(encoded, str(tmp_path))
            # If it doesn't raise, the resolved path must still be inside workspace
            assert result.startswith(str(tmp_path.resolve()))
        except HTTPException as e:
            assert e.status_code == 400

    def test_workspace_root_itself_is_allowed(self, tmp_path):
        result = verify_path_in_workspace(str(tmp_path), str(tmp_path))
        assert result == str(tmp_path.resolve())
