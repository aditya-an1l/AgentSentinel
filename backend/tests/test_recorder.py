from app.recorder.flight_recorder import redact


def test_redacts_sensitive_keys():
    assert redact({"api_key": "abc", "nested": {"password": "secret"}}) == {
        "api_key": "[REDACTED]", "nested": {"password": "[REDACTED]"}
    }


def test_redacts_token_shaped_values():
    assert redact({"message": "sk-abcdefghijklmnopqrstuvwxyz"})["message"] == "[REDACTED]"
