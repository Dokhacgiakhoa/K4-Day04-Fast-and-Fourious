"""UI integration smoke checks; no API requests or action tools."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest
import chat
from providers.base import ModelResponse, ToolCall
from versioning import build_artifact_version


class ScriptedProvider:
    default_model = "ui-test"
    api_key_env = "UI_TEST_API_KEY"

    def __init__(self):
        self.messages = []
        self.responses = [
            ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Asset ID là gì?"})]),
            ModelResponse(text="Đã nhận mã thiết bị."),
            ModelResponse(tool_calls=[ToolCall("inspect_device", {"asset_id": "UNKNOWN-TEST"})]),
            ModelResponse(text="Không tìm thấy thiết bị."),
            RuntimeError("private provider detail"),
        ]

    def complete(self, messages, tools, **kwargs):
        self.messages.append(messages)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def check():
    provider = ScriptedProvider()
    with TemporaryDirectory(prefix="day04-ui-check-") as temp, \
         patch.dict(os.environ, {"UI_TEST_API_KEY": "fake-local-test"}), \
         patch("providers.make_provider", return_value=provider), \
         patch.object(chat, "ROOT", Path(temp)):
        ui = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
        assert not ui.exception, ui.exception
        assert not ui.chat_input[0].disabled
        ui.chat_input[0].set_value("Máy tôi bị chậm.").run()
        session = ui.session_state["desk_session"]
        assert session["transcript"]["turns"][0]["status"] == "waiting_for_user"
        assert len(ui.chat_message) == 2
        assert session["path"].exists()
        assert session["transcript"]["turns"][0]["tool_events"][0]["tool"] == "clarify"
        ui.chat_input[0].set_value("ASSET-001").run()
        assert len(ui.chat_message) == 4
        assert provider.messages[1][-2]["content"] == "Asset ID là gì?"
        before_rerun = len(provider.messages)
        ui.run()
        assert len(provider.messages) == before_rerun, "UI rerun must not repeat tool execution"
        ui.chat_input[0].set_value("Kiểm tra UNKNOWN-TEST").run()
        assert any("tool trả về lỗi" in item.value for item in ui.error)
        ui.chat_input[0].set_value("Lỗi kết nối").run()
        assert not ui.exception, ui.exception
        assert session["transcript"]["turns"][-1]["status"] == "provider_error"
        assert "private provider detail" not in session["path"].read_text(encoding="utf-8")
        old_path = session["path"]
        ui.text_input[1].set_value("v1").run()
        assert ui.chat_input[0].disabled
        ui.button[0].click().run()
        assert not ui.chat_message
        assert old_path.exists()
        assert not ui.chat_input[0].disabled
        assert ui.session_state["desk_session"]["config"]["version"] == "v1"

        # A changed artifact hash requires a new session even with the same label.
        provider.responses.append(ModelResponse(text="OK"))
        ui.chat_input[0].set_value("Xin chào").run()
        original = build_artifact_version("v1", ROOT / "artifacts/system_prompt.md", ROOT / "artifacts/tools.yaml")
        from dataclasses import replace
        with patch("versioning.build_artifact_version", return_value=replace(original, prompt_hash="changed")):
            ui.run()
            assert ui.chat_input[0].disabled
        assert not ui.exception, ui.exception

    with patch("providers.make_provider", return_value=provider), patch.dict(os.environ, {"UI_TEST_API_KEY": ""}):
        ui = AppTest.from_file(str(ROOT / "app.py")).run()
        assert ui.chat_input[0].disabled
        assert not ui.exception, ui.exception
    print("PASS: chat, clarification/context, trace/tool error, provider error, transcript, reset, artifact change, missing key")


if __name__ == "__main__":
    check()
