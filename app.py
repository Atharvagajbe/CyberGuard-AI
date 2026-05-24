import json
import os
import re
from string import Template
from datetime import datetime, timezone

import streamlit as st

try:
    from google import genai
except ImportError:  # Keeps demo mode usable before dependencies are installed.
    genai = None

try:
    from google.cloud import firestore, storage
except ImportError:
    firestore = None
    storage = None


DEFAULT_LOG_INPUT = """Multiple failed SSH login attempts detected from unknown IP.
User root login failed 15 times.
Port scanning activity found."""
DEFAULT_CODE_INPUT = """query = "SELECT * FROM users WHERE username = '" + username + "'" """


RISK_COLORS = {
    "Low": "#0f8a5f",
    "Medium": "#b7791f",
    "High": "#d13f32",
    "Critical": "#8f1d2c",
}

THEMES = {
    "Light": {
        "app_bg": "radial-gradient(circle at top left, rgba(18, 168, 180, 0.16), transparent 30rem), linear-gradient(180deg, #f7fbfd 0%, #eef5f8 48%, #f8fafc 100%)",
        "ink": "#102033",
        "muted": "#53677f",
        "line": "#cbd9e8",
        "panel": "rgba(255, 255, 255, 0.9)",
        "panel_solid": "#ffffff",
        "field": "#ffffff",
        "field_text": "#102033",
        "field_label": "#24384f",
        "field_placeholder": "#708096",
        "action": "#f7fafc",
        "shadow": "0 12px 32px rgba(40, 64, 88, 0.1)",
        "tab": "#31445c",
        "accent": "#0f7280",
        "code_bg": "#f6f9fc",
    },
    "Dark": {
        "app_bg": "radial-gradient(circle at top left, rgba(20, 184, 166, 0.14), transparent 30rem), linear-gradient(180deg, #0b1320 0%, #101827 52%, #0d1421 100%)",
        "ink": "#edf6ff",
        "muted": "#a8b7ca",
        "line": "#284057",
        "panel": "rgba(15, 27, 43, 0.92)",
        "panel_solid": "#111e30",
        "field": "#0c1727",
        "field_text": "#f4f8ff",
        "field_label": "#d9e7f6",
        "field_placeholder": "#8fa3ba",
        "action": "#15243a",
        "shadow": "0 14px 38px rgba(0, 0, 0, 0.28)",
        "tab": "#c7d5e6",
        "accent": "#2dd4bf",
        "code_bg": "#08111f",
    },
}


def get_setting(name, default=None):
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def configure_page():
    st.set_page_config(
        page_title="CyberGuard AI",
        page_icon=":shield:",
        layout="wide",
    )
    theme_name = st.sidebar.radio(
        "Theme",
        ["Light", "Dark"],
        horizontal=True,
        key="cyberguard_theme",
    )
    theme = THEMES[theme_name]
    css = Template(
        """
        <style>
            :root {
                --cg-ink: $ink;
                --cg-muted: $muted;
                --cg-line: $line;
                --cg-panel: $panel;
                --cg-panel-solid: $panel_solid;
                --cg-field: $field;
                --cg-field-text: $field_text;
                --cg-field-label: $field_label;
                --cg-field-placeholder: $field_placeholder;
                --cg-action: $action;
                --cg-shadow: $shadow;
                --cg-tab: $tab;
                --cg-accent: $accent;
                --cg-code-bg: $code_bg;
                --cg-cyan: #12a8b4;
                --cg-green: #15996d;
                --cg-blue: #2563eb;
            }

            .stApp {
                background: $app_bg;
                color: var(--cg-ink);
            }

            .block-container {
                max-width: 1180px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                letter-spacing: 0;
                color: var(--cg-ink);
            }

            p, li, label, span, div[data-testid="stMarkdownContainer"] {
                color: var(--cg-ink);
            }

            section[data-testid="stSidebar"] {
                background: var(--cg-panel-solid);
                border-right: 1px solid var(--cg-line);
            }

            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {
                color: var(--cg-ink);
            }

            div[data-testid="stWidgetLabel"] label,
            div[data-testid="stWidgetLabel"] p {
                color: var(--cg-field-label);
                font-weight: 750;
            }

            div[data-testid="stTabs"] button {
                border-radius: 0.5rem 0.5rem 0 0;
                color: var(--cg-tab);
                font-weight: 700;
            }

            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: var(--cg-accent);
                border-bottom-color: var(--cg-accent);
            }

            div[data-testid="stTextArea"] textarea {
                border: 1px solid var(--cg-line);
                border-radius: 0.6rem;
                background: var(--cg-field);
                color: var(--cg-field-text);
                caret-color: var(--cg-accent);
                font-size: 0.95rem;
                line-height: 1.55;
                box-shadow: inset 0 1px 2px rgba(16, 32, 51, 0.04);
            }

            div[data-testid="stTextArea"] textarea::placeholder {
                color: var(--cg-field-placeholder);
                opacity: 1;
            }

            div[data-testid="stTextArea"] textarea:focus {
                border-color: var(--cg-accent);
                box-shadow: 0 0 0 0.15rem rgba(18, 168, 180, 0.2);
            }

            .stButton > button {
                border-radius: 0.55rem;
                font-weight: 800;
                min-height: 2.8rem;
                border: 0;
                color: #ffffff;
                box-shadow: 0 10px 20px rgba(18, 168, 180, 0.18);
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #0e7490, #12a8b4);
            }

            .cg-hero {
                border: 1px solid rgba(18, 168, 180, 0.2);
                border-radius: 0.8rem;
                padding: 1.6rem;
                background:
                    linear-gradient(135deg, rgba(16, 32, 51, 0.96), rgba(11, 79, 98, 0.9)),
                    url("assets/cyberguard-banner.png");
                background-size: cover;
                background-position: center;
                color: white;
                box-shadow: 0 18px 50px rgba(16, 32, 51, 0.18);
                margin-bottom: 1.3rem;
            }

            .cg-hero h1 {
                margin: 0 0 0.45rem;
                font-size: 3rem;
                line-height: 1;
            }

            .cg-hero p {
                max-width: 46rem;
                margin: 0;
                color: rgba(255, 255, 255, 0.82);
                font-size: 1.05rem;
                line-height: 1.6;
            }

            .cg-kicker {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.35rem 0.65rem;
                margin-bottom: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.26);
                border-radius: 999px;
                color: rgba(255, 255, 255, 0.86);
                background: rgba(255, 255, 255, 0.1);
                font-size: 0.8rem;
                font-weight: 800;
                text-transform: uppercase;
            }

            .cg-mode {
                border: 1px solid var(--cg-line);
                border-radius: 0.75rem;
                padding: 0.85rem 1rem;
                background: var(--cg-panel);
                color: var(--cg-ink);
                margin-bottom: 1.2rem;
            }

            .cg-mode strong {
                color: var(--cg-accent);
            }

            .cg-mode code {
                color: var(--cg-ink);
                background: var(--cg-code-bg);
                border: 1px solid var(--cg-line);
                border-radius: 0.3rem;
                padding: 0.1rem 0.25rem;
            }

            .cg-panel {
                border: 1px solid var(--cg-line);
                border-radius: 0.75rem;
                padding: 1.05rem;
                background: var(--cg-panel);
                box-shadow: var(--cg-shadow);
                margin: 0.7rem 0 1rem;
            }

            .cg-section-title {
                margin: 0 0 0.25rem;
                font-size: 1.35rem;
                font-weight: 850;
                color: var(--cg-ink);
            }

            .cg-section-copy {
                margin: 0 0 1rem;
                color: var(--cg-muted);
                line-height: 1.55;
            }

            .cg-result {
                border: 1px solid var(--cg-line);
                border-radius: 0.75rem;
                padding: 1rem;
                background: var(--cg-panel-solid);
                color: var(--cg-ink);
                box-shadow: var(--cg-shadow);
                margin-top: 1rem;
            }

            .cg-result h3 {
                margin: 0 0 0.8rem;
                font-size: 1.05rem;
                color: var(--cg-ink);
            }

            .cg-result p {
                color: var(--cg-ink);
            }

            .cg-badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 7rem;
                padding: 0.55rem 0.8rem;
                border-radius: 999px;
                color: white;
                font-weight: 850;
                box-shadow: 0 8px 18px rgba(16, 32, 51, 0.14);
            }

            .cg-actions {
                margin: 0.6rem 0 0;
                padding: 0;
                list-style: none;
            }

            .cg-actions li {
                padding: 0.65rem 0.75rem;
                margin: 0 0 0.45rem;
                border: 1px solid var(--cg-line);
                border-radius: 0.55rem;
                background: var(--cg-action);
                color: var(--cg-ink);
            }

            .cg-save-note {
                color: var(--cg-muted);
                font-size: 0.85rem;
                margin-top: 0.8rem;
            }

            div[data-testid="stExpander"] {
                border: 1px solid var(--cg-line);
                border-radius: 0.7rem;
                background: var(--cg-panel);
                color: var(--cg-ink);
            }

            div[data-testid="stExpander"] summary,
            div[data-testid="stExpander"] p {
                color: var(--cg-ink);
            }

            div[data-testid="stCodeBlock"] {
                background: var(--cg-code-bg);
                border: 1px solid var(--cg-line);
                border-radius: 0.65rem;
            }

            @media (max-width: 700px) {
                .block-container {
                    padding-top: 1rem;
                }

                .cg-hero {
                    padding: 1.15rem;
                }

                .cg-hero h1 {
                    font-size: 2.25rem;
                }
            }
        </style>
        """,
    ).substitute(theme)
    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def escape_html(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def has_gemini():
    return bool(get_setting("GEMINI_API_KEY")) and genai is not None


def gemini_model():
    return genai.Client(api_key=get_setting("GEMINI_API_KEY"))


def extract_json(text):
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Gemini response did not include JSON.")
    return json.loads(match.group(0))


def call_gemini_json(prompt, fallback):
    if not has_gemini():
        return fallback()

    try:
        response = gemini_model().models.generate_content(
            model=get_setting("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=prompt,
        )
        return extract_json(response.text)
    except Exception as exc:
        st.warning(f"Gemini live analysis failed, using demo mode instead. Details: {exc}")
        return fallback()


def summarize_security_text(security_text):
    prompt = f"""
You are a cybersecurity incident triage assistant.
Analyze the following logs, phishing email, or incident report.
Return only JSON with these keys:
summary, risk_level, recommended_actions.
recommended_actions must be a list of short action strings.

Security text:
{security_text}
"""

    def fallback():
        lowered = security_text.lower()
        actions = ["Check server logs", "Review affected accounts"]
        risk = "Medium"
        summary = "Suspicious security activity requires investigation."

        if "failed" in lowered and ("ssh" in lowered or "login" in lowered):
            summary = "Possible brute-force attack."
            risk = "High"
            actions = [
                "Block suspicious IP",
                "Disable root SSH login",
                "Enable MFA",
                "Check server logs",
            ]
        elif "phishing" in lowered or "password" in lowered or "urgent" in lowered:
            summary = "Possible phishing attempt."
            risk = "High"
            actions = [
                "Do not click links",
                "Report the email",
                "Reset exposed credentials",
                "Scan related inboxes",
            ]
        elif "port scan" in lowered or "scanning" in lowered:
            summary = "Possible reconnaissance activity."
            risk = "Medium"
            actions = ["Block scanner IP", "Review firewall rules", "Inspect exposed services"]

        return {
            "summary": summary,
            "risk_level": risk,
            "recommended_actions": actions,
        }

    return call_gemini_json(prompt, fallback)


def debug_secure_code(code_text):
    prompt = f"""
You are a secure code reviewer.
Find the most important vulnerability in this snippet and suggest a secure fix.
Return only JSON with these keys:
vulnerability, severity, problem, secure_fix, fixed_code.

Code:
{code_text}
"""

    def fallback():
        lowered = code_text.lower()
        if "select" in lowered and "+" in code_text:
            return {
                "vulnerability": "SQL Injection",
                "severity": "Critical",
                "problem": "User input is directly added to a SQL query string.",
                "secure_fix": "Use parameterized queries so user input is treated as data, not executable SQL.",
                "fixed_code": 'cursor.execute("SELECT * FROM users WHERE username = ?", (username,))',
            }
        if "password" in lowered and ("=" in code_text or ":" in code_text):
            return {
                "vulnerability": "Hardcoded Secret",
                "severity": "High",
                "problem": "Sensitive credentials appear to be stored directly in source code.",
                "secure_fix": "Move secrets to a secret manager or environment variable and rotate exposed values.",
                "fixed_code": 'password = os.environ["DATABASE_PASSWORD"]',
            }
        return {
            "vulnerability": "Security Review Needed",
            "severity": "Medium",
            "problem": "The snippet may need deeper review for input validation, authentication, or data exposure issues.",
            "secure_fix": "Validate inputs, use safe libraries, and avoid manual construction of sensitive operations.",
            "fixed_code": code_text,
        }

    return call_gemini_json(prompt, fallback)


def save_to_firestore(collection, payload):
    if firestore is None or not get_setting("GOOGLE_CLOUD_PROJECT"):
        return False
    db = firestore.Client()
    db.collection(collection).add(payload)
    return True


def save_to_cloud_storage(blob_name, payload):
    bucket_name = get_setting("CYBERGUARD_BUCKET")
    if storage is None or not bucket_name:
        return False
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(payload, indent=2), content_type="application/json")
    return True


def persist_result(kind, request_text, result):
    payload = {
        "kind": kind,
        "request": request_text,
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    firestore_saved = save_to_firestore("cyberguard_analyses", payload)
    storage_saved = save_to_cloud_storage(
        f"cyberguard/{kind}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json",
        payload,
    )
    return firestore_saved, storage_saved


def render_status_badge(label):
    st.markdown(status_badge_html(label), unsafe_allow_html=True)


def status_badge_html(label):
    color = RISK_COLORS.get(label, "#334155")
    return f"<span class='cg-badge' style='background:{color}'>{escape_html(label)}</span>"


def render_header():
    mode = "Gemini API" if has_gemini() else "Demo mode"
    st.markdown(
        f"""
        <section class="cg-hero">
            <div class="cg-kicker">Cybersecurity triage assistant</div>
            <h1>CyberGuard AI</h1>
            <p>
                Analyze suspicious logs, phishing messages, and risky code with a focused
                Gemini-powered workflow built for fast security review.
            </p>
        </section>
        <div class="cg-mode">
            Current model mode: <strong>{mode}</strong>. Add <code>GEMINI_API_KEY</code>
            to use live Gemini analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summarizer_tab():
    st.markdown(
        """
        <div class="cg-panel">
            <p class="cg-section-title">Security Log / Email Summarizer</p>
            <p class="cg-section-copy">
                Paste a suspicious event, phishing message, or incident note to get a
                concise triage summary and action list.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    security_text = st.text_area(
        "Paste security logs, phishing emails, or incident reports",
        value=DEFAULT_LOG_INPUT,
        height=180,
    )

    if st.button("Analyze Security Text", type="primary"):
        result = summarize_security_text(security_text)
        persist = persist_result("summary", security_text, result)

        left, right = st.columns([2, 1])
        with left:
            actions = "".join(
                f"<li>{escape_html(action)}</li>" for action in result["recommended_actions"]
            )
            st.markdown(
                f"""
                <div class="cg-result">
                    <h3>Security Summary</h3>
                    <p>{escape_html(result["summary"])}</p>
                    <h3>Recommended Actions</h3>
                    <ul class="cg-actions">{actions}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                f"""
                <div class="cg-result">
                    <h3>Risk Level</h3>
                    {status_badge_html(result["risk_level"])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<p class='cg-save-note'>Saved to Firestore: {persist[0]} | Saved to Cloud Storage: {persist[1]}</p>",
            unsafe_allow_html=True,
        )


def render_code_debugger_tab():
    st.markdown(
        """
        <div class="cg-panel">
            <p class="cg-section-title">Secure Code Debugger</p>
            <p class="cg-section-copy">
                Drop in a snippet to identify the biggest security issue, understand the
                risk, and generate a safer replacement pattern.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    code_text = st.text_area(
        "Paste insecure or suspicious code",
        value=DEFAULT_CODE_INPUT,
        height=180,
    )

    if st.button("Debug Code Security", type="primary"):
        result = debug_secure_code(code_text)
        persist = persist_result("code-debug", code_text, result)

        left, right = st.columns([2, 1])
        with left:
            st.markdown(
                f"""
                <div class="cg-result">
                    <h3>Vulnerability</h3>
                    <p>{escape_html(result["vulnerability"])}</p>
                    <h3>Problem</h3>
                    <p>{escape_html(result["problem"])}</p>
                    <h3>Secure Fix</h3>
                    <p>{escape_html(result["secure_fix"])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(result["fixed_code"], language="python")
        with right:
            st.markdown(
                f"""
                <div class="cg-result">
                    <h3>Severity</h3>
                    {status_badge_html(result["severity"])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<p class='cg-save-note'>Saved to Firestore: {persist[0]} | Saved to Cloud Storage: {persist[1]}</p>",
            unsafe_allow_html=True,
        )


def main():
    configure_page()
    render_header()

    tab_summary, tab_code = st.tabs(
        ["Security Log / Email Summarizer", "Secure Code Debugger"]
    )
    with tab_summary:
        render_summarizer_tab()
    with tab_code:
        render_code_debugger_tab()

    with st.expander("Google Cloud Architecture"):
        st.write("Streamlit UI -> Gemini API -> Firestore / Cloud Storage -> Cloud Run deployment")


if __name__ == "__main__":
    main()
