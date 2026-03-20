import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from app.services.refiner_tools import _make_json_safe, save_refinement_result


class _SampleModel(BaseModel):
    score: float
    label: str


@dataclass
class _SampleDataclass:
    key: str
    value: int


class _CustomObject:
    def __str__(self) -> str:
        return "custom-object"


class TestMakeJsonSafe:
    def test_primitives_passthrough(self):
        assert _make_json_safe("x") == "x"
        assert _make_json_safe(1) == 1
        assert _make_json_safe(1.25) == 1.25
        assert _make_json_safe(True) is True
        assert _make_json_safe(None) is None

    def test_nested_collections_and_key_stringification(self):
        value = {
            1: [1, 2, ("a", "b")],
            "nested": {"ok": True},
        }
        result = _make_json_safe(value)
        assert result == {
            "1": [1, 2, ["a", "b"]],
            "nested": {"ok": True},
        }

    def test_pydantic_model_conversion(self):
        model = _SampleModel(score=0.9, label="good")
        result = _make_json_safe(model)
        assert result == {"score": 0.9, "label": "good"}

    def test_dataclass_conversion(self):
        item = _SampleDataclass(key="k", value=3)
        result = _make_json_safe(item)
        assert result == {"key": "k", "value": 3}

    def test_unknown_object_falls_back_to_string(self):
        result = _make_json_safe(_CustomObject())
        assert result == "custom-object"


class TestSaveRefinementResult:
    def test_writes_log_file_and_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = save_refinement_result(
            agent_name="refiner_agent",
            refined_prompt="updated prompt",
            summary="improved clarity",
        )

        file_path = Path(path)
        assert file_path.exists()
        assert file_path.parent.name == "refinement_logs"

        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert data["agent_name"] == "refiner_agent"
        assert data["refined_prompt"] == "updated prompt"
        assert data["summary"] == "improved clarity"
        assert "timestamp_utc" in data

    def test_invalid_agent_name_uses_refiner_prefix(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = save_refinement_result(
            agent_name="!!!",
            refined_prompt="p",
            summary="s",
        )
        assert Path(path).name.startswith("refiner_")

    def test_optional_payload_fields_are_serialized(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        changes = [_SampleDataclass(key="tone", value=1)]
        full_result = _SampleModel(score=0.88, label="pass")

        path = save_refinement_result(
            agent_name="my refiner/v2!",
            refined_prompt="new",
            summary="ok",
            original_prompt="old",
            changes=changes,
            expected_impact="higher score",
            evaluation_score_ref={"overall_score": 0.88},
            full_result=full_result,
            extra={"owner": "ci"},
        )

        file_path = Path(path)
        assert "/" not in file_path.name
        assert "!" not in file_path.name

        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert data["original_prompt"] == "old"
        assert data["changes"] == [{"key": "tone", "value": 1}]
        assert data["expected_impact"] == "higher score"
        assert data["evaluation_score_ref"] == {"overall_score": 0.88}
        assert data["full_result"] == {"score": 0.88, "label": "pass"}
        assert data["extra"] == {"owner": "ci"}
