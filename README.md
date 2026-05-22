<p align="center">
  <img src="assets/cyberguard-banner.png" alt="CyberGuard AI Banner" width="100%">
</p>

# 🛡️ CyberGuard AI

**CyberGuard AI** is a Gemini-powered cybersecurity assistant built with **Python** and **Streamlit**.  
It demonstrates how Google Gemini can be used for cybersecurity tasks such as summarizing security logs, analyzing phishing emails, reviewing insecure code, and suggesting secure fixes.

---

## 📌 Final Topic

- **Topic:** Topic L - Gemini AI Capabilities
- **Project Name:** CyberGuard AI: Gemini Cybersecurity Assistant

---

## 🚀 Key Features

CyberGuard AI demonstrates two major Gemini capabilities:

### 1. Summarization

CyberGuard AI can summarize cybersecurity-related text such as:

- Security logs
- Phishing emails
- Incident reports
- Suspicious login activity
- Port scanning activity
- Brute-force attack logs

The assistant provides:

- Short security summary
- Risk level
- Recommended actions

---

### 2. Code Generation and Debugging

CyberGuard AI can analyze insecure code snippets and identify common security problems.

It can detect issues such as:

- SQL Injection
- Hardcoded credentials
- Unsafe input handling
- Weak coding patterns
- Security misconfigurations

The assistant also suggests safer coding practices and secure fixes.

---

## 🧪 Demo Features

The application contains two main tabs.

---

## 🔍 Tab 1: Security Log / Email Summarizer

This tab accepts security logs, phishing emails, or incident text and generates a cybersecurity-focused summary.

### Example Input

```text
Multiple failed SSH login attempts detected from unknown IP.
User root login failed 15 times.
Port scanning activity found.
```

### Example Output

```text
Summary: Possible brute-force attack.

Risk Level: High

Recommended Actions:
- Block suspicious IP
- Disable root SSH login
- Enable MFA
- Check server logs
```

---

## 💻 Tab 2: Secure Code Debugger

This tab accepts insecure code snippets and detects possible vulnerabilities.

### Example Input

```python
query = "SELECT * FROM users WHERE username = '" + username + "'"
```

### Example Output

```text
Vulnerability: SQL Injection

Severity: Critical

Problem:
User input is directly added to the SQL query.

Secure Fix:
Use parameterized queries to prevent SQL injection.
```

---

## 🏗️ Google Cloud Architecture

```text
Streamlit UI
     |
     v
Gemini API
     |
     v
Firestore / Cloud Storage
     |
     v
Google Cloud Run Deployment
```

---

## ☁️ Google Cloud Components

| Component | Purpose |
|---|---|
| Streamlit | Web-based user interface |
| Gemini API | Generates summaries, analysis, and secure code suggestions |
| Firestore | Stores structured analysis results |
| Cloud Storage | Stores JSON output files |
| Cloud Run | Deploys and hosts the application |
| Docker | Containerizes the application for cloud deployment |

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | Main programming language |
| Streamlit | Frontend web interface |
| Google Gemini API | AI analysis and response generation |
| Firestore | Optional database persistence |
| Google Cloud Storage | Optional file storage |
| Google Cloud Run | Cloud deployment |
| Docker | Containerized deployment |

---

## 📂 Project Structure

```text
CyberGuard-AI/
│
├── .streamlit/
│   └── secrets.toml
│
├── app.py
├── requirements.txt
├── Dockerfile
├── .gitignore
├── .dockerignore
└── README.md
```

---

## ⚙️ Environment Variables

The app runs in **demo mode** without credentials.

To use live Gemini and Google Cloud persistence, set the following environment variables:

```bash
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_CLOUD_PROJECT=your-project-id
CYBERGUARD_BUCKET=your-cloud-storage-bucket
```

---

## 🔐 Streamlit Secrets Setup

For local Streamlit development, create a file:

```text
.streamlit/secrets.toml
```

Add your configuration:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
GEMINI_MODEL = "gemini-2.0-flash"
GOOGLE_CLOUD_PROJECT = "your-project-id"
CYBERGUARD_BUCKET = "your-cloud-storage-bucket"
```

> Do not commit `.streamlit/secrets.toml` to GitHub.  
> It contains sensitive credentials and should remain ignored by `.gitignore`.

---

## ▶️ Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Atharvagajbe/CyberGuard-AI.git
cd CyberGuard-AI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Application

```bash
streamlit run app.py
```

The app will usually open at:

```text
http://localhost:8501
```

---

## 🧪 Demo Mode

CyberGuard AI can run without a Gemini API key.

If no credentials are configured, the application automatically uses demo mode. This allows users to test the project without setting up Google Cloud or Gemini API credentials.

Demo mode supports sample detection for:

- SSH brute-force activity
- Phishing-like messages
- Port scanning activity
- SQL injection code
- Hardcoded password examples

---

## 🐳 Run with Docker

### Build Docker Image

```bash
docker build -t cyberguard-ai .
```

### Run Docker Container

```bash
docker run -p 8080:8080 cyberguard-ai
```

The app will be available at:

```text
http://localhost:8080
```

---

## ☁️ Deploy to Google Cloud Run

### 1. Login to Google Cloud

```bash
gcloud auth login
```

### 2. Set Your Google Cloud Project

```bash
gcloud config set project your-project-id
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy cyberguard-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-gemini-api-key,GOOGLE_CLOUD_PROJECT=your-project-id,CYBERGUARD_BUCKET=your-cloud-storage-bucket
```

---

## 🔄 Application Workflow

```text
User enters log, email, or code
        |
        v
Streamlit receives input
        |
        v
Prompt is sent to Gemini
        |
        v
Gemini generates structured cybersecurity analysis
        |
        v
Result is displayed in the Streamlit UI
        |
        v
Optional storage in Firestore / Cloud Storage
```

---

## 📊 Example Use Cases

CyberGuard AI can be used for:

- Cybersecurity learning
- AI security demonstrations
- Secure coding practice
- Phishing email analysis
- Security log summarization
- Beginner SOC investigation practice
- Cloud security project demonstration
- Academic Gemini API capability showcase

---

## 🔐 Security Considerations

This project is designed for educational and demonstration purposes.

Important notes:

- Do not upload real confidential logs.
- Do not commit API keys or secrets to GitHub.
- Use environment variables or secret management for credentials.
- Validate AI-generated security advice before applying it.
- AI output should support human analysis, not replace it.
- Always review code fixes manually before using them in production.

---

## 🚧 Future Improvements

Possible future enhancements:

- Add login/authentication
- Add downloadable PDF reports
- Add dashboard for previous analysis history
- Add file upload support for logs
- Add MITRE ATT&CK mapping
- Add OWASP Top 10 classification
- Add severity charts
- Add multilingual support
- Add Google Secret Manager integration
- Add CI/CD pipeline using GitHub Actions

---

## ⭐ Support

If you found this project useful, consider giving it a star on GitHub.

---

## 🏁 Summary

CyberGuard AI is a practical Gemini-based cybersecurity assistant that combines:

- Security log summarization
- Phishing email analysis
- Secure code debugging
- Gemini API integration
- Streamlit web interface
- Optional Google Cloud persistence
- Cloud Run deployment readiness

It is a strong portfolio project for demonstrating AI, cybersecurity, cloud, and secure software development skills.

---

## 📄 License

This project is created for educational and demonstration purposes.

Recommended license for this project:

```text
MIT License
```
