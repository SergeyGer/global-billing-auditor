"""
Global Billing & Invoice Compliance Auditor
-------------------------------------------
Mini-MVP Streamlit app for Remote.com-style fintech vertical demos.

Run:
    streamlit run app.py

Architecture (single-file modules for easy debugging):
  - CONFIG / STYLING ........ theme + constants
  - AUDIT CALCULATOR ........ employer cost / fees / tax simulation
  - AI COMPLIANCE CHECKER ... rule + mock-LLM invoice risk flags
  - AUDIT LOG ............... in-memory sample dashboard data
  - UI PAGES ................ Streamlit tabs wiring it all together
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Literal

import pandas as pd
import streamlit as st

# =============================================================================
# 1) CONFIG & THEME
# =============================================================================

APP_TITLE = "Global Billing & Invoice Compliance Auditor"
APP_TAGLINE = "Remote.com fintech vertical · Mini-MVP"

Country = Literal["Germany", "US", "UK"]
EmployeeType = Literal["Contractor", "Full-time"]
Currency = Literal["USD", "EUR"]

COUNTRIES: list[Country] = ["Germany", "US", "UK"]
EMPLOYEE_TYPES: list[EmployeeType] = ["Contractor", "Full-time"]
CURRENCIES: list[Currency] = ["USD", "EUR"]

# Simulated FX (demo only — not live rates)
USD_TO_EUR = 0.92

# Country compliance / tax simulation knobs (illustrative, not legal advice)
COUNTRY_RULES: dict[str, dict] = {
    "Germany": {
        "compliance_fee_rate": 0.035,  # platform / EOR compliance fee
        "vat_rate": 0.19,  # German VAT
        "employer_social_rate_ft": 0.20,  # approx employer social contributions
        "employer_social_rate_contractor": 0.0,
        "currency_hint": "EUR",
        "notes": "VAT ID (USt-IdNr.) typically required on B2B invoices.",
    },
    "US": {
        "compliance_fee_rate": 0.028,
        "vat_rate": 0.0,  # no federal VAT; sales tax varies — simulated as 0
        "employer_social_rate_ft": 0.0765,  # FICA-like employer share (simplified)
        "employer_social_rate_contractor": 0.0,
        "currency_hint": "USD",
        "notes": "Contractors often need W-8BEN / W-9 on file for tax withholding.",
    },
    "UK": {
        "compliance_fee_rate": 0.030,
        "vat_rate": 0.20,  # UK VAT
        "employer_social_rate_ft": 0.138,  # simplified employer NI
        "employer_social_rate_contractor": 0.0,
        "currency_hint": "GBP (shown in selected currency)",
        "notes": "VAT registration number expected when VAT is charged.",
    },
}

REMOTE_CSS = """
<style>
    /* Remote.com–inspired deep blue theme */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    :root {
        --remote-navy: #0B1F3A;
        --remote-deep: #122B4A;
        --remote-mid: #1A3A5C;
        --remote-accent: #3D8BFF;
        --remote-accent-soft: #5BA3FF;
        --remote-teal: #2DD4BF;
        --remote-text: #E8EEF7;
        --remote-muted: #9AAFC7;
        --remote-danger: #FF6B7A;
        --remote-warn: #F5B942;
        --remote-ok: #3DDC97;
        --remote-border: rgba(61, 139, 255, 0.22);
    }

    .stApp {
        background: linear-gradient(165deg, #071525 0%, #0B1F3A 42%, #122B4A 100%);
        color: var(--remote-text);
        font-family: 'IBM Plex Sans', 'DM Sans', sans-serif;
    }

    /* Hide Streamlit chrome noise */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2 {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--remote-text) !important;
        letter-spacing: -0.02em;
    }

    .hero-brand {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--remote-accent-soft);
        margin-bottom: 0.35rem;
    }

    .hero-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 2.05rem;
        font-weight: 700;
        line-height: 1.15;
        color: #F4F8FF;
        margin: 0 0 0.4rem 0;
    }

    .hero-sub {
        color: var(--remote-muted);
        font-size: 1.02rem;
        max-width: 42rem;
        margin-bottom: 1.25rem;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(26, 58, 92, 0.85), rgba(11, 31, 58, 0.9));
        border: 1px solid var(--remote-border);
        border-radius: 12px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: var(--remote-muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.55rem;
        font-weight: 700;
        color: #F4F8FF;
    }

    .metric-hint {
        color: var(--remote-muted);
        font-size: 0.8rem;
        margin-top: 0.2rem;
    }

    .risk-high {
        background: rgba(255, 107, 122, 0.12);
        border-left: 3px solid var(--remote-danger);
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }

    .risk-medium {
        background: rgba(245, 185, 66, 0.12);
        border-left: 3px solid var(--remote-warn);
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }

    .risk-low {
        background: rgba(61, 220, 151, 0.10);
        border-left: 3px solid var(--remote-ok);
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }

    .risk-title {
        font-weight: 600;
        color: #F4F8FF;
        margin-bottom: 0.15rem;
    }

    .risk-body {
        color: var(--remote-muted);
        font-size: 0.92rem;
    }

    .pill {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-right: 0.35rem;
    }

    .pill-high { background: rgba(255,107,122,0.2); color: #FF8A96; }
    .pill-medium { background: rgba(245,185,66,0.2); color: #F5C86A; }
    .pill-low { background: rgba(61,220,151,0.18); color: #6EE7B7; }
    .pill-info { background: rgba(61,139,255,0.2); color: #8BB8FF; }

    .disclaimer {
        color: var(--remote-muted);
        font-size: 0.78rem;
        border-top: 1px solid var(--remote-border);
        padding-top: 0.75rem;
        margin-top: 1.5rem;
    }

    /* Inputs */
    div[data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #0A1A2E !important;
        color: #E8EEF7 !important;
        border-color: rgba(61, 139, 255, 0.35) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid rgba(61, 139, 255, 0.2);
    }

    .stTabs [data-baseweb="tab"] {
        color: #9AAFC7;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        color: #5BA3FF !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071525 0%, #0B1F3A 100%);
        border-right: 1px solid rgba(61, 139, 255, 0.15);
    }

    .stButton > button {
        background: linear-gradient(135deg, #3D8BFF, #2563EB);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.45rem 1.1rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #5BA3FF, #3D8BFF);
        color: white;
        border: none;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(61, 139, 255, 0.2);
        border-radius: 10px;
        overflow: hidden;
    }
</style>
"""


# =============================================================================
# 2) FEATURE 1 — Invoice Audit Calculator
# =============================================================================

@dataclass
class AuditBreakdown:
    """Structured result of a simulated employer-cost audit."""

    country: str
    employee_type: str
    invoice_amount: float
    currency: str
    amount_usd: float
    compliance_fee: float
    employer_social: float
    tax_vat: float
    total_employer_cost: float
    effective_load_pct: float
    notes: str

    def to_display_dict(self) -> dict:
        """Flat dict for Streamlit metrics / CSV export."""
        return asdict(self)


def to_usd(amount: float, currency: Currency) -> float:
    """Convert invoice amount to USD for apples-to-apples totals."""
    if currency == "USD":
        return amount
    # EUR → USD using demo FX
    return amount / USD_TO_EUR


def from_usd(amount_usd: float, currency: Currency) -> float:
    """Convert a USD figure back into the user's selected display currency."""
    if currency == "USD":
        return amount_usd
    return amount_usd * USD_TO_EUR


def calculate_audit(
    country: Country,
    invoice_amount: float,
    currency: Currency,
    employee_type: EmployeeType,
) -> AuditBreakdown:
    """
    Simulate employer cost for an invoice.

    Formula (demo):
        base_usd            = convert(invoice)
        compliance_fee      = base_usd * country.compliance_fee_rate
        employer_social     = base_usd * social_rate (FT only)
        tax_vat             = base_usd * vat_rate   (shown as recoverable estimate)
        total_employer_cost = base_usd + compliance_fee + employer_social
                              (+ tax_vat for display of gross outflow)
    """
    if invoice_amount < 0:
        raise ValueError("Invoice amount must be >= 0")

    rules = COUNTRY_RULES[country]
    base_usd = to_usd(invoice_amount, currency)

    social_rate = (
        rules["employer_social_rate_ft"]
        if employee_type == "Full-time"
        else rules["employer_social_rate_contractor"]
    )

    compliance_fee_usd = base_usd * rules["compliance_fee_rate"]
    employer_social_usd = base_usd * social_rate
    tax_vat_usd = base_usd * rules["vat_rate"]

    # Employer "all-in" cost: base + platform compliance + social.
    # VAT is tracked separately (often reclaimable for B2B).
    total_usd = base_usd + compliance_fee_usd + employer_social_usd
    load_pct = ((total_usd - base_usd) / base_usd * 100) if base_usd else 0.0

    # Present figures in the user's chosen currency
    return AuditBreakdown(
        country=country,
        employee_type=employee_type,
        invoice_amount=invoice_amount,
        currency=currency,
        amount_usd=round(base_usd, 2),
        compliance_fee=round(from_usd(compliance_fee_usd, currency), 2),
        employer_social=round(from_usd(employer_social_usd, currency), 2),
        tax_vat=round(from_usd(tax_vat_usd, currency), 2),
        total_employer_cost=round(from_usd(total_usd, currency), 2),
        effective_load_pct=round(load_pct, 2),
        notes=rules["notes"],
    )


def render_metric_card(label: str, value: str, hint: str = "") -> None:
    """Small HTML metric tile matching the Remote theme."""
    hint_html = f'<div class="metric-hint">{hint}</div>' if hint else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(amount: float, currency: str) -> str:
    """Format currency for UI."""
    symbol = {"USD": "$", "EUR": "€"}.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


# =============================================================================
# 3) FEATURE 2 — AI Invoice Compliance Checker (mock LLM + rules)
# =============================================================================

@dataclass
class ComplianceFinding:
    severity: Literal["high", "medium", "low"]
    code: str
    title: str
    detail: str


def _detect_country_hints(text: str) -> set[str]:
    """Infer likely jurisdiction(s) from invoice text heuristics."""
    t = text.lower()
    found: set[str] = set()
    if any(k in t for k in ("germany", "deutschland", "berlin", "gmbh", "ust-id", "ust id", "mwst", "ust-idnr")):
        found.add("Germany")
    if any(k in t for k in ("united states", "usa", "u.s.", "california", "delaware", "irs", "w-8", "w-9", "ein")):
        found.add("US")
    if any(k in t for k in ("united kingdom", "london", "england", "hmrc", "vat reg", "ltd", "plc")):
        found.add("UK")
    return found


def _has_vat_id(text: str) -> bool:
    """Rough VAT / tax-ID pattern match (DE / EU / UK style)."""
    patterns = [
        r"\bDE\s?\d{9}\b",  # German VAT
        r"\bGB\s?\d{9}\b",  # UK VAT
        r"\bVAT[:\s#]*[A-Z]{0,2}\s?\d{8,12}\b",
        r"\bUSt[- ]?Id(?:Nr)?\.?\s*[:\s]*[A-Z0-9]+",
        r"\bVAT\s+(?:number|no\.?|reg\.?)\b",
    ]
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _has_w8_or_w9(text: str) -> bool:
    return bool(re.search(r"\bW-?8BEN\b|\bW-?9\b", text, flags=re.IGNORECASE))


def _has_invoice_number(text: str) -> bool:
    return bool(re.search(r"\binvoice\s*(?:number|no\.?|#)\b|\bINV[-_]?\d+", text, flags=re.IGNORECASE))


def _has_dates(text: str) -> bool:
    return bool(
        re.search(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}",
            text,
            flags=re.IGNORECASE,
        )
    )


def _has_bank_details(text: str) -> bool:
    return bool(re.search(r"\bIBAN\b|\bSWIFT\b|\bBIC\b|\brouting\s*(?:number|no\.?)\b|\baccount\s*(?:number|no\.?)\b", text, flags=re.IGNORECASE))


def mock_llm_narrative(findings: list[ComplianceFinding], text_len: int) -> str:
    """
    Mock LLM summary — deterministic so demos are reproducible.
    Swap this function for a real OpenAI/Anthropic call later if needed.
    """
    if not findings:
        return (
            "Mock LLM review: Invoice structure looks complete for a demo audit. "
            "No high-severity structural gaps detected. Recommend human review before payment."
        )

    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    digest = hashlib.sha256(str(sorted(f.code for f in findings)).encode()).hexdigest()[:8]

    return (
        f"Mock LLM review [{digest}]: Analyzed {text_len} characters of invoice text. "
        f"Flagged {high} high and {medium} medium structural risk(s). "
        "Priority: remediate tax-form and jurisdiction identifiers before routing for payment. "
        "(This is a simulated model response — not legal or tax advice.)"
    )


def check_invoice_compliance(
    invoice_text: str,
    assumed_country: Country | None = None,
    employee_type: EmployeeType = "Contractor",
) -> tuple[list[ComplianceFinding], str]:
    """
    Rule-based compliance checker with a mock LLM narrative.

    Returns:
        (findings, mock_llm_summary)
    """
    text = (invoice_text or "").strip()
    findings: list[ComplianceFinding] = []

    if len(text) < 40:
        findings.append(
            ComplianceFinding(
                severity="high",
                code="EMPTY_OR_SHORT",
                title="Invoice text too short",
                detail="Paste a fuller invoice (vendor, amount, tax IDs, dates) for a meaningful audit.",
            )
        )
        return findings, mock_llm_narrative(findings, len(text))

    countries = _detect_country_hints(text)
    if assumed_country:
        countries.add(assumed_country)

    # Structural baseline checks
    if not _has_invoice_number(text):
        findings.append(
            ComplianceFinding(
                severity="medium",
                code="MISSING_INVOICE_NUMBER",
                title="Missing invoice number",
                detail="No clear invoice number / INV- reference found. AP systems usually require a unique ID.",
            )
        )

    if not _has_dates(text):
        findings.append(
            ComplianceFinding(
                severity="medium",
                code="MISSING_DATE",
                title="Missing invoice / service date",
                detail="Could not detect an invoice or service period date.",
            )
        )

    if not _has_bank_details(text):
        findings.append(
            ComplianceFinding(
                severity="low",
                code="MISSING_PAYMENT_RAILS",
                title="Payment details unclear",
                detail="No IBAN/SWIFT/routing cues found. Confirm how funds should be remitted.",
            )
        )

    # Country-specific risks
    if "Germany" in countries or assumed_country == "Germany":
        if not _has_vat_id(text):
            findings.append(
                ComplianceFinding(
                    severity="high",
                    code="DE_MISSING_VAT",
                    title="Germany: missing VAT number (USt-IdNr.)",
                    detail="German B2B invoices typically require a VAT ID. Flagged as a structural compliance gap.",
                )
            )

    if "UK" in countries or assumed_country == "UK":
        if not _has_vat_id(text) and re.search(r"\bVAT\b|\b20%\b", text, flags=re.IGNORECASE):
            findings.append(
                ComplianceFinding(
                    severity="high",
                    code="UK_MISSING_VAT_REG",
                    title="UK: VAT charged but registration number unclear",
                    detail="VAT appears referenced without a clear GB VAT registration number.",
                )
            )
        elif not _has_vat_id(text):
            findings.append(
                ComplianceFinding(
                    severity="medium",
                    code="UK_VAT_ID_CHECK",
                    title="UK: VAT registration not detected",
                    detail="Confirm whether the supplier is VAT-registered and if reverse charge applies.",
                )
            )

    if "US" in countries or assumed_country == "US":
        if employee_type == "Contractor" and not _has_w8_or_w9(text):
            findings.append(
                ComplianceFinding(
                    severity="high",
                    code="US_MISSING_W8BEN",
                    title="US contractor: missing W-8BEN / W-9 hint",
                    detail="For US-related contractor payouts, tax forms (W-8BEN for foreign / W-9 for US persons) are commonly required on file.",
                )
            )
        if not re.search(r"\bEIN\b|\bSSN\b|\btax\s*id\b", text, flags=re.IGNORECASE):
            findings.append(
                ComplianceFinding(
                    severity="medium",
                    code="US_TAX_ID",
                    title="US: tax identification not detected",
                    detail="No EIN / tax ID language found. Verify vendor master data before payment.",
                )
            )

    if not countries and assumed_country is None:
        findings.append(
            ComplianceFinding(
                severity="medium",
                code="UNKNOWN_JURISDICTION",
                title="Jurisdiction ambiguous",
                detail="Could not infer country from the text. Select an assumed country for sharper checks.",
            )
        )

    # Severity sort: high → medium → low
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order[f.severity])

    return findings, mock_llm_narrative(findings, len(text))


def render_finding(finding: ComplianceFinding) -> None:
    css = {"high": "risk-high", "medium": "risk-medium", "low": "risk-low"}[finding.severity]
    pill = {"high": "pill-high", "medium": "pill-medium", "low": "pill-low"}[finding.severity]
    st.markdown(
        f"""
        <div class="{css}">
            <div class="risk-title">
                <span class="pill {pill}">{finding.severity}</span>
                {finding.title}
            </div>
            <div class="risk-body">{finding.detail} <span class="pill pill-info">{finding.code}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 4) FEATURE 3 — Asynchronous Audit Log (simulated store)
# =============================================================================

def seed_audit_log() -> pd.DataFrame:
    """
    Deterministic sample of past audits for the dashboard table.
    In a production app this would be Postgres / Snowflake / an async job queue.
    """
    today = date.today()
    rows = [
        {"audit_id": "AUD-1001", "created_at": today - timedelta(days=1), "country": "Germany", "employee_type": "Full-time", "amount": 4200.00, "currency": "EUR", "status": "Completed", "risk_level": "Low", "source": "Calculator"},
        {"audit_id": "AUD-1002", "created_at": today - timedelta(days=2), "country": "US", "employee_type": "Contractor", "amount": 6500.00, "currency": "USD", "status": "Flagged", "risk_level": "High", "source": "AI Checker"},
        {"audit_id": "AUD-1003", "created_at": today - timedelta(days=3), "country": "UK", "employee_type": "Contractor", "amount": 3100.00, "currency": "EUR", "status": "Completed", "risk_level": "Medium", "source": "AI Checker"},
        {"audit_id": "AUD-1004", "created_at": today - timedelta(days=4), "country": "US", "employee_type": "Full-time", "amount": 9800.00, "currency": "USD", "status": "Completed", "risk_level": "Low", "source": "Calculator"},
        {"audit_id": "AUD-1005", "created_at": today - timedelta(days=5), "country": "Germany", "employee_type": "Contractor", "amount": 2750.00, "currency": "EUR", "status": "In review", "risk_level": "High", "source": "AI Checker"},
        {"audit_id": "AUD-1006", "created_at": today - timedelta(days=6), "country": "UK", "employee_type": "Full-time", "amount": 5400.00, "currency": "USD", "status": "Completed", "risk_level": "Low", "source": "Calculator"},
        {"audit_id": "AUD-1007", "created_at": today - timedelta(days=8), "country": "Germany", "employee_type": "Full-time", "amount": 11200.00, "currency": "EUR", "status": "Flagged", "risk_level": "Medium", "source": "AI Checker"},
        {"audit_id": "AUD-1008", "created_at": today - timedelta(days=9), "country": "US", "employee_type": "Contractor", "amount": 1500.00, "currency": "USD", "status": "Completed", "risk_level": "Medium", "source": "Calculator"},
        {"audit_id": "AUD-1009", "created_at": today - timedelta(days=11), "country": "UK", "employee_type": "Contractor", "amount": 890.00, "currency": "EUR", "status": "In review", "risk_level": "High", "source": "AI Checker"},
        {"audit_id": "AUD-1010", "created_at": today - timedelta(days=12), "country": "Germany", "employee_type": "Contractor", "amount": 4600.00, "currency": "EUR", "status": "Completed", "risk_level": "Low", "source": "Calculator"},
        {"audit_id": "AUD-1011", "created_at": today - timedelta(days=14), "country": "US", "employee_type": "Full-time", "amount": 7200.00, "currency": "USD", "status": "Completed", "risk_level": "Low", "source": "Calculator"},
        {"audit_id": "AUD-1012", "created_at": today - timedelta(days=16), "country": "UK", "employee_type": "Full-time", "amount": 3900.00, "currency": "USD", "status": "Flagged", "risk_level": "Medium", "source": "AI Checker"},
    ]
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def init_session_state() -> None:
    """Ensure Streamlit session has an audit log DataFrame and a counter."""
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = seed_audit_log()
    if "audit_seq" not in st.session_state:
        st.session_state.audit_seq = 1013


def append_audit_row(
    country: str,
    employee_type: str,
    amount: float,
    currency: str,
    status: str,
    risk_level: str,
    source: str,
) -> str:
    """Append a new row to the in-session audit log (simulates async write)."""
    init_session_state()
    audit_id = f"AUD-{st.session_state.audit_seq}"
    st.session_state.audit_seq += 1
    new_row = pd.DataFrame(
        [
            {
                "audit_id": audit_id,
                "created_at": pd.Timestamp(datetime.utcnow().date()),
                "country": country,
                "employee_type": employee_type,
                "amount": float(amount),
                "currency": currency,
                "status": status,
                "risk_level": risk_level,
                "source": source,
            }
        ]
    )
    st.session_state.audit_log = pd.concat([new_row, st.session_state.audit_log], ignore_index=True)
    return audit_id


# =============================================================================
# 5) UI PAGES
# =============================================================================

def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero-brand">Remote · Fintech Vertical</div>
        <h1 class="hero-title">{APP_TITLE}</h1>
        <p class="hero-sub">
            Simulate employer costs, flag invoice compliance gaps, and browse an audit trail —
            a product-shaped demo for global payroll & contractor billing.
        </p>
        """,
        unsafe_allow_html=True,
    )


def page_calculator() -> None:
    st.subheader("Invoice Audit Calculator")
    st.caption("Estimate employer cost, compliance fee, and tax/VAT for a single invoice.")

    with st.form("audit_calculator_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            country: Country = st.selectbox("Country", COUNTRIES, index=0)
            employee_type: EmployeeType = st.selectbox("Employee type", EMPLOYEE_TYPES, index=0)
        with c2:
            currency: Currency = st.selectbox("Currency", CURRENCIES, index=0)
            invoice_amount = st.number_input(
                "Invoice amount",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Gross invoice amount before simulated fees.",
            )
        submitted = st.form_submit_button("Run audit calculation", use_container_width=True)

    if submitted:
        try:
            result = calculate_audit(country, float(invoice_amount), currency, employee_type)
        except ValueError as exc:
            st.error(str(exc))
            return

        st.success(f"Audit ready for **{country}** · **{employee_type}**")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("Invoice", money(result.invoice_amount, currency), f"≈ ${result.amount_usd:,.2f} USD")
        with m2:
            render_metric_card("Compliance fee", money(result.compliance_fee, currency), f"{COUNTRY_RULES[country]['compliance_fee_rate']*100:.1f}% rate")
        with m3:
            render_metric_card("Employer social", money(result.employer_social, currency), "0% for contractors in this sim")
        with m4:
            render_metric_card("Tax / VAT est.", money(result.tax_vat, currency), "Often reclaimable B2B")

        t1, t2 = st.columns(2)
        with t1:
            render_metric_card(
                "Total employer cost",
                money(result.total_employer_cost, currency),
                "Invoice + compliance + social (VAT excluded from load)",
            )
        with t2:
            render_metric_card("Effective load", f"{result.effective_load_pct:.1f}%", result.notes)

        with st.expander("Raw breakdown (debug)"):
            st.json(result.to_display_dict())

        # Persist into audit log for Feature 3
        risk = "Low" if result.effective_load_pct < 10 else ("Medium" if result.effective_load_pct < 20 else "High")
        audit_id = append_audit_row(
            country=country,
            employee_type=employee_type,
            amount=result.invoice_amount,
            currency=currency,
            status="Completed",
            risk_level=risk,
            source="Calculator",
        )
        st.info(f"Logged as `{audit_id}` in the Asynchronous Audit Log tab.")


def page_compliance_checker() -> None:
    st.subheader("AI Invoice Compliance Checker")
    st.caption("Paste raw invoice text. Rule engine + mock LLM narrative flag structural risks.")

    default_de_sample = (
        "INVOICE\n"
        "From: Acme Beratungs GmbH, Berlin\n"
        "Bill to: Remote Customer AG\n"
        "Amount: EUR 4,200.00 for August consulting\n"
        "Please pay via bank transfer.\n"
    )
    us_sample = (
        "Invoice #4421\nDate: 08/01/2026\n"
        "Vendor: Jane Doe Consulting LLC, Delaware, USA\n"
        "Services: Product advisory — $6,500 USD\n"
        "Payable to account ending 4412\n"
    )

    # Widget state lives under this key (do not also pass value=)
    if "invoice_text_area" not in st.session_state:
        st.session_state.invoice_text_area = default_de_sample

    assumed_country = st.selectbox(
        "Assumed country (improves detection)",
        ["Auto-detect"] + COUNTRIES,
        index=0,
    )
    employee_type: EmployeeType = st.selectbox(
        "Payee type",
        EMPLOYEE_TYPES,
        index=0,
        key="compliance_employee_type",
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        run = st.button("Run compliance check", use_container_width=True)
    with col_b:
        if st.button("Load US contractor sample", use_container_width=True):
            st.session_state.invoice_text_area = us_sample
            st.rerun()

    invoice_text = st.text_area(
        "Invoice text",
        height=220,
        help="Paste OCR output or email body.",
        key="invoice_text_area",
    )

    if run:
        country_arg: Country | None = None if assumed_country == "Auto-detect" else assumed_country  # type: ignore[assignment]
        findings, narrative = check_invoice_compliance(invoice_text, country_arg, employee_type)

        st.markdown("##### Mock LLM summary")
        st.write(narrative)

        st.markdown("##### Structural findings")
        if not findings:
            st.markdown(
                '<div class="risk-low"><div class="risk-title">'
                '<span class="pill pill-low">ok</span> No structural risks flagged'
                "</div></div>",
                unsafe_allow_html=True,
            )
        else:
            for f in findings:
                render_finding(f)

        # Log to audit table
        worst = "Low"
        if any(f.severity == "high" for f in findings):
            worst = "High"
        elif any(f.severity == "medium" for f in findings):
            worst = "Medium"
        status = "Flagged" if worst in ("High", "Medium") else "Completed"
        country_for_log = country_arg or (next(iter(_detect_country_hints(invoice_text)), "US"))
        audit_id = append_audit_row(
            country=country_for_log,
            employee_type=employee_type,
            amount=0.0,
            currency="USD",
            status=status,
            risk_level=worst,
            source="AI Checker",
        )
        st.info(f"Logged as `{audit_id}` · risk **{worst}**")


def page_audit_log() -> None:
    st.subheader("Asynchronous Audit Log")
    st.caption("Simulated durable store of past audits — filter like a data-driven ops dashboard.")

    init_session_state()
    df: pd.DataFrame = st.session_state.audit_log.copy()

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        countries = st.multiselect("Country", COUNTRIES, default=COUNTRIES)
    with f2:
        statuses = st.multiselect(
            "Status",
            sorted(df["status"].unique().tolist()),
            default=sorted(df["status"].unique().tolist()),
        )
    with f3:
        risks = st.multiselect(
            "Risk level",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
        )
    with f4:
        sources = st.multiselect(
            "Source",
            sorted(df["source"].unique().tolist()),
            default=sorted(df["source"].unique().tolist()),
        )

    filtered = df[
        df["country"].isin(countries)
        & df["status"].isin(statuses)
        & df["risk_level"].isin(risks)
        & df["source"].isin(sources)
    ].sort_values("created_at", ascending=False)

    # KPI strip
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card("Audits shown", str(len(filtered)))
    with k2:
        render_metric_card("Flagged", str(int((filtered["status"] == "Flagged").sum())))
    with k3:
        render_metric_card("High risk", str(int((filtered["risk_level"] == "High").sum())))
    with k4:
        total_amt = filtered["amount"].sum()
        render_metric_card("Σ amounts", f"{total_amt:,.0f}")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "audit_id": "Audit ID",
            "created_at": st.column_config.DateColumn("Created", format="YYYY-MM-DD"),
            "country": "Country",
            "employee_type": "Employee type",
            "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "currency": "CCY",
            "status": "Status",
            "risk_level": "Risk",
            "source": "Source",
        },
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv,
        file_name="audit_log_export.csv",
        mime="text/csv",
    )


# =============================================================================
# 6) MAIN
# =============================================================================

def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(REMOTE_CSS, unsafe_allow_html=True)
    init_session_state()

    with st.sidebar:
        st.markdown("### Navigation")
        st.markdown(f"*{APP_TAGLINE}*")
        st.markdown("---")
        st.markdown(
            """
            **Modules**
            1. Invoice Audit Calculator  
            2. AI Compliance Checker  
            3. Asynchronous Audit Log  

            Rates are **illustrative** for product demos only.
            """
        )
        st.markdown("---")
        if st.button("Reset audit log to seed data"):
            st.session_state.audit_log = seed_audit_log()
            st.session_state.audit_seq = 1013
            st.success("Audit log reset.")

    render_header()

    tab1, tab2, tab3 = st.tabs(
        ["Invoice Audit Calculator", "AI Compliance Checker", "Asynchronous Audit Log"]
    )
    with tab1:
        page_calculator()
    with tab2:
        page_compliance_checker()
    with tab3:
        page_audit_log()

    st.markdown(
        '<p class="disclaimer">Disclaimer: Simulated fees, VAT, and compliance checks for MVP prototyping. '
        "Not tax, legal, or accounting advice. Replace mock LLM with a real model + policy engine for production.</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
