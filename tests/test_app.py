"""Unit tests for the Global Billing & Invoice Compliance Auditor core logic.

These tests exercise the pure calculation and rule-engine functions in ``app.py``
and do not require a running Streamlit server.
"""

from __future__ import annotations

import pytest

from app import (
    COUNTRY_RULES,
    calculate_audit,
    check_invoice_compliance,
    from_usd,
    to_usd,
)

GERMAN_SAMPLE = (
    "INVOICE\n"
    "From: Acme Beratungs GmbH, Berlin\n"
    "Bill to: Remote Customer AG\n"
    "Amount: EUR 4,200.00 for August consulting\n"
)

US_CONTRACTOR_SAMPLE = (
    "Invoice #4421\n"
    "Date: 08/01/2026\n"
    "Vendor: Jane Doe Consulting LLC, Delaware, USA\n"
    "Services: Product advisory - $6,500 USD\n"
    "Payable to account ending 4412\n"
)

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class TestCurrencyConversion:
    def test_usd_is_identity(self):
        assert to_usd(100.0, "USD") == 100.0
        assert from_usd(100.0, "USD") == 100.0

    def test_eur_roundtrip_is_stable(self):
        original = 500.0
        assert from_usd(to_usd(original, "EUR"), "EUR") == pytest.approx(original)


class TestCalculateAudit:
    def test_us_contractor_incurs_only_compliance_fee(self):
        result = calculate_audit("US", 1000.0, "USD", "Contractor")
        assert result.compliance_fee == pytest.approx(28.0)
        assert result.employer_social == pytest.approx(0.0)
        assert result.tax_vat == pytest.approx(0.0)
        assert result.total_employer_cost == pytest.approx(1028.0)
        assert result.effective_load_pct == pytest.approx(2.8)

    def test_full_time_worker_has_social_contribution(self):
        result = calculate_audit("Germany", 1000.0, "EUR", "Full-time")
        assert result.employer_social > 0

    def test_contractor_has_no_social_contribution(self):
        result = calculate_audit("UK", 1000.0, "EUR", "Contractor")
        assert result.employer_social == pytest.approx(0.0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError):
            calculate_audit("US", -1.0, "USD", "Contractor")

    def test_notes_come_from_country_rules(self):
        result = calculate_audit("Germany", 1000.0, "EUR", "Full-time")
        assert result.notes == COUNTRY_RULES["Germany"]["notes"]

    def test_total_excludes_vat_from_load(self):
        # Germany full-time: total = base + compliance + social (VAT tracked separately).
        result = calculate_audit("Germany", 1000.0, "EUR", "Full-time")
        assert result.total_employer_cost < result.invoice_amount + result.tax_vat + 1000


class TestComplianceChecker:
    def test_short_text_is_flagged_high(self):
        findings, _ = check_invoice_compliance("too short", None, "Contractor")
        assert any(f.code == "EMPTY_OR_SHORT" for f in findings)
        assert findings[0].severity == "high"

    def test_german_invoice_missing_vat_is_flagged(self):
        findings, _ = check_invoice_compliance(GERMAN_SAMPLE, "Germany", "Contractor")
        assert "DE_MISSING_VAT" in {f.code for f in findings}

    def test_us_contractor_missing_tax_form_is_flagged(self):
        findings, _ = check_invoice_compliance(US_CONTRACTOR_SAMPLE, None, "Contractor")
        assert "US_MISSING_W8BEN" in {f.code for f in findings}

    def test_findings_are_sorted_by_severity(self):
        findings, _ = check_invoice_compliance(GERMAN_SAMPLE, "Germany", "Contractor")
        ranks = [SEVERITY_ORDER[f.severity] for f in findings]
        assert ranks == sorted(ranks)

    def test_narrative_is_returned(self):
        _, narrative = check_invoice_compliance(GERMAN_SAMPLE, "Germany", "Contractor")
        assert isinstance(narrative, str)
        assert narrative.strip() != ""
