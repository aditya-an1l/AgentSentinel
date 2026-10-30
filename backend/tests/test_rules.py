from app.screening.rules import inspect_call, mock_classification
from app.proxy.policy import execution_allowed


def test_blocks_destructive_command():
    blocked, reason = inspect_call("shell", {"command": "rm -rf /workspace"})
    assert blocked and "Destructive" in reason


def test_blocks_shell_operators():
    assert inspect_call("shell", {"command": "pwd; whoami"})[0]


def test_blocks_path_traversal():
    assert inspect_call("filesystem.read", {"path": "../../etc/passwd"})[0]


def test_blocks_env_file():
    assert inspect_call("filesystem.read", {"path": ".env"})[0]


def test_allows_workspace_listing():
    assert inspect_call("filesystem.list", {"path": "."}) == (False, None)


def test_mock_classifier_is_not_model():
    verdict, reason = mock_classification("filesystem.list", {"path": "."})
    assert verdict == "allow"
    assert "Mock" in reason


def test_only_allow_is_executable():
    assert execution_allowed("allow")
    assert not execution_allowed("deny")
    assert not execution_allowed("escalate")
    assert not execution_allowed("confirm")
