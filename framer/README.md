# CyberGuard AI Framer UI

This folder contains a Framer code component version of the CyberGuard AI UI.

## Use In Framer

1. Open your Framer project.
2. Go to `Assets` -> `Code` -> `New Code File`.
3. Name it `CyberGuardAI.tsx`.
4. Paste the contents of `framer/CyberGuardAI.tsx`.
5. Drag the `CyberGuardAI` component onto your page.
6. Set the component width to fill the page or a large desktop frame.

## Demo Mode

The component works without a backend. If `API Endpoint` is empty, it uses the same local demo logic as the Streamlit app.

## API Mode

This repo includes a local API backend in `api.py`.

Run it from the project root:

```powershell
python -m uvicorn api:api --host 127.0.0.1 --port 8000
```

Then set the Framer component's `API Endpoint` property to:

```text
http://127.0.0.1:8000
```

The backend exposes these routes:

```text
POST /summarize
POST /debug-code
```

Both routes should accept:

```json
{ "text": "user input here" }
```

`/summarize` should return:

```json
{
  "summary": "Possible brute-force attack.",
  "risk_level": "High",
  "recommended_actions": ["Block suspicious IP", "Enable MFA"]
}
```

`/debug-code` should return:

```json
{
  "vulnerability": "SQL Injection",
  "severity": "Critical",
  "problem": "User input is directly added to a SQL query string.",
  "secure_fix": "Use parameterized queries.",
  "fixed_code": "cursor.execute(...)"
}
```

Then paste your deployed backend URL into the Framer component's `API Endpoint` property.

For a published Framer site, `http://127.0.0.1:8000` will not work for visitors. Deploy `api.py` to Cloud Run, Render, Railway, or another public host, then use that public HTTPS URL as the `API Endpoint`.
