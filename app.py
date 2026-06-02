import json
import os
import re
from pathlib import Path
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


def load_env_file():
    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


RISK_COLORS = {
    "Low": "#0f8a5f",
    "Medium": "#b7791f",
    "High": "#d13f32",
    "Critical": "#8f1d2c",
}

THEMES = {
    "Light": {
        "app_bg": "linear-gradient(180deg, #fbfcf8 0%, #eef9f8 52%, #f8fcff 100%)",
        "ink": "#08111f",
        "muted": "#5d6f78",
        "line": "#dbe6e6",
        "panel": "#ffffff",
        "panel_solid": "#ffffff",
        "field": "#ffffff",
        "field_text": "#08111f",
        "field_label": "#08111f",
        "field_placeholder": "#708096",
        "action": "#f8fbfd",
        "shadow": "0 24px 70px rgba(13, 66, 90, 0.1)",
        "tab": "#08111f",
        "accent": "#0a9f8f",
        "accent_hover": "#087f73",
        "code_bg": "#eef6f8",
        "code_text": "#0b4b5d",
        "hero_bg": "linear-gradient(135deg, #06121f 0%, #09384b 52%, #0b7580 100%)",
        "hero_shadow": "0 32px 90px rgba(4, 45, 66, 0.26)",
        "sidebar_bg": "#ffffff",
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
        "accent_hover": "#14b8a6",
        "code_bg": "#08111f",
        "code_text": "#9ff5e8",
        "hero_bg": "linear-gradient(135deg, #07111f 0%, #123c50 55%, #0f6d78 100%)",
        "hero_shadow": "0 28px 80px rgba(0, 0, 0, 0.35)",
        "sidebar_bg": "#111e30",
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
        page_icon="🛡️",
        layout="wide",
    )
    if "cyberguard_theme" not in st.session_state:
        st.session_state.cyberguard_theme = "Light"
    theme_name = st.session_state.cyberguard_theme
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
                --cg-accent-hover: $accent_hover;
                --cg-code-bg: $code_bg;
                --cg-code-text: $code_text;
                --cg-hero-bg: $hero_bg;
                --cg-hero-shadow: $hero_shadow;
                --cg-sidebar-bg: $sidebar_bg;
                --cg-cyan: #12a8b4;
                --cg-green: #15996d;
                --cg-blue: #2563eb;
            }

            .stApp {
                background: $app_bg;
                color: var(--cg-ink);
            }

            header[data-testid="stHeader"],
            div[data-testid="stToolbar"],
            div[data-testid="stDecoration"],
            #MainMenu,
            footer {
                visibility: hidden;
                height: 0;
            }

            .block-container {
                max-width: 1120px;
                padding-top: 2rem;
                padding-bottom: 4rem;
            }

            h1, h2, h3 {
                letter-spacing: 0;
                color: var(--cg-ink);
            }

            p, li, label, span, div[data-testid="stMarkdownContainer"] {
                color: var(--cg-ink);
            }

            section[data-testid="stSidebar"] {
                background: var(--cg-sidebar-bg);
                border-right: 1px solid var(--cg-line);
            }

            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {
                color: var(--cg-ink);
            }

            .cg-nav {
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-sizing: border-box;
                gap: 22px;
                width: min(100%, 960px);
                min-height: 72px;
                padding: 10px 12px 10px 18px;
                margin: 0 auto 54px;
                border: 1px solid var(--cg-line);
                border-radius: 999px;
                background: var(--cg-panel);
                box-shadow: 0 18px 55px rgba(8, 17, 31, 0.1);
                backdrop-filter: blur(18px);
            }

            .cg-brand {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                color: var(--cg-ink);
                font-weight: 900;
                min-width: 210px;
                font-size: 0.98rem;
            }

            .cg-brand span,
            .cg-nav-links span {
                color: inherit;
            }

            .cg-brand-mark {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 38px;
                height: 38px;
                border-radius: 999px;
                background: #07111f;
                color: #ffffff;
                font-weight: 900;
            }

            .cg-nav-links {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 28px;
                color: var(--cg-muted);
                font-size: 0.92rem;
                font-weight: 850;
                flex: 1;
            }

            .cg-nav-action {
                display: inline-flex;
                align-items: center;
                justify-content: flex-end;
                min-width: auto;
                min-height: auto;
                padding: 0;
                border-radius: 999px;
                background: transparent;
                box-shadow: none;
            }

            .cg-nav-cta {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 48px;
                min-width: 132px;
                padding: 0 22px;
                border-radius: 999px;
                background: #07111f;
                color: #ffffff;
                font-weight: 900;
                font-size: 0.95rem;
                box-shadow: 0 14px 28px rgba(8, 17, 31, 0.25);
            }

            .cg-nav-cta {
                color: #ffffff;
            }

            .cg-theme-label {
                width: fit-content;
                margin: -36px auto 48px;
                padding: 8px 14px;
                border: 1px solid var(--cg-line);
                border-radius: 999px;
                background: var(--cg-panel);
                color: var(--cg-muted);
                font-size: 0.82rem;
                font-weight: 850;
                box-shadow: 0 12px 34px rgba(8, 17, 31, 0.08);
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) {
                width: fit-content;
                margin: -42px auto 48px;
                padding: 6px;
                border: 1px solid var(--cg-line);
                border-radius: 999px;
                background: var(--cg-panel);
                box-shadow: 0 12px 34px rgba(8, 17, 31, 0.08);
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) > label {
                display: none;
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) [role="radiogroup"] {
                display: flex;
                gap: 4px;
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) [role="radio"] {
                min-height: 36px;
                padding: 0 14px;
                border-radius: 999px;
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) [role="radio"] p {
                color: var(--cg-muted) !important;
                font-weight: 850;
                margin: 0 !important;
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) [aria-checked="true"] {
                background: #07111f;
            }

            div[data-testid="stRadio"]:has(input[value="Light"]) [aria-checked="true"] p {
                color: #ffffff !important;
            }

            .cg-theme-toggle {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px;
                border: 1px solid var(--cg-line);
                border-radius: 999px;
                background: var(--cg-action);
            }

            .cg-theme-toggle div[data-testid="stButton"] {
                width: auto;
            }

            .cg-theme-toggle .stButton > button {
                min-width: 52px;
                min-height: 34px;
                padding: 0 12px;
                border-radius: 999px;
                background: transparent;
                color: var(--cg-muted);
                box-shadow: none;
                font-size: 0.82rem;
            }

            .cg-theme-toggle .stButton > button *,
            .cg-theme-toggle .stButton > button p,
            .cg-theme-toggle .stButton > button span {
                color: var(--cg-muted) !important;
            }

            .cg-theme-toggle .stButton > button:hover {
                background: var(--cg-panel);
                transform: none;
            }

            .cg-theme-toggle .stButton > button[kind="primary"] {
                background: #08111f;
                color: #ffffff;
                box-shadow: 0 10px 22px rgba(8, 17, 31, 0.14);
            }

            .cg-theme-toggle .stButton > button[kind="primary"] *,
            .cg-theme-toggle .stButton > button[kind="primary"] p,
            .cg-theme-toggle .stButton > button[kind="primary"] span {
                color: #ffffff !important;
            }

            div[data-testid="stWidgetLabel"] label,
            div[data-testid="stWidgetLabel"] p {
                color: var(--cg-field-label);
                font-weight: 750;
            }

            div[data-testid="stTabs"] button {
                color: var(--cg-tab);
                font-weight: 800;
                padding-left: 0;
                padding-right: 0;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 20px;
                border-bottom: 1px solid var(--cg-line);
            }

            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: var(--cg-accent);
                border-bottom-color: var(--cg-accent);
            }

            div[data-testid="stTextArea"] textarea {
                border: 1px solid var(--cg-line);
                border-radius: 14px;
                background: var(--cg-field);
                color: var(--cg-field-text);
                caret-color: var(--cg-accent);
                font-size: 15px;
                line-height: 1.6;
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
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 220px;
                width: auto;
                min-height: 52px;
                border-radius: 999px;
                font-weight: 800;
                border: 0;
                color: #ffffff;
                background: var(--cg-accent);
                padding: 0 24px;
                box-shadow: 0 12px 24px rgba(7, 147, 164, 0.25);
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .stButton > button *,
            .stButton > button p,
            .stButton > button span {
                color: #ffffff !important;
                margin: 0 !important;
                white-space: nowrap;
            }

            .stButton > button:hover,
            .stButton > button:focus,
            .stButton > button:active {
                background: var(--cg-accent-hover);
                color: #ffffff;
                transform: translateY(-1px);
            }

            .stButton > button:hover *,
            .stButton > button:focus *,
            .stButton > button:active * {
                color: #ffffff !important;
            }

            .cg-hero {
                max-width: 930px;
                margin: 0 auto 18px;
                text-align: center;
                color: var(--cg-ink);
            }

            .cg-hero h1 {
                max-width: 860px;
                margin: 0 auto;
                font-size: 68px;
                line-height: 1;
                font-weight: 900;
                letter-spacing: 0;
                color: var(--cg-ink);
            }

            .cg-hero p {
                max-width: 720px;
                margin: 22px auto 0;
                color: var(--cg-muted);
                font-size: 18px;
                line-height: 1.7;
            }

            .cg-kicker {
                display: inline-block;
                padding: 9px 15px;
                margin-bottom: 26px;
                border: 1px solid var(--cg-line);
                border-radius: 999px;
                color: var(--cg-ink);
                background: var(--cg-panel);
                box-shadow: 0 12px 32px rgba(8, 17, 31, 0.06);
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0;
            }

            .cg-hero-actions {
                display: flex;
                align-items: center;
                justify-content: center;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 24px;
            }

            .cg-hero-button,
            .cg-hero-secondary {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 48px;
                padding: 0 22px;
                border-radius: 999px;
                font-weight: 900;
            }

            .cg-hero-button {
                background: #08111f;
                color: #ffffff;
                box-shadow: 0 16px 36px rgba(8, 17, 31, 0.2);
            }

            .cg-hero-secondary {
                border: 1px solid var(--cg-line);
                background: var(--cg-panel);
                color: var(--cg-ink);
            }

            .cg-mode {
                max-width: 930px;
                border: 1px solid var(--cg-line);
                border-radius: 18px;
                padding: 18px 20px;
                background: var(--cg-panel);
                color: var(--cg-ink);
                margin: 32px auto 34px;
                box-shadow: var(--cg-shadow);
            }

            .cg-mode strong {
                color: var(--cg-accent);
                font-weight: 800;
            }

            .cg-mode code {
                color: var(--cg-code-text);
                background: var(--cg-code-bg);
                border-radius: 5px;
                padding: 3px 6px;
            }

            .cg-panel,
            .glass-card {
                border: 1px solid var(--cg-line);
                border-radius: 22px;
                padding: 24px;
                background: var(--cg-panel);
                box-shadow: var(--cg-shadow);
                margin-bottom: 22px;
            }

            .cg-section-title,
            .glass-card h3 {
                margin: 0 0 0.5rem;
                font-size: 20px;
                font-weight: 900;
                color: var(--cg-ink);
            }

            .cg-section-copy,
            .muted-text {
                margin: 0;
                color: var(--cg-muted);
                font-size: 14px;
                line-height: 1.6;
            }

            .cg-result,
            .result-card {
                border: 1px solid var(--cg-line);
                border-radius: 22px;
                padding: 24px;
                background: var(--cg-panel-solid);
                color: var(--cg-ink);
                box-shadow: var(--cg-shadow);
                margin-top: 1rem;
            }

            .cg-result h3,
            .result-card h3 {
                margin: 0 0 0.9rem;
                font-size: 20px;
                font-weight: 900;
                color: var(--cg-ink);
            }

            .cg-result p {
                color: var(--cg-ink);
            }

            .cg-badge,
            .risk-pill,
            .critical-pill {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 7rem;
                padding: 12px 38px;
                border-radius: 999px;
                color: white;
                font-weight: 900;
                box-shadow: 0 8px 18px rgba(16, 32, 51, 0.14);
            }

            .risk-pill {
                background: #e84c3d;
            }

            .critical-pill {
                background: #a1192b;
            }

            .cg-actions {
                margin: 0.6rem 0 0;
                padding: 0;
                list-style: none;
            }

            .cg-actions li,
            .action-item {
                padding: 14px 16px;
                margin-bottom: 10px;
                border: 1px solid var(--cg-line);
                border-radius: 10px;
                background: var(--cg-action);
                color: var(--cg-ink);
                font-weight: 600;
            }

            .cg-save-note {
                color: var(--cg-muted);
                font-size: 0.85rem;
                margin-top: 0.8rem;
            }

            div[data-testid="stExpander"] {
                border: 1px solid var(--cg-line);
                border-radius: 18px;
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
                border-radius: 10px;
            }

            code {
                background: var(--cg-code-bg) !important;
                color: var(--cg-code-text) !important;
                padding: 3px 6px !important;
                border-radius: 5px !important;
            }

            @media (max-width: 700px) {
                .block-container {
                    padding-top: 1.2rem;
                }

                .cg-hero {
                    margin-top: 0;
                }

                .cg-hero h1 {
                    font-size: 44px;
                }

                .cg-nav {
                    min-height: auto;
                    padding: 18px;
                    border-radius: 28px;
                    align-items: flex-start;
                    flex-direction: column;
                    gap: 18px;
                }

                .cg-nav-links {
                    gap: 14px;
                    flex-wrap: wrap;
                    justify-content: flex-start;
                }

                .cg-nav-action {
                    min-width: 100%;
                    justify-content: center;
                    min-height: 56px;
                    padding: 0 8px;
                }

                .cg-brand {
                    min-width: auto;
                }
            }

            @media (min-width: 701px) and (max-width: 1050px) {
                .cg-nav {
                    width: min(100%, 900px);
                    gap: 18px;
                }

                .cg-brand {
                    min-width: 210px;
                }

                .cg-nav-links {
                    gap: 18px;
                    font-size: 0.92rem;
                }

                .cg-nav-action {
                    min-width: 245px;
                }

                .cg-nav-cta {
                    min-width: 126px;
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


def is_placeholder(value):
    return not value or value.strip().lower().startswith("your-")


def short_error(exc):
    return str(exc).splitlines()[0][:180]


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
    project_id = get_setting("GOOGLE_CLOUD_PROJECT")
    if firestore is None:
        return {"saved": False, "detail": "google-cloud-firestore is not installed."}
    if is_placeholder(project_id):
        return {"saved": False, "detail": "GOOGLE_CLOUD_PROJECT is not configured."}

    try:
        db = firestore.Client(project=project_id)
        db.collection(collection).add(payload)
        return {"saved": True, "detail": f"Saved to Firestore collection {collection}."}
    except Exception as exc:
        return {"saved": False, "detail": f"Firestore error: {short_error(exc)}"}


def save_to_cloud_storage(blob_name, payload):
    bucket_name = get_setting("CYBERGUARD_BUCKET")
    project_id = get_setting("GOOGLE_CLOUD_PROJECT")
    if storage is None:
        return {"saved": False, "detail": "google-cloud-storage is not installed."}
    if is_placeholder(bucket_name):
        return {"saved": False, "detail": "CYBERGUARD_BUCKET is not configured."}

    try:
        client = storage.Client(project=None if is_placeholder(project_id) else project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(payload, indent=2), content_type="application/json")
        return {"saved": True, "detail": f"Saved to gs://{bucket_name}/{blob_name}."}
    except Exception as exc:
        return {"saved": False, "detail": f"Cloud Storage error: {short_error(exc)}"}


def persist_result(kind, request_text, result):
    payload = {
        "kind": kind,
        "request": request_text,
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    firestore_status = save_to_firestore("cyberguard_analyses", payload)
    storage_status = save_to_cloud_storage(
        f"cyberguard/{kind}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json",
        payload,
    )
    return {
        "firestore": firestore_status,
        "storage": storage_status,
    }


def render_persist_note(status):
    firestore_icon = "Saved" if status["firestore"]["saved"] else "Not saved"
    storage_icon = "Saved" if status["storage"]["saved"] else "Not saved"
    st.markdown(
        f"""
        <p class='cg-save-note'>
            Firestore: {firestore_icon} - {escape_html(status["firestore"]["detail"])}<br>
            Cloud Storage: {storage_icon} - {escape_html(status["storage"]["detail"])}
        </p>
        """,
        unsafe_allow_html=True,
    )


def cloud_status_items():
    project_id = get_setting("GOOGLE_CLOUD_PROJECT")
    bucket_name = get_setting("CYBERGUARD_BUCKET")
    gemini_key = get_setting("GEMINI_API_KEY")

    return [
        {
            "name": "Gemini API",
            "ready": bool(gemini_key) and genai is not None,
            "detail": "GEMINI_API_KEY is configured." if gemini_key else "Add GEMINI_API_KEY for live analysis.",
        },
        {
            "name": "Firestore",
            "ready": firestore is not None and not is_placeholder(project_id),
            "detail": f"Project: {project_id}" if not is_placeholder(project_id) else "Set GOOGLE_CLOUD_PROJECT.",
        },
        {
            "name": "Cloud Storage",
            "ready": storage is not None and not is_placeholder(bucket_name),
            "detail": f"Bucket: {bucket_name}" if not is_placeholder(bucket_name) else "Set CYBERGUARD_BUCKET.",
        },
        {
            "name": "Cloud Run",
            "ready": not is_placeholder(project_id),
            "detail": "Dockerfile is ready for Cloud Run deployment.",
        },
    ]


def render_status_badge(label):
    st.markdown(status_badge_html(label), unsafe_allow_html=True)


def status_badge_html(label):
    color = RISK_COLORS.get(label, "#334155")
    return f"<span class='cg-badge' style='background:{color}'>{escape_html(label)}</span>"


def status_pill_html(label):
    pill_class = "critical-pill" if label == "Critical" else "risk-pill"
    if label not in ("High", "Critical"):
        color = RISK_COLORS.get(label, "#334155")
        return f"<div class='{pill_class}' style='background:{color}'>{escape_html(label)}</div>"
    return f"<div class='{pill_class}'>{escape_html(label)}</div>"


def render_header():
    mode = "Gemini API" if has_gemini() else "Demo mode"
    st.markdown(
        f"""
        <nav class="cg-nav">
            <div class="cg-brand">
                <span class="cg-brand-mark">C</span>
                <span>CyberGuard AI</span>
            </div>
            <div class="cg-nav-links">
                <span>Summarize</span>
                <span>Debug</span>
                <span>Cloud</span>
                <span>Security</span>
            </div>
            <div class="cg-nav-action">
                <span class="cg-nav-cta">Launch App</span>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )

    st.radio(
        "Theme",
        ["Light", "Dark"],
        horizontal=True,
        key="cyberguard_theme",
        label_visibility="collapsed",
    )

    st.markdown(
        f"""
        <section class="cg-hero">
            <div class="cg-kicker">Version 1.1 is available now</div>
            <h1>Unlock Security Insights with AI</h1>
            <p>
                CyberGuard AI helps you summarize suspicious logs, inspect phishing messages,
                and debug vulnerable code from one focused cybersecurity workspace.
            </p>
            <div class="cg-hero-actions">
                <span class="cg-hero-button">Start Analysis</span>
                <span class="cg-hero-secondary">Gemini-powered triage</span>
            </div>
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
        <div class="glass-card">
            <h3>Security Log / Email Summarizer</h3>
            <p class="muted-text">
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
        height=150,
    )

    if st.button("Analyze Security Text"):
        result = summarize_security_text(security_text)
        persist = persist_result("summary", security_text, result)

        left, right = st.columns([2, 1])
        with left:
            actions = "".join(
                f'<div class="action-item">{escape_html(action)}</div>'
                for action in result["recommended_actions"]
            )
            st.markdown(
                f"""
                <div class="result-card">
                    <h3>Security Summary</h3>
                    <p>{escape_html(result["summary"])}</p>

                    <h3>Recommended Actions</h3>
                    {actions}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                f"""
                <div class="result-card">
                    <h3>Risk Level</h3>
                    {status_pill_html(result["risk_level"])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_persist_note(persist)


def render_code_debugger_tab():
    st.markdown(
        """
        <div class="glass-card">
            <h3>Secure Code Debugger</h3>
            <p class="muted-text">
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
        height=170,
    )

    if st.button("Debug Code Security"):
        result = debug_secure_code(code_text)
        persist = persist_result("code-debug", code_text, result)

        left, right = st.columns([2, 1])
        with left:
            st.markdown(
                f"""
                <div class="result-card">
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
                <div class="result-card">
                    <h3>Severity</h3>
                    {status_pill_html(result["severity"])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_persist_note(persist)


def render_cloud_tab():
    st.markdown(
        """
        <div class="glass-card">
            <h3>Google Cloud Integration</h3>
            <p class="muted-text">
                Check Gemini, Firestore, Cloud Storage, and Cloud Run configuration from
                the same workspace where analysis results are created.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for col, item in zip(cols, cloud_status_items()):
        state = "Ready" if item["ready"] else "Needs setup"
        color = "#0f8a5f" if item["ready"] else "#b7791f"
        with col:
            st.markdown(
                f"""
                <div class="result-card">
                    <h3>{escape_html(item["name"])}</h3>
                    <p><span class="cg-badge" style="background:{color}; min-width: 0; padding: 8px 14px;">{state}</span></p>
                    <p>{escape_html(item["detail"])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="cg-panel">
            <h3 class="cg-section-title">Required configuration</h3>
            <p class="cg-section-copy">Use environment variables locally, Streamlit secrets, or Cloud Run environment variables.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        """GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_CLOUD_PROJECT=your-project-id
CYBERGUARD_BUCKET=your-cloud-storage-bucket""",
        language="bash",
    )

    if st.button("Test Google Cloud Save"):
        test_result = {
            "summary": "Google Cloud integration test",
            "risk_level": "Low",
            "recommended_actions": ["Confirm Firestore document", "Confirm Cloud Storage JSON file"],
        }
        status = persist_result("cloud-test", "Manual Google Cloud integration test", test_result)
        render_persist_note(status)


def main():
    configure_page()
    render_header()

    tab_summary, tab_code, tab_cloud = st.tabs(
        ["Security Log / Email Summarizer", "Secure Code Debugger", "Google Cloud"]
    )
    with tab_summary:
        render_summarizer_tab()
    with tab_code:
        render_code_debugger_tab()
    with tab_cloud:
        render_cloud_tab()

    with st.expander("Google Cloud Architecture"):
        st.write("Streamlit UI -> Gemini API -> Firestore / Cloud Storage -> Cloud Run deployment")


if __name__ == "__main__":
    main()
