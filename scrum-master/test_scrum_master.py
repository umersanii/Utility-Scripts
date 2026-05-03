import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from scrum_master import ask_yes_no, get_scrum_display_date, parse_args, post_to_slack, since_timestamp


def test_post_to_slack_success():
    summary = "1. Quick Updates\n* Did stuff"
    config = {
        "slack_token": "xoxb-10826896409590-10822583948547-0witZpGCMoTkYtai1HKqcP3X",
        "slack_channel": "#your-channel-name",
        "schedule": "3:00 pm - 8:00 pm",
        "cc": "@test",
    }

    response_mock = Mock()
    response_mock.json.return_value = {"ok": True, "ts": "12345"}

    with patch("scrum_master.requests.post", return_value=response_mock) as post_mock:
        data = post_to_slack(summary, config)

    post_mock.assert_called_once()
    assert data["ok"] is True


def test_post_to_slack_prefers_user_token_over_bot_token():
    summary = "1. Quick Updates\n* Did stuff"
    config = {
        "slack_token": "xoxb-bot-token",
        "slack_user_token": "xoxp-user-token",
        "slack_channel": "#your-channel-name",
        "schedule": "3:00 pm - 8:00 pm",
        "cc": "@test",
    }

    response_mock = Mock()
    response_mock.json.return_value = {"ok": True, "ts": "12345"}

    with patch("scrum_master.requests.post", return_value=response_mock) as post_mock:
        post_to_slack(summary, config)

    headers = post_mock.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer xoxp-user-token"


def test_post_to_slack_failure_raises():
    summary = "1. Quick Updates\n* Did stuff"
    config = {
        "slack_token": "xoxb-invalid-token",
        "slack_channel": "#your-channel-name",
        "schedule": "3:00 pm - 8:00 pm",
        "cc": "@test",
    }

    response_mock = Mock()
    response_mock.json.return_value = {"ok": False, "error": "invalid_auth"}

    with patch("scrum_master.requests.post", return_value=response_mock):
        with pytest.raises(RuntimeError, match="Slack API error"):
            post_to_slack(summary, config)


def test_post_to_slack_missing_token_raises():
    summary = "1. Quick Updates\n* Did stuff"
    config = {}

    with pytest.raises(ValueError, match="SLACK_USER_TOKEN or SLACK_BOT_TOKEN"):
        post_to_slack(summary, config)


def test_post_to_slack_uses_friday_date_on_monday():
    summary = "1. Quick Updates\n* Did stuff"
    config = {
        "slack_token": "xoxb-bot-token",
        "slack_channel": "#your-channel-name",
        "schedule": "3:00 pm - 8:00 pm",
        "cc": "@test",
    }

    response_mock = Mock()
    response_mock.json.return_value = {"ok": True, "ts": "12345"}

    class MondayDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 6, 10, 0, 0)

    with patch("scrum_master.datetime", MondayDateTime):
        with patch("scrum_master.requests.post", return_value=response_mock) as post_mock:
            post_to_slack(summary, config)

    payload = post_mock.call_args.kwargs["json"]
    assert payload["text"].startswith("[Friday, 03 Apr 2026]\n")


def test_since_timestamp_uses_friday_window_on_monday():
    class MondayDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 6, 12, 0, 0, tzinfo=tz)

    with patch("scrum_master.datetime", MondayDateTime):
        since = since_timestamp()

    assert since == "2026-04-03T12:00:00+00:00"


def test_since_timestamp_uses_24h_window_non_monday():
    class TuesdayDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 7, 12, 0, 0, tzinfo=tz)

    with patch("scrum_master.datetime", TuesdayDateTime):
        since = since_timestamp()

    assert since == "2026-04-06T12:00:00+00:00"


def test_ask_yes_no_accepts_yes_short():
    with patch("builtins.input", side_effect=["y"]):
        assert ask_yes_no("Post? ") is True


def test_ask_yes_no_reprompts_until_valid():
    with patch("builtins.input", side_effect=["maybe", "n"]):
        assert ask_yes_no("Post? ") is False


def test_parse_args_accepts_specific_date_flag():
    with patch("sys.argv", ["scrum_master.py", "--date", "2026-04-15"]):
        args = parse_args()

    assert args.date.isoformat() == "2026-04-15"


def test_get_scrum_display_date_uses_specific_date_when_provided():
    assert get_scrum_display_date(target_date=datetime(2026, 4, 15).date()) == "Wednesday, 15 Apr 2026"
