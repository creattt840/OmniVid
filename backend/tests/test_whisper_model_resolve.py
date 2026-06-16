"""Whisper 模型路径解析单元测试。"""
import pytest

from app.services.ai.transcriber import resolve_whisper_model_spec


def test_builtin_size():
    assert resolve_whisper_model_spec("small") == "small"


def test_hf_repo_id():
    assert resolve_whisper_model_spec("Systran/faster-whisper-small") == "Systran/faster-whisper-small"


def test_missing_local_dir_raises(tmp_path):
    missing = tmp_path / "no-such-model"
    with pytest.raises(ValueError, match="目录不存在"):
        resolve_whisper_model_spec(str(missing))


def test_incomplete_local_dir_raises(tmp_path):
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    with pytest.raises(ValueError, match="model.bin"):
        resolve_whisper_model_spec(str(incomplete))


def test_valid_local_dir(tmp_path):
    model_dir = tmp_path / "faster-whisper-small"
    model_dir.mkdir()
    (model_dir / "model.bin").write_bytes(b"x")
    assert resolve_whisper_model_spec(str(model_dir)) == str(model_dir.resolve())
