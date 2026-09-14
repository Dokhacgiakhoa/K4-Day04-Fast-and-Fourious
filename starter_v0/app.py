"""Lab UI. Run: python -m streamlit run app.py"""
from __future__ import annotations

import json
import os
from uuid import uuid4

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


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


def run_turn(session: dict, user_text: str) -> None:
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
            provider=make_provider(config["provider"]),
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
        turn.update(status="provider_error", error=type(exc).__name__)
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


def main() -> None:
    st.set_page_config(page_title="DeskMate | IT Helpdesk", page_icon="💬", layout="wide")
    st.markdown("""<style>
        .stApp { background: #f7f9fc; }
        .block-container { max-width: 1120px; padding-top: 2.5rem; }
        [data-testid="stSidebar"] { background: #edf2f7; }
        [data-testid="stChatMessage"] { border: 1px solid #e2e8f0;
            border-radius: 16px; background: white; padding: 1.1rem; }
        h1 { letter-spacing: -0.045em; }
        .desk-eyebrow { color: #2563eb; font-size: .78rem; font-weight: 700;
            letter-spacing: .14em; margin-bottom: .5rem; }
        </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 💬 DeskMate")
        st.caption("DAY 04 · IT HELPDESK LAB")
        st.divider()
        st.markdown("**Cấu hình phiên chat**")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])
        provider = make_provider(provider_name)
        model = st.text_input("Model", value=provider.default_model, key=f"model_{provider_name}").strip()
        version = st.text_input("Artifact version", value="v0").strip()
        with st.expander("Tùy chọn hội thoại"):
            history_window = st.number_input("Số lượt giữ trong context", min_value=1, max_value=30, value=5)
            max_rounds = st.number_input("Giới hạn vòng tool mỗi lượt", min_value=1, max_value=12, value=4)
        key_ready = bool(os.getenv(provider.api_key_env))
        if key_ready:
            st.success("Đã cấu hình API key")
        else:
            st.warning(f"Chưa có {provider.api_key_env}")
            st.caption("Cấu hình trong starter_v0/.env hoặc DAY04_ENV_FILE rồi khởi động lại app.")
        reset = st.button("＋ Cuộc trò chuyện mới", use_container_width=True)

    st.markdown('<div class="desk-eyebrow">YOUR IT SUPPORT SPACE</div>', unsafe_allow_html=True)
    st.title("Hỗ trợ IT, ngay tại đây.")
    st.write("Mô tả vấn đề bạn đang gặp. Theo dõi câu trả lời và từng bước kiểm tra của agent.")

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
    col1, col2, col3 = st.columns(3)
    col1.metric("Phiên bản", session["config"]["version"] or "—")
    col2.metric("Tools khả dụng", len(session["tools"]))
    col3.metric("Lượt hội thoại", len(turns))
    st.divider()

    if not turns:
        st.markdown("### Bạn cần hỗ trợ gì?")
        st.caption("Một vài câu hỏi để bắt đầu — sao chép vào ô chat bên dưới.")
        for column, title, example in zip(st.columns(3),
            ["🌐 Kết nối", "💻 Thiết bị", "📚 Hướng dẫn"],
            ["Kiểm tra trạng thái dịch vụ VPN.", "Máy tính của tôi đang rất chậm, bạn kiểm tra giúp được không?", "Tìm hướng dẫn xử lý Wi-Fi trên Windows."]):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.write(example)
    for turn in turns:
        render_turn(turn)

    text = st.chat_input("Nhập vấn đề IT của bạn…", disabled=changed or not key_ready or not model or not version)
    if text and text.strip():
        with st.chat_message("user"):
            st.markdown(text.strip())
        with st.spinner("Agent đang kiểm tra và xử lý yêu cầu…"):
            run_turn(session, text.strip())
        st.rerun()

    if turns:
        with st.sidebar:
            st.divider()
            st.download_button("↓ Tải transcript JSON", data=json.dumps(session["transcript"], ensure_ascii=False, indent=2),
                               file_name=session["path"].name, mime="application/json", use_container_width=True)
            st.caption(f"Transcript: {session['path']}")
            if session.get("save_error"):
                st.warning("Không lưu được file trên máy. Dùng nút tải transcript để giữ evidence.")
    st.caption("IT Helpdesk Lab · Dữ liệu mô phỏng · Tool trace xuất hiện sau khi mỗi lượt xử lý hoàn tất.")


if __name__ == "__main__":
    main()
