import json
import os
import re
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
        page_icon="security",
        layout="wide",
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
    color = {
        "Low": "#15803d",
        "Medium": "#ca8a04",
        "High": "#dc2626",
        "Critical": "#991b1b",
    }.get(label, "#334155")
    st.markdown(
        f"<span style='background:{color};color:white;padding:0.35rem 0.6rem;border-radius:0.4rem;font-weight:700'>{label}</span>",
        unsafe_allow_html=True,
    )


def render_header():
    st.title("CyberGuard AI")
    st.caption("A Gemini-based cybersecurity assistant for summarization and secure code debugging.")

    mode = "Gemini API" if has_gemini() else "Demo mode"
    st.info(
        f"Current model mode: {mode}. Add `GEMINI_API_KEY` to use live Gemini analysis."
    )


def render_summarizer_tab():
    st.subheader("Security Log / Email Summarizer")
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
            st.markdown(f"**Summary:** {result['summary']}")
            st.markdown("**Recommended Actions:**")
            for action in result["recommended_actions"]:
                st.write(f"- {action}")
        with right:
            st.markdown("**Risk Level**")
            render_status_badge(result["risk_level"])

        st.caption(f"Saved to Firestore: {persist[0]} | Saved to Cloud Storage: {persist[1]}")


def render_code_debugger_tab():
    st.subheader("Secure Code Debugger")
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
            st.markdown(f"**Vulnerability:** {result['vulnerability']}")
            st.markdown(f"**Problem:** {result['problem']}")
            st.markdown(f"**Secure Fix:** {result['secure_fix']}")
            st.code(result["fixed_code"], language="python")
        with right:
            st.markdown("**Severity**")
            render_status_badge(result["severity"])

        st.caption(f"Saved to Firestore: {persist[0]} | Saved to Cloud Storage: {persist[1]}")


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
