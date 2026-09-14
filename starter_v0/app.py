"""Lab UI. Run: python -m streamlit run app.py"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
from uuid import uuid4

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


MODEL_OPTIONS = {
    "gemini": ["gemini-3.5-flash-lite", "gemini-2.5-flash"],
    "openrouter": ["openai/gpt-4o-mini"],
    "openai": ["gpt-4o-mini"],
    "anthropic": ["claude-haiku-4-5-20251001"],
}


def new_session(config: dict, prompt: str, tools: list[dict]) -> dict:
    session_id = f"ui_{uuid4().hex}"
    return {
        "config": config,
        "prompt": prompt,
        "tools": tools,
        "history": [],
        "path": ROOT / "transcripts" / f"{session_id}.transcript.json",
        "transcript": {
            "transcript_id": session_id,
            **config,
            "source": "streamlit_ui",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        },
    }


def provider_error_summary(exc: Exception, api_key: str) -> str:
    """Keep a useful provider failure reason without recording credentials."""
    if type(exc).__name__ not in {"ClientError", "ServerError", "APIStatusError", "AuthenticationError", "RateLimitError"}:
        return "Provider runtime error. Check the selected provider, model, and installed SDK."
    message = " ".join(str(exc).split())
    if api_key:
        message = message.replace(api_key, "[redacted]")
    message = re.sub(r"AIza[\w-]{20,}", "[redacted]", message)
    message = re.sub(r"(key|api[_-]?key)=([^\s&]+)", r"\1=[redacted]", message, flags=re.I)
    if not message:
        message = "Provider did not return an error message."
    return message[:500]


def run_turn(session: dict, user_text: str, api_key: str = "") -> None:
    config = session["config"]
    turn = {
        "turn_index": len(session["transcript"]["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": "",
        "rounds": [],
        "tool_events": [],
    }
    try:
        result = run_model_tool_loop(
            provider=make_provider(config["provider"], api_key=api_key or None),
            messages=[
                {"role": "system", "content": session["prompt"]},
                *trim_history(session["history"], config["history_window"]),
                {"role": "user", "content": user_text},
            ],
            tools=session["tools"],
            model=config["model"],
            max_tool_rounds=config["max_tool_rounds"],
        )
        turn.update(result)
        session["history"].extend([
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": result["assistant_text"]},
        ])
    except Exception as exc:
        # Avoid leaking provider request bodies / credentials into UI transcripts.
        turn.update(
            status="provider_error",
            error=type(exc).__name__,
            error_detail=provider_error_summary(exc, api_key),
        )
    turn["ended_at"] = now_iso()
    session["transcript"]["turns"].append(turn)
    try:
        write_transcript(session["path"], session["transcript"])
        session.pop("save_error", None)
    except OSError:
        session["save_error"] = True


def render_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn["status"] == "provider_error":
            st.error(f"Không hoàn tất lượt chat ({turn['error']}). Kiểm tra API key, model và kết nối.")
            st.caption(turn.get("error_detail", "Không có chi tiết từ provider."))
            st.caption("Runtime có thể đã chạy tool trước khi gặp lỗi; trace một phần không được trả về. Kiểm tra trạng thái trước khi gửi lại action.")
        elif turn["status"] == "waiting_for_user":
            st.info("Đang chờ bạn bổ sung thông tin hoặc xác nhận.")
        elif turn["status"] == "max_tool_rounds":
            st.warning("Đã đạt giới hạn vòng gọi tool. Xem trace trước khi tiếp tục.")
        if turn.get("assistant_text"):
            st.markdown(turn["assistant_text"])
        count = len(turn.get("tool_events", []))
        st.caption(f"Lượt {turn['turn_index']} · {turn['status']} · {count} tool calls")
        if turn.get("rounds"):
            with st.expander(f"Xem quá trình xử lý · {count} tool calls"):
                for record in turn["rounds"]:
                    st.markdown(f"**Vòng {record['round']}**")
                    if record.get("assistant_text"):
                        st.markdown(record["assistant_text"])
                    if not record.get("tool_calls"):
                        st.caption("Trả lời trực tiếp, không gọi tool.")
                    for call in record.get("tool_calls", []):
                        st.code(call["name"], language=None)
                        st.caption("Arguments")
                        st.json(call.get("args", {}))
                    for event in record.get("tool_results", []):
                        result = event.get("result", {})
                        if event.get("error") or (isinstance(result, dict) and result.get("error")):
                            st.error(f"{event['tool']}: tool trả về lỗi")
                        st.caption(f"Kết quả · {event['tool']}")
                        st.json(event)


def prefill_question(question: str) -> None:
    st.session_state["desk_chat_input"] = question


def main() -> None:
    st.set_page_config(page_title="DeskMate | IT Helpdesk", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
    st.markdown(f"<style>{Path(__file__).with_name('ui.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.markdown('''<div class="desk-overline">WORKSPACE &nbsp; / &nbsp; IT HELPDESK</div>
        <div class="desk-hero"><div class="desk-eyebrow">LESS FRICTION. MORE FOCUS.</div>
        <h1>Một nơi cho mọi<br>vấn đề IT của bạn.</h1>
        <p>Từ kết nối đến thiết bị. Đặt câu hỏi, theo dõi cách xử lý và tiếp tục công việc.</p>
        <div class="desk-hero-symbol" aria-hidden="true">✳</div></div>''', unsafe_allow_html=True)
    with st.container(border=True, key="connection_panel"):
        st.markdown('<div class="desk-section"><strong>Kết nối AI</strong><span>CẤU HÌNH CHO PHIÊN CỦA BẠN</span></div>', unsafe_allow_html=True)
        provider_col, model_col, key_col = st.columns([1, 1.4, 1.6])
        with provider_col:
            provider_name = st.selectbox("Provider", ["openrouter", "gemini", "openai", "anthropic"],
                                         format_func=lambda name: {
                                             "gemini": "Gemini · Google AI Studio",
                                             "openrouter": "OpenRouter",
                                             "openai": "OpenAI",
                                             "anthropic": "Anthropic",
                                         }[name])
        provider = make_provider(provider_name)
        with model_col:
            model = st.selectbox(
                "Model",
                MODEL_OPTIONS[provider_name],
                key=f"model_{provider_name}",
                help="Gemini 3.5 Flash-Lite là model mặc định Google yêu cầu cho user mới; có function calling.",
            )
        with key_col:
            api_key = st.text_input("API key", type="password", key=f"api_key_{provider_name}",
                               placeholder=f"Nhập {provider.api_key_env}",
                               help="Chỉ giữ trong phiên UI; không ghi vào .env, transcript hoặc Git.").strip()
        key_ready = bool(api_key or os.getenv(provider.api_key_env))
        if key_ready:
            st.markdown('<div class="desk-ready">● &nbsp; Đã có API key · Gửi câu hỏi để kiểm tra kết nối.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="desk-setup">○ &nbsp; Nhập API key để bắt đầu · Key chỉ được giữ trong phiên của bạn.</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('''<div class="desk-brand"><div class="desk-logo">✦</div>
            <div><strong>DeskMate</strong><small>YOUR IT COMPANION</small></div></div>
            <div class="desk-overline">FAST AND FOURIOUS · DAY 04</div>
            <div class="desk-nav">◉ &nbsp; Không gian hội thoại</div>''', unsafe_allow_html=True)
        st.divider()
        st.markdown("**Cấu hình phiên chat**")
        version = st.text_input("Artifact version", value="v0", key="artifact_label").strip()
        with st.expander("Tùy chọn hội thoại"):
            history_window = st.number_input("Số lượt giữ trong context", min_value=1, max_value=30, value=5)
            max_rounds = st.number_input("Giới hạn vòng tool mỗi lượt", min_value=1, max_value=12, value=4)
        reset = st.button("＋ Cuộc trò chuyện mới", key="new_conversation", use_container_width=True)

    try:
        prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        prompt = prompt_path.read_text(encoding="utf-8")
        declarations = load_tool_declarations(tools_path)
        tools = to_openai_tools(declarations)
        artifact = artifact_version_dict(build_artifact_version(version, prompt_path, tools_path))
    except Exception as exc:
        st.error(f"Không đọc được prompt hoặc tool declarations ({type(exc).__name__}). Kiểm tra artifacts/.")
        st.stop()

    config = {
        **artifact, "provider": provider_name, "model": model,
        "system_prompt": str(prompt_path), "tools": str(tools_path),
        "history_window": int(history_window), "max_tool_rounds": int(max_rounds),
    }
    if reset or "desk_session" not in st.session_state:
        st.session_state.desk_session = new_session(config, prompt, tools)
        if reset:
            st.session_state["desk_chat_input"] = ""
            st.success("Đã tạo cuộc trò chuyện mới với cấu hình hiện tại.")
    session = st.session_state.desk_session
    if not session["transcript"]["turns"]:
        session = new_session(config, prompt, tools)
        st.session_state.desk_session = session
    changed = config != session["config"]
    if changed:
        st.warning("Cấu hình hoặc artifacts đã thay đổi. Tải transcript hiện tại nếu cần, rồi chọn ‘Cuộc trò chuyện mới’ để dùng bản mới.")

    with st.sidebar:
        st.divider()
        st.markdown("**Artifacts của phiên hiện tại**")
        st.code(session["config"]["artifact_version"], language=None, wrap_lines=True)
        with st.expander("Hashes & tools"):
            st.text(f"Prompt: {session['config']['prompt_hash']}")
            st.text(f"Tools: {session['config']['tools_hash']}")
            for tool in session["tools"]:
                st.caption(tool["function"]["name"])

    turns = session["transcript"]["turns"]
    metrics = [
        ("Phiên bản", session["config"]["version"] or "—", "Artifacts của phiên hiện tại"),
        ("Tools khả dụng", str(len(session["tools"])), "Theo declarations của phiên"),
        ("Lượt hội thoại", str(len(turns)), "Trong cuộc trò chuyện này"),
        ("Tool calls", str(sum(len(t.get("tool_events", [])) for t in turns)), "Các lời gọi đã có trace"),
    ]
    for column, metric in zip(st.columns(4), metrics):
        with column:
            st.markdown(
                f'<div class="desk-metric"><div class="desk-metric-label">{metric[0]}</div>'
                f'<div class="desk-metric-value">{metric[1]}</div>'
                f'<div class="desk-metric-note">{metric[2]}</div></div>',
                unsafe_allow_html=True,
            )
    st.divider()
    st.markdown('<div class="desk-section"><strong>Hội thoại</strong><span>HỖ TRỢ RÕ RÀNG, TỪNG BƯỚC MỘT</span></div>', unsafe_allow_html=True)

    if not turns:
        st.markdown('<div class="desk-empty-title">Hôm nay, bạn cần hỗ trợ gì?</div><div class="desk-empty-subtitle">Bắt đầu với một gợi ý, hoặc kể cho mình vấn đề của bạn.</div>', unsafe_allow_html=True)
        for column, title, example, symbol in zip(st.columns(3),
            ["🌐 Kết nối", "💻 Thiết bị", "📚 Hướng dẫn"],
            ["Kiểm tra trạng thái dịch vụ VPN.", "Máy tính của tôi đang rất chậm, bạn kiểm tra giúp được không?", "Tìm hướng dẫn xử lý Wi-Fi trên Windows."], ["◎", "▣", "≡"]):
            with column:
                with st.container(border=True):
                    st.markdown(f'<div class="desk-prompt-icon" aria-hidden="true">{symbol}</div><div class="desk-prompt-title">{title[2:]}</div><div class="desk-prompt-text">{example}</div>', unsafe_allow_html=True)
                    st.button("Dùng câu hỏi này  ↗", key=f"sample_{title}",
                              on_click=prefill_question, args=(example,), use_container_width=True)
    for turn in turns:
        render_turn(turn)

    if not key_ready:
        st.info("Bạn có thể nhập câu hỏi; cần điền API key trong phần Kết nối AI trước khi gửi.")
    elif not model or not version:
        st.info("Chọn Model trong Kết nối AI và điền Artifact version ở thanh bên để gửi tin nhắn.")
    if "unsent_draft" in st.session_state:
        st.session_state["desk_chat_input"] = st.session_state.pop("unsent_draft")
        st.warning("Chưa gửi câu hỏi: hoàn tất API key, Model ID và Artifact version trước khi gửi.")
    text = st.chat_input("Nhập vấn đề IT của bạn…", key="desk_chat_input",
                         disabled=changed)
    if text and text.strip():
        if not key_ready or not model or not version:
            st.session_state["unsent_draft"] = text.strip()
            st.rerun()
        with st.chat_message("user"):
            st.markdown(text.strip())
        with st.spinner("Agent đang kiểm tra và xử lý yêu cầu…"):
            run_turn(session, text.strip(), api_key)
        st.rerun()

    if turns:
        with st.sidebar:
            st.divider()
            st.download_button("↓ Tải transcript JSON", data=json.dumps(session["transcript"], ensure_ascii=False, indent=2),
                               file_name=session["path"].name, mime="application/json", use_container_width=True)
            st.caption(f"Transcript: {session['path']}")
            if session.get("save_error"):
                st.warning("Không lưu được file trên máy. Dùng nút tải transcript để giữ evidence.")
    st.markdown('<div class="desk-footer">DESKMATE &nbsp; · &nbsp; Dữ liệu mô phỏng &nbsp; · &nbsp; Trace hiển thị sau mỗi lượt xử lý.</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
