import json
from pathlib import Path

from app.services.judge_tools import save_evaluation_result


class TestSaveEvaluationResult:
    """Tests for the judge agent's evaluation log tool."""

    def test_returns_true_on_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert save_evaluation_result("judge_agent", 0.85, "Looks good") is True

    def test_creates_log_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_evaluation_result("judge_agent", 0.85, "Looks good")
        logs = list((tmp_path / "evaluation_logs").glob("*.json"))
        assert len(logs) == 1

    def test_log_file_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_evaluation_result("judge_agent", 0.85, "Looks good")
        log_file = next((tmp_path / "evaluation_logs").glob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert data["agent_name"] == "judge_agent"
        assert data["agent_score"] == 0.85
        assert data["summary"] == "Looks good"
        assert "timestamp_utc" in data

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert not (tmp_path / "evaluation_logs").exists()
        save_evaluation_result("judge_agent", 0.5, "Needs work")
        assert (tmp_path / "evaluation_logs").is_dir()

    def test_filename_has_no_illegal_characters(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_evaluation_result("judge_agent", 0.9, "Fine")
        log_file = next((tmp_path / "evaluation_logs").glob("*.json"))
        assert ":" not in log_file.name

    def test_agent_name_sanitised_in_filename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_evaluation_result("my agent/v2!", 0.5, "test")
        log_file = next((tmp_path / "evaluation_logs").glob("*.json"))
        assert "/" not in log_file.name
        assert "!" not in log_file.name

    def test_empty_agent_name_falls_back(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_evaluation_result("!!!", 0.5, "test")
        log_file = next((tmp_path / "evaluation_logs").glob("*.json"))
        assert log_file.name.startswith("judge_")

    def test_returns_false_on_write_failure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Make evaluation_logs a file rather than a directory so open() fails
        (tmp_path / "evaluation_logs").write_text("blocking file")
        result = save_evaluation_result("judge_agent", 0.5, "test")
        assert result is False
