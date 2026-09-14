"""Lab UI — Version comparison workbench for the IT Helpdesk Agent.

Mục đích: cùng MỘT câu hỏi (hoặc một eval case), đối chiếu hành vi tool-calling
giữa các phiên bản artifact (prompt + tools) — để thấy trực quan vì sao một thay
đổi prompt/tool declaration làm routing/args tốt lên hay xấu đi.

Chạy: python -m streamlit run app.py
Tái sử dụng run_model_tool_loop (thực thi) và HelpdeskAgent + evaluate_phase_b
(chấm điểm giống run_eval), không viết agent loop mới.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import streamlit as st

from agent import HelpdeskAgent
from chat import ARTIFACTS_DIR, ROOT, run_model_tool_loop
from providers import make_provider
from run_eval import case_messages, evaluate_phase_b
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

DATA_DIR = ROOT / "data"
VERSIONS_DIR = ARTIFACTS_DIR / "versions"

MODEL_OPTIONS = {
    "openrouter": ["openai/gpt-4o-mini"],
    "gemini": ["gemini-3.5-flash-lite", "gemini-2.5-flash"],
    "openai": ["gpt-4o-mini"],
    "anthropic": ["claude-haiku-4-5-20251001"],
}

DATASETS = {
    "eval_base": DATA_DIR / "eval_base.json",
    "eval_group": DATA_DIR / "eval_group.json",
    "eval_helpdesk_extension": DATA_DIR / "eval_helpdesk_extension.json",
    "eval_adversarial": DATA_DIR / "eval_adversarial.json",
}


# ----------------------------- data helpers -----------------------------

def discover_versions() -> dict[str, tuple[Path, Path]]:
    """Map version label -> (system_prompt path, tools.yaml path)."""
    presets: dict[str, tuple[Path, Path]] = {
        "current · main": (ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml"),
    }
    if VERSIONS_DIR.exists():
        for d in sorted(VERSIONS_DIR.iterdir()):
            sp, tp = d / "system_prompt.md", d / "tools.yaml"
            if sp.exists() and tp.exists():
                presets[f"{d.name} · snapshot"] = (sp, tp)
    return presets


@st.cache_data(show_spinner=False)
def load_cases(path_str: str) -> list[dict]:
    data = json.loads(Path(path_str).read_text(encoding="utf-8"))
    return data.get("cases", data if isinstance(data, list) else [])


def load_version(label: str, paths: tuple[Path, Path]) -> dict:
    prompt_path, tools_path = paths
    prompt = prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    tools = to_openai_tools(declarations)
    artifact = artifact_version_dict(build_artifact_version(label.split(" ")[0], prompt_path, tools_path))
    return {"label": label, "prompt": prompt, "tools": tools, "artifact": artifact}


def provider_error_summary(exc: Exception, api_key: str) -> str:
    message = " ".join(str(exc).split())
    if api_key:
        message = message.replace(api_key, "[redacted]")
    message = re.sub(r"AIza[\w-]{20,}", "[redacted]", message)
    message = re.sub(r"(key|api[_-]?key)=([^\s&]+)", r"\1=[redacted]", message, flags=re.I)
    return (message or "Provider did not return an error message.")[:500]


def run_execution(provider_name, model, api_key, version, user_text, max_rounds=4) -> dict:
    """Full multi-round execution (chat/compare) — shows real tool results."""
    try:
        result = run_model_tool_loop(
            provider=make_provider(provider_name, api_key=api_key or None),
            messages=[{"role": "system", "content": version["prompt"]},
                      {"role": "user", "content": user_text}],
            tools=version["tools"], model=model, max_tool_rounds=int(max_rounds),
        )
        result["ok"] = True
        return result
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "error_detail": provider_error_summary(exc, api_key)}


def run_grade(provider_name, model, api_key, version, case) -> dict:
    """Single decision + grader (giống run_eval) — cho mode replay."""
    try:
        agent = HelpdeskAgent(make_provider(provider_name, api_key=api_key or None),
                              system_prompt=version["prompt"], tools=version["tools"], model=model)
        tool_choice = None if case["expect"].get("no_tool") else "required"
        run = agent.run(case_messages(case), tool_choice=tool_choice)
        calls = [{"name": c.name, "args": c.args} for c in run.tool_calls]
        grade = evaluate_phase_b(case, calls, run.text)
        grade["ok"] = True
        return grade
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "error_detail": provider_error_summary(exc, api_key)}


def calls_signature(result: dict) -> list[tuple[str, str]]:
    sig = []
    for r in result.get("rounds", []):
        for c in r.get("tool_calls", []):
            sig.append((c["name"], json.dumps(c.get("args", {}), sort_keys=True, ensure_ascii=False)))
    return sig


# ------------------------------- rendering ------------------------------

def render_rounds(rounds: list[dict]) -> None:
    for record in rounds:
        st.markdown(f"**Vòng {record['round']}**")
        if not record.get("tool_calls"):
            st.caption("Trả lời trực tiếp, không gọi tool.")
        for call in record.get("tool_calls", []):
            st.code(call["name"], language=None)
            st.json(call.get("args", {}))
        for event in record.get("tool_results", []):
            res = event.get("result", {})
            if event.get("error") or (isinstance(res, dict) and res.get("error")):
                st.error(f"{event['tool']}: tool trả về lỗi")
            with st.expander(f"Kết quả · {event['tool']}", expanded=False):
                st.json(event)


def render_execution(version_label: str, result: dict) -> None:
    st.markdown(f"**{version_label}**")
    if not result.get("ok"):
        st.error(f"Lỗi provider ({result.get('error')}).")
        st.caption(result.get("error_detail", ""))
        return
    st.caption(f"status: {result['status']} · {len(result.get('tool_events', []))} tool calls")
    if result.get("assistant_text"):
        st.markdown(result["assistant_text"])
    if result.get("rounds"):
        with st.expander("Trace tool-calling", expanded=True):
            render_rounds(result["rounds"])


def render_grade(version_label: str, case: dict, grade: dict) -> None:
    st.markdown(f"**{version_label}**")
    if not grade.get("ok"):
        st.error(f"Lỗi provider ({grade.get('error')}).")
        st.caption(grade.get("error_detail", ""))
        return
    if grade.get("passed"):
        st.success("✅ PASS")
    else:
        st.error("❌ FAIL")
        cols = f"routing={grade.get('routing_correct')} · args={grade.get('args_correct')} · mismatch={grade.get('observed_mismatch')}"
        st.caption(cols)
    st.caption("Expected")
    st.json(case["expect"].get("tool_calls", []) if not case["expect"].get("no_tool") else "no_tool")
    st.caption("Actual")
    st.json(grade.get("actual_tool_calls", []))
    if grade.get("failures"):
        for f in grade["failures"]:
            st.caption(f"• {f}")


# --------------------------------- main ---------------------------------

def main() -> None:
    st.set_page_config(page_title="DeskMate | Version Compare", page_icon="✦", layout="wide",
                       initial_sidebar_state="expanded")
    css = Path(__file__).with_name("ui.css")
    if css.exists():
        st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    versions = discover_versions()
    version_labels = list(versions.keys())

    # ---- Sidebar: kết nối AI + tùy chọn ----
    with st.sidebar:
        st.markdown("### ✦ DeskMate")
        st.caption("FAST AND FOURIOUS · DAY 04 — Version compare workbench")
        st.divider()
        st.markdown("**Kết nối AI**")
        provider_name = st.selectbox("Provider", ["openrouter", "gemini", "openai", "anthropic"], key="provider",
                                     format_func=lambda n: {"openrouter": "OpenRouter", "gemini": "Gemini",
                                                            "openai": "OpenAI", "anthropic": "Anthropic"}[n])
        provider = make_provider(provider_name)
        model = st.selectbox("Model", MODEL_OPTIONS[provider_name], key="model")
        api_key = st.text_input("API key", type="password", placeholder=f"Nhập {provider.api_key_env}", key="api_key",
                                help="Chỉ giữ trong phiên UI; không ghi .env/transcript/Git.").strip()
        key_ready = bool(api_key or os.getenv(provider.api_key_env))
        st.caption("● Đã có key" if key_ready else "○ Chưa có key")
        max_rounds = st.number_input("Giới hạn vòng tool/lượt", 1, 12, 4)
        st.divider()
        st.caption("Versions phát hiện được:")
        for lbl, (sp, _tp) in versions.items():
            st.caption(f"• {lbl}")

    # ---- Header ----
    st.markdown("## 🔬 So sánh phiên bản Agent")
    st.markdown("Cùng một câu hỏi (hoặc eval case) → đối chiếu **hành vi tool-calling** giữa các "
                "phiên bản artifact. Trả lời câu hỏi cốt lõi của lab: *thay đổi prompt/tool "
                "declaration nào tạo ra khác biệt đo được?*")

    mode = st.radio("Chế độ", ["🆚 So sánh 2 version", "🎯 Replay eval case", "💬 Trò chuyện 1 version"],
                    horizontal=True, label_visibility="collapsed")

    if not key_ready:
        st.info("Điền **API key** ở thanh bên (hoặc để trống nếu `.env` đã có key) để chạy.")

    # ============ MODE 1: So sánh 2 version ============
    if mode.startswith("🆚"):
        c1, c2 = st.columns(2)
        with c1:
            la = st.selectbox("Version A", version_labels, key="cmp_a",
                              index=version_labels.index(next((l for l in version_labels if "v0" in l), version_labels[-1])))
        with c2:
            lb = st.selectbox("Version B", version_labels, index=0, key="cmp_b")
        query = st.text_area("Câu hỏi để chạy trên CẢ HAI version", key="cmp_query",
                             value="Kiểm tra Wi-Fi trên laptop của mình giúp nhé.", height=80)
        if st.button("▶ Chạy so sánh", type="primary", disabled=not key_ready, key="run_compare"):
            with st.spinner("Đang chạy trên 2 version…"):
                va, vb = load_version(la, versions[la]), load_version(lb, versions[lb])
                ra = run_execution(provider_name, model, api_key, va, query, max_rounds)
                rb = run_execution(provider_name, model, api_key, vb, query, max_rounds)
            st.session_state["cmp"] = {"la": la, "lb": lb, "ra": ra, "rb": rb,
                                       "sa": va["artifact"]["artifact_version"], "sb": vb["artifact"]["artifact_version"]}
        cmp = st.session_state.get("cmp")
        if cmp:
            sig_a, sig_b = calls_signature(cmp["ra"]), calls_signature(cmp["rb"])
            if cmp["ra"].get("ok") and cmp["rb"].get("ok"):
                if sig_a == sig_b:
                    st.info("↔️ Hai version gọi tool **giống hệt** (name + args). Khác biệt nếu có nằm ở nội dung trả lời.")
                else:
                    st.warning("⚠️ Tool-calling **KHÁC nhau** giữa A và B — xem trace bên dưới.")
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(cmp["sa"])
                render_execution(cmp["la"], cmp["ra"])
            with col_b:
                st.caption(cmp["sb"])
                render_execution(cmp["lb"], cmp["rb"])

    # ============ MODE 2: Replay eval case ============
    elif mode.startswith("🎯"):
        c1, c2 = st.columns([1, 2])
        with c1:
            ds = st.selectbox("Dataset", list(DATASETS.keys()))
        cases = load_cases(str(DATASETS[ds]))
        with c2:
            cid = st.selectbox("Case", [c["id"] for c in cases])
        case = next(c for c in cases if c["id"] == cid)
        with st.expander("Nội dung case", expanded=True):
            if "turns" in case:
                for t in case["turns"]:
                    st.markdown(f"**{t['role']}:** {t['content']}")
            else:
                st.markdown(f"**input:** {case.get('input') or case.get('query', '')}")
            st.caption("Expected")
            st.json(case["expect"])
        cc1, cc2 = st.columns(2)
        with cc1:
            la = st.selectbox("Version A ", version_labels,
                              index=version_labels.index(next((l for l in version_labels if "v0" in l), version_labels[-1])), key="rp_a")
        with cc2:
            lb = st.selectbox("Version B ", version_labels, index=0, key="rp_b")
        if st.button("▶ Replay trên 2 version", type="primary", disabled=not key_ready):
            with st.spinner("Đang chấm 2 version…"):
                va, vb = load_version(la, versions[la]), load_version(lb, versions[lb])
                ga = run_grade(provider_name, model, api_key, va, case)
                gb = run_grade(provider_name, model, api_key, vb, case)
            st.session_state["rp"] = {"la": la, "lb": lb, "ga": ga, "gb": gb}
        rp = st.session_state.get("rp")
        if rp:
            col_a, col_b = st.columns(2)
            with col_a:
                render_grade(rp["la"], case, rp["ga"])
            with col_b:
                render_grade(rp["lb"], case, rp["gb"])

    # ============ MODE 3: Trò chuyện 1 version ============
    else:
        lbl = st.selectbox("Version", version_labels, index=0)
        query = st.text_input("Câu hỏi")
        if st.button("▶ Gửi", type="primary", disabled=not key_ready) and query.strip():
            with st.spinner("Agent đang xử lý…"):
                v = load_version(lbl, versions[lbl])
                res = run_execution(provider_name, model, api_key, v, query.strip(), max_rounds)
            st.session_state["chat"] = {"lbl": lbl, "res": res, "sig": v["artifact"]["artifact_version"]}
        chat = st.session_state.get("chat")
        if chat:
            st.caption(chat["sig"])
            render_execution(chat["lbl"], chat["res"])


if __name__ == "__main__":
    main()
