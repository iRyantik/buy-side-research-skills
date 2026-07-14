from pathlib import Path

from coverage_monitor.delivery import workspace_env


def test_workspace_env_loads_dotenv_without_overriding_existing_env(tmp_path: Path):
    (tmp_path / ".env").write_text(
        "SMTP_HOST=smtp.qq.com\nSMTP_USER=user@example.com\nSMTP_PASSWORD=secret\nCOVERAGE_EMAIL_TO=to@example.com\n",
        encoding="utf-8",
    )
    env = workspace_env(tmp_path, env={"SMTP_USER": "existing@example.com"})
    assert env["SMTP_HOST"] == "smtp.qq.com"
    assert env["SMTP_USER"] == "existing@example.com"
    assert env["SMTP_PASSWORD"] == "secret"
    assert env["COVERAGE_EMAIL_TO"] == "to@example.com"

