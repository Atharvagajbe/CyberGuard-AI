import * as React from "react"
import { addPropertyControls, ControlType } from "framer"

type ThemeName = "light" | "dark"
type TabName = "summary" | "code"

type SummaryResult = {
    summary: string
    risk_level: "Low" | "Medium" | "High" | "Critical" | string
    recommended_actions: string[]
}

type CodeResult = {
    vulnerability: string
    severity: "Low" | "Medium" | "High" | "Critical" | string
    problem: string
    secure_fix: string
    fixed_code: string
}

type Props = {
    apiEndpoint?: string
    defaultTheme: ThemeName
}

const DEFAULT_LOG_INPUT = `Multiple failed SSH login attempts detected from unknown IP.
User root login failed 15 times.
Port scanning activity found.`

const DEFAULT_CODE_INPUT = `query = "SELECT * FROM users WHERE username = '" + username + "'"`

const palette = {
    light: {
        app: "#eef6f9",
        panel: "#ffffff",
        panelSoft: "#f7fafc",
        text: "#102033",
        muted: "#53677f",
        line: "#ccd9e6",
        input: "#ffffff",
        heroA: "#102033",
        heroB: "#155e75",
        accent: "#0f96a6",
        accentStrong: "#0f7280",
        shadow: "0 18px 50px rgba(40, 64, 88, 0.12)",
    },
    dark: {
        app: "#0b1320",
        panel: "#111e30",
        panelSoft: "#15243a",
        text: "#edf6ff",
        muted: "#a8b7ca",
        line: "#284057",
        input: "#0c1727",
        heroA: "#08111f",
        heroB: "#12495a",
        accent: "#2dd4bf",
        accentStrong: "#5eead4",
        shadow: "0 18px 50px rgba(0, 0, 0, 0.28)",
    },
}

const severityColors: Record<string, string> = {
    Low: "#0f8a5f",
    Medium: "#b7791f",
    High: "#d13f32",
    Critical: "#8f1d2c",
}

function summarizeDemo(text: string): SummaryResult {
    const lowered = text.toLowerCase()

    if (lowered.includes("failed") && (lowered.includes("ssh") || lowered.includes("login"))) {
        return {
            summary: "Possible brute-force attack.",
            risk_level: "High",
            recommended_actions: [
                "Block suspicious IP",
                "Disable root SSH login",
                "Enable MFA",
                "Check server logs",
            ],
        }
    }

    if (lowered.includes("phishing") || lowered.includes("password") || lowered.includes("urgent")) {
        return {
            summary: "Possible phishing attempt.",
            risk_level: "High",
            recommended_actions: [
                "Do not click links",
                "Report the email",
                "Reset exposed credentials",
                "Scan related inboxes",
            ],
        }
    }

    if (lowered.includes("port scan") || lowered.includes("scanning")) {
        return {
            summary: "Possible reconnaissance activity.",
            risk_level: "Medium",
            recommended_actions: ["Block scanner IP", "Review firewall rules", "Inspect exposed services"],
        }
    }

    return {
        summary: "Suspicious security activity requires investigation.",
        risk_level: "Medium",
        recommended_actions: ["Check server logs", "Review affected accounts"],
    }
}

function debugCodeDemo(text: string): CodeResult {
    const lowered = text.toLowerCase()

    if (lowered.includes("select") && text.includes("+")) {
        return {
            vulnerability: "SQL Injection",
            severity: "Critical",
            problem: "User input is directly added to a SQL query string.",
            secure_fix: "Use parameterized queries so user input is treated as data, not executable SQL.",
            fixed_code: `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))`,
        }
    }

    if (lowered.includes("password") && (text.includes("=") || text.includes(":"))) {
        return {
            vulnerability: "Hardcoded Secret",
            severity: "High",
            problem: "Sensitive credentials appear to be stored directly in source code.",
            secure_fix: "Move secrets to a secret manager or environment variable and rotate exposed values.",
            fixed_code: `password = os.environ["DATABASE_PASSWORD"]`,
        }
    }

    return {
        vulnerability: "Security Review Needed",
        severity: "Medium",
        problem: "The snippet may need deeper review for input validation, authentication, or data exposure issues.",
        secure_fix: "Validate inputs, use safe libraries, and avoid manual construction of sensitive operations.",
        fixed_code: text,
    }
}

async function callApi<T>(apiEndpoint: string | undefined, path: string, text: string, fallback: () => T) {
    if (!apiEndpoint) return fallback()

    try {
        const response = await fetch(`${apiEndpoint.replace(/\/$/, "")}/${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        })

        if (!response.ok) throw new Error(`Request failed with ${response.status}`)
        return (await response.json()) as T
    } catch {
        return fallback()
    }
}

export default function CyberGuardAI(props: Props) {
    const { apiEndpoint, defaultTheme = "light" } = props
    const [themeName, setThemeName] = React.useState<ThemeName>(defaultTheme)
    const [activeTab, setActiveTab] = React.useState<TabName>("summary")
    const [securityText, setSecurityText] = React.useState(DEFAULT_LOG_INPUT)
    const [codeText, setCodeText] = React.useState(DEFAULT_CODE_INPUT)
    const [summaryResult, setSummaryResult] = React.useState<SummaryResult | null>(null)
    const [codeResult, setCodeResult] = React.useState<CodeResult | null>(null)
    const [loading, setLoading] = React.useState(false)
    const theme = palette[themeName]

    async function analyzeSummary() {
        setLoading(true)
        const result = await callApi<SummaryResult>(
            apiEndpoint,
            "summarize",
            securityText,
            () => summarizeDemo(securityText)
        )
        setSummaryResult(result)
        setLoading(false)
    }

    async function analyzeCode() {
        setLoading(true)
        const result = await callApi<CodeResult>(
            apiEndpoint,
            "debug-code",
            codeText,
            () => debugCodeDemo(codeText)
        )
        setCodeResult(result)
        setLoading(false)
    }

    const styles = makeStyles(theme)

    return (
        <main style={styles.shell}>
            <section style={styles.hero}>
                <div style={styles.heroBadge}>Cybersecurity triage assistant</div>
                <h1 style={styles.title}>CyberGuard AI</h1>
                <p style={styles.heroText}>
                    Analyze suspicious logs, phishing messages, and risky code with a focused
                    Gemini-powered workflow built for fast security review.
                </p>
            </section>

            <div style={styles.toolbar}>
                <div>
                    Current model mode: <strong>{apiEndpoint ? "API connected" : "Demo mode"}</strong>
                </div>
                <div style={styles.segment}>
                    <button
                        type="button"
                        style={themeButton(themeName === "light", theme)}
                        onClick={() => setThemeName("light")}
                    >
                        Light
                    </button>
                    <button
                        type="button"
                        style={themeButton(themeName === "dark", theme)}
                        onClick={() => setThemeName("dark")}
                    >
                        Dark
                    </button>
                </div>
            </div>

            <nav style={styles.tabs}>
                <button
                    type="button"
                    style={tabButton(activeTab === "summary", theme)}
                    onClick={() => setActiveTab("summary")}
                >
                    Security Log / Email Summarizer
                </button>
                <button
                    type="button"
                    style={tabButton(activeTab === "code", theme)}
                    onClick={() => setActiveTab("code")}
                >
                    Secure Code Debugger
                </button>
            </nav>

            {activeTab === "summary" ? (
                <section>
                    <InfoPanel
                        title="Security Log / Email Summarizer"
                        text="Paste a suspicious event, phishing message, or incident note to get a concise triage summary and action list."
                        theme={theme}
                    />
                    <label style={styles.label}>Paste security logs, phishing emails, or incident reports</label>
                    <textarea
                        value={securityText}
                        onChange={(event) => setSecurityText(event.target.value)}
                        style={styles.textarea}
                    />
                    <button type="button" style={styles.primaryButton} onClick={analyzeSummary}>
                        {loading ? "Analyzing..." : "Analyze Security Text"}
                    </button>
                    {summaryResult && (
                        <div style={styles.resultGrid}>
                            <article style={styles.card}>
                                <h3 style={styles.cardTitle}>Security Summary</h3>
                                <p style={styles.bodyText}>{summaryResult.summary}</p>
                                <h3 style={styles.cardTitle}>Recommended Actions</h3>
                                <div style={styles.actionList}>
                                    {summaryResult.recommended_actions.map((action) => (
                                        <div key={action} style={styles.actionItem}>
                                            {action}
                                        </div>
                                    ))}
                                </div>
                            </article>
                            <article style={styles.card}>
                                <h3 style={styles.cardTitle}>Risk Level</h3>
                                <Badge label={summaryResult.risk_level} />
                            </article>
                        </div>
                    )}
                </section>
            ) : (
                <section>
                    <InfoPanel
                        title="Secure Code Debugger"
                        text="Drop in a snippet to identify the biggest security issue, understand the risk, and generate a safer replacement pattern."
                        theme={theme}
                    />
                    <label style={styles.label}>Paste insecure or suspicious code</label>
                    <textarea
                        value={codeText}
                        onChange={(event) => setCodeText(event.target.value)}
                        style={styles.textarea}
                    />
                    <button type="button" style={styles.primaryButton} onClick={analyzeCode}>
                        {loading ? "Debugging..." : "Debug Code Security"}
                    </button>
                    {codeResult && (
                        <div style={styles.resultGrid}>
                            <article style={styles.card}>
                                <h3 style={styles.cardTitle}>Vulnerability</h3>
                                <p style={styles.bodyText}>{codeResult.vulnerability}</p>
                                <h3 style={styles.cardTitle}>Problem</h3>
                                <p style={styles.bodyText}>{codeResult.problem}</p>
                                <h3 style={styles.cardTitle}>Secure Fix</h3>
                                <p style={styles.bodyText}>{codeResult.secure_fix}</p>
                                <pre style={styles.codeBlock}>{codeResult.fixed_code}</pre>
                            </article>
                            <article style={styles.card}>
                                <h3 style={styles.cardTitle}>Severity</h3>
                                <Badge label={codeResult.severity} />
                            </article>
                        </div>
                    )}
                </section>
            )}
        </main>
    )
}

function InfoPanel({
    title,
    text,
    theme,
}: {
    title: string
    text: string
    theme: typeof palette.light
}) {
    return (
        <div
            style={{
                border: `1px solid ${theme.line}`,
                borderRadius: 12,
                background: theme.panel,
                boxShadow: theme.shadow,
                padding: 18,
                marginBottom: 22,
            }}
        >
            <h2 style={{ color: theme.text, fontSize: 20, margin: "0 0 8px" }}>{title}</h2>
            <p style={{ color: theme.muted, margin: 0, lineHeight: 1.55 }}>{text}</p>
        </div>
    )
}

function Badge({ label }: { label: string }) {
    return (
        <span
            style={{
                display: "inline-flex",
                justifyContent: "center",
                minWidth: 112,
                borderRadius: 999,
                background: severityColors[label] || "#334155",
                color: "#ffffff",
                fontWeight: 800,
                padding: "12px 18px",
            }}
        >
            {label}
        </span>
    )
}

function makeStyles(theme: typeof palette.light): Record<string, React.CSSProperties> {
    return {
        shell: {
            width: "100%",
            minHeight: "100%",
            padding: "clamp(18px, 4vw, 32px)",
            background: theme.app,
            color: theme.text,
            fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            boxSizing: "border-box",
        },
        hero: {
            border: `1px solid ${theme.line}`,
            borderRadius: 14,
            padding: 34,
            background: `linear-gradient(135deg, ${theme.heroA}, ${theme.heroB})`,
            boxShadow: theme.shadow,
            marginBottom: 22,
        },
        heroBadge: {
            display: "inline-flex",
            border: "1px solid rgba(255,255,255,0.28)",
            borderRadius: 999,
            color: "rgba(255,255,255,0.88)",
            padding: "8px 12px",
            marginBottom: 28,
            fontSize: 12,
            fontWeight: 800,
            textTransform: "uppercase",
        },
        title: {
            color: "#ffffff",
            fontSize: "clamp(34px, 8vw, 54px)",
            lineHeight: 1,
            margin: "0 0 20px",
            letterSpacing: 0,
        },
        heroText: {
            maxWidth: 760,
            color: "rgba(255,255,255,0.86)",
            fontSize: 17,
            lineHeight: 1.6,
            margin: 0,
        },
        toolbar: {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 16,
            border: `1px solid ${theme.line}`,
            borderRadius: 12,
            background: theme.panel,
            color: theme.text,
            padding: "12px 16px",
            marginBottom: 24,
            boxShadow: theme.shadow,
        },
        segment: {
            display: "flex",
            gap: 6,
            padding: 4,
            borderRadius: 10,
            border: `1px solid ${theme.line}`,
            background: theme.panelSoft,
        },
        tabs: {
            display: "flex",
            gap: 8,
            borderBottom: `1px solid ${theme.line}`,
            marginBottom: 28,
            overflowX: "auto",
        },
        label: {
            display: "block",
            color: theme.text,
            fontWeight: 700,
            marginBottom: 10,
        },
        textarea: {
            width: "100%",
            minHeight: 190,
            resize: "vertical",
            boxSizing: "border-box",
            border: `1px solid ${theme.line}`,
            borderRadius: 12,
            background: theme.input,
            color: theme.text,
            padding: 16,
            fontSize: 15,
            lineHeight: 1.55,
            outline: "none",
        },
        primaryButton: {
            marginTop: 16,
            marginBottom: 18,
            border: 0,
            borderRadius: 10,
            background: `linear-gradient(135deg, ${theme.accentStrong}, ${theme.accent})`,
            color: "#ffffff",
            padding: "14px 18px",
            fontWeight: 800,
            fontSize: 15,
            cursor: "pointer",
            boxShadow: "0 10px 20px rgba(18, 168, 180, 0.2)",
        },
        resultGrid: {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 20,
        },
        card: {
            border: `1px solid ${theme.line}`,
            borderRadius: 12,
            background: theme.panel,
            boxShadow: theme.shadow,
            padding: 22,
        },
        cardTitle: {
            color: theme.text,
            fontSize: 18,
            margin: "0 0 14px",
        },
        bodyText: {
            color: theme.text,
            fontSize: 16,
            lineHeight: 1.6,
            margin: "0 0 22px",
        },
        actionList: {
            display: "grid",
            gap: 10,
        },
        actionItem: {
            border: `1px solid ${theme.line}`,
            borderRadius: 10,
            background: theme.panelSoft,
            color: theme.text,
            padding: "13px 14px",
        },
        codeBlock: {
            whiteSpace: "pre-wrap",
            border: `1px solid ${theme.line}`,
            borderRadius: 10,
            background: theme.panelSoft,
            color: theme.text,
            padding: 14,
            fontSize: 14,
            overflowX: "auto",
        },
    }
}

function themeButton(active: boolean, theme: typeof palette.light): React.CSSProperties {
    return {
        border: 0,
        borderRadius: 8,
        background: active ? theme.accent : "transparent",
        color: active ? "#ffffff" : theme.text,
        padding: "8px 12px",
        fontWeight: 800,
        cursor: "pointer",
    }
}

function tabButton(active: boolean, theme: typeof palette.light): React.CSSProperties {
    return {
        border: 0,
        borderBottom: active ? `3px solid ${theme.accent}` : "3px solid transparent",
        background: "transparent",
        color: active ? theme.accentStrong : theme.text,
        padding: "12px 10px",
        fontWeight: 800,
        cursor: "pointer",
        whiteSpace: "nowrap",
    }
}

addPropertyControls(CyberGuardAI, {
    apiEndpoint: {
        title: "API Endpoint",
        type: ControlType.String,
        defaultValue: "",
        placeholder: "https://your-api.example.com",
    },
    defaultTheme: {
        title: "Theme",
        type: ControlType.Enum,
        options: ["light", "dark"],
        optionTitles: ["Light", "Dark"],
        defaultValue: "light",
    },
})
