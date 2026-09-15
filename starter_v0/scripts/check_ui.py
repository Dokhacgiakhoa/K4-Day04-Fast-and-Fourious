"""UI smoke check for the version-compare workbench; no real API requests.

Chạy: .venv/Scripts/python.exe scripts/check_ui.py
Dùng AppTest với provider giả lập (clarify → awaiting_user) nên không gọi model
thật và không tạo ticket. Kiểm: app render 3 mode, default provider OpenRouter,
version discovery (current + v0 snapshot), chạy compare không exception, và
nút bị khoá khi thiếu key.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest
from providers.base import ModelResponse, ToolCall


class ScriptedProvider:
    """Luôn trả về một clarify call → run_model_tool_loop dừng ở waiting_for_user."""
    default_model = "ui-test"
    api_key_env = "OPENROUTER_API_KEY"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools, **kwargs):
        self.calls += 1
        return ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Asset ID là gì?"})])


def check() -> None:
    # --- 1. App render + cấu trúc cơ bản (có key) ---
    provider = ScriptedProvider()
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-local-test"}), \
         patch("providers.make_provider", return_value=provider):
        ui = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        assert not ui.exception, ui.exception

        # 3 chế độ
        assert len(ui.radio[0].options) == 3, ui.radio[0].options
        # provider mặc định OpenRouter
        assert ui.selectbox(key="provider").value == "openrouter", ui.selectbox(key="provider").value
        # version discovery: current + v0 snapshot đều có trong option của Version A/B
        version_opts = ui.selectbox(key="cmp_a").options
        assert any("current" in o for o in version_opts), version_opts
        assert any("v0" in o for o in version_opts), version_opts

        # --- 2. Chạy compare: nút không bị khoá, click chạy được, gọi provider cho cả 2 version ---
        run_btn = ui.button(key="run_compare")
        assert not run_btn.disabled
        before = provider.calls
        run_btn.click().run()
        assert not ui.exception, ui.exception
        assert provider.calls >= before + 2, f"compare phải chạy cả 2 version (calls={provider.calls})"

    # --- 3. Thiếu key → nút chạy bị khoá ---
    provider2 = ScriptedProvider()
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}), \
         patch("providers.make_provider", return_value=provider2):
        ui = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        assert not ui.exception, ui.exception
        assert ui.button(key="run_compare").disabled, "Thiếu key thì nút chạy phải bị khoá"
        assert provider2.calls == 0, "Không được gọi provider khi thiếu key"

    print("PASS: 3 modes render, OpenRouter default, version discovery (current+v0), "
          "compare chạy cả 2 version, nút khoá khi thiếu key")


if __name__ == "__main__":
    check()
