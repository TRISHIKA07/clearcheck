"""
ComplianceCore AI Report Generator Module.
Generates comprehensive Markdown and PDF audit reports containing customer profile details,
transaction analytics, rule findings, risk scores, and local Gemma's final reasoning.
"""

import logging
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import config
from utils import setup_logging
from models import CustomerProfile, TransactionSummary, RuleFinding, RiskAssessment, GemmaResponse, AuditReport

logger = logging.getLogger("ComplianceCore.Report")

class CompliancePDF(FPDF):
    """
    Custom FPDF2 subclass for compliance audit reports.
    """
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "COMPLIANCECORE AI - CONFIDENTIAL REGULATORY AUDIT REPORT", ln=1, align="R")
        self.set_draw_color(200, 200, 200)
        self.line(10, 15, 200, 15)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def generate_markdown_report(
    report_id: str,
    generated_at: str,
    profile: CustomerProfile,
    txn_summary: TransactionSummary,
    risk_assessment: RiskAssessment,
    gemma_response: GemmaResponse,
    rule_findings: list[RuleFinding],
    output_path: Path
) -> None:
    """
    Writes a formatted Markdown compliance report to disk.
    """
    try:
        md_content = f"""# ComplianceCore AI Audit Report
**Report ID:** {report_id}  
**Generated At:** {generated_at}  
**Anchor Date:** 2026-07-18  

---

## 1. CUSTOMER IDENTITY & KYC PROFILE
* **Customer Name:** {profile.name or "N/A"}
* **Date of Birth:** {profile.dob or "N/A"}
* **Address:** {profile.address or "N/A"}
* **PAN Number:** {profile.pan or "N/A"}
* **Aadhaar Number:** {profile.aadhaar or "N/A"}
* **Passport Number:** {profile.passport_number or "N/A"}
* **Driving License:** {profile.driving_license_number or "N/A"}
* **Expiry Date:** {profile.expiry_date or "N/A"}
* **Utility Bill Info:** {profile.utility_bill_info or "N/A"}
* **Bank Statement Info:** {profile.bank_statement_info or "N/A"}

---

## 2. TRANSACTION ANALYTICS & STATISTICS
* **Total Transactions:** {txn_summary.total_transactions}
* **Total Volume:** {txn_summary.total_volume:.2f}
* **Average Transaction Amount:** {txn_summary.average_amount:.2f}
* **Minimum / Maximum Amount:** {txn_summary.minimum_amount:.2f} / {txn_summary.maximum_amount:.2f}
* **Duplicate Transactions:** {txn_summary.duplicate_transactions_count}
* **Missing Fields Count:** {txn_summary.missing_fields_count}
* **High-Value Transfers Count:** {txn_summary.high_value_transfers_count}
* **Velocity Violations Count:** {txn_summary.velocity_violations_count}
* **Transaction Bursts Count:** {txn_summary.transaction_bursts_count}
* **Suspicious Keywords Found:** {txn_summary.suspicious_descriptions_count}
* **Cross-Border Transfers:** {txn_summary.cross_border_count}

---

## 3. DETERMINISTIC COMPLIANCE RULES CHECK
| Rule ID | Rule Name | Status | Severity | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
"""
        for f in rule_findings:
            md_content += f"| {f.rule_id} | {f.rule_name} | {f.status} | {f.severity} | {f.recommendation} |\n"

        md_content += f"""
---

## 4. DETERMINISTIC RISK EVALUATION
* **Calculated Risk Score:** {risk_assessment.risk_score} / 100
* **Calculated Risk Level:** {risk_assessment.risk_level}
* **Triage Priority:** {risk_assessment.priority}
* **Assessment Confidence:** {risk_assessment.confidence:.2f}

---

## 5. LOCAL GEMMA AI FINAL COMPLIANCE DECISION
* **Compliance Review Decision:** **{gemma_response.compliance_decision}**
* **AI Assessed Severity:** {gemma_response.severity}
* **AI Decision Confidence:** {gemma_response.confidence:.2f}

### Executive Summary
{gemma_response.executive_summary}

### Detailed Audit Summary
{gemma_response.audit_summary}

### Key Evidence Cited
{gemma_response.evidence}

### AI Regulatory Recommendations
"""
        for rec in gemma_response.recommendations:
            md_content += f"* {rec}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Markdown report generated successfully at: {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate markdown report: {e}")
        raise e

def generate_pdf_report(
    report_id: str,
    generated_at: str,
    profile: CustomerProfile,
    txn_summary: TransactionSummary,
    risk_assessment: RiskAssessment,
    gemma_response: GemmaResponse,
    rule_findings: list[RuleFinding],
    output_path: Path
) -> None:
    """
    Generates a professionally structured PDF report using fpdf2.
    """
    try:
        pdf = CompliancePDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Palette definition
        c_primary = (25, 42, 86)  # Deep Navy Blue
        c_text = (44, 62, 80)     # Dark Slate
        c_risk_level = {
            "Low": (39, 174, 96),       # Green
            "Medium": (243, 156, 18),   # Orange
            "High": (211, 47, 47),      # Soft Red
            "Critical": (153, 0, 0)     # Crimson
        }

        # --- Report Title Block ---
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 10, "COMPLIANCE & RISK TRIAGE AUDIT REPORT", ln=1, align="L")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        pdf.cell(100, 5, f"Report ID: {report_id}", ln=0)
        pdf.cell(0, 5, f"Generated At: {generated_at}", ln=1, align="R")
        pdf.cell(100, 5, "Anchor Date: 2026-07-18", ln=0)
        pdf.cell(0, 5, "AI Engine: Google Gemma 4 (Local)", ln=1, align="R")
        pdf.ln(5)

        # --- Section 1: Customer KYC Profile ---
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 8, "1. Customer Identity & KYC Profile", ln=1)
        pdf.set_draw_color(*c_primary)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        
        # Grid layout for profile
        profile_data = [
            ("Customer Name:", profile.name or "N/A"),
            ("Date of Birth:", profile.dob or "N/A"),
            ("Address:", profile.address or "N/A"),
            ("PAN Card:", profile.pan or "N/A"),
            ("Aadhaar Number:", profile.aadhaar or "N/A"),
            ("Passport Number:", profile.passport_number or "N/A"),
            ("Driving License:", profile.driving_license_number or "N/A"),
            ("Document Expiry:", profile.expiry_date or "N/A"),
            ("Utility Bill Info:", profile.utility_bill_info or "N/A"),
            ("Bank Statement:", profile.bank_statement_info or "N/A")
        ]
        
        for label, val in profile_data:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(40, 5, label, ln=0)
            pdf.set_font("Helvetica", "", 9)
            # Wrap text for long addresses
            if label == "Address:" or len(val) > 60:
                pdf.multi_cell(0, 5, val)
                pdf.ln(1)
            else:
                pdf.cell(0, 5, val, ln=1)
        pdf.ln(4)

        # --- Section 2: Transaction Analytics ---
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 8, "2. Transaction Analytics & Statistics", ln=1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        
        stats_col1 = [
            f"Total Transactions: {txn_summary.total_transactions}",
            f"Total Transaction Volume: {txn_summary.total_volume:.2f}",
            f"Average Txn Amount: {txn_summary.average_amount:.2f}",
            f"Min / Max Txn Amount: {txn_summary.minimum_amount:.2f} / {txn_summary.maximum_amount:.2f}"
        ]
        stats_col2 = [
            f"Duplicate Transactions Count: {txn_summary.duplicate_transactions_count}",
            f"Missing Fields Count: {txn_summary.missing_fields_count}",
            f"High-Value Transfers Count: {txn_summary.high_value_transfers_count}",
            f"Velocity / Burst Warnings: {txn_summary.velocity_violations_count} / {txn_summary.transaction_bursts_count}",
            f"Suspicious Keyword / Cross-Border: {txn_summary.suspicious_descriptions_count} / {txn_summary.cross_border_count}"
        ]

        # Draw columns side by side
        y_pos = pdf.get_y()
        for idx, line in enumerate(stats_col1):
            pdf.set_xy(10, y_pos + (idx * 5))
            pdf.cell(90, 5, f"- {line}")
            
        for idx, line in enumerate(stats_col2):
            pdf.set_xy(105, y_pos + (idx * 5))
            pdf.cell(90, 5, f"- {line}")
            
        pdf.set_xy(10, y_pos + (max(len(stats_col1), len(stats_col2)) * 5) + 3)
        pdf.ln(2)

        # --- Section 3: Deterministic Compliance Rules Check ---
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 8, "3. Deterministic Compliance Rules Check", ln=1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        # Table Header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(45, 5, "Rule Name", border=1, fill=True)
        pdf.cell(20, 5, "Status", border=1, fill=True, align="C")
        pdf.cell(20, 5, "Severity", border=1, fill=True, align="C")
        pdf.cell(105, 5, "Key Recommendation / Remediation", border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for f in rule_findings:
            # Color Status
            if f.status == "FAIL":
                pdf.set_text_color(211, 47, 47)
            else:
                pdf.set_text_color(39, 174, 96)
                
            pdf.cell(45, 5, f.rule_name[:25], border=1)
            pdf.cell(20, 5, f.status, border=1, align="C")
            
            # Reset text color for severity
            pdf.set_text_color(*c_text)
            pdf.cell(20, 5, f.severity, border=1, align="C")
            
            # Print recommendation (multi-cell wrapping handled carefully)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(105, 5, f.recommendation, border=1)
            y_after = pdf.get_y()
            pdf.set_xy(10, y_after)
            
        pdf.set_text_color(*c_text)
        pdf.ln(4)

        # --- Section 4: Risk Evaluation & Local AI Review ---
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 8, "4. Triage & Local AI Compliance Review", ln=1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        # Risk Box Row
        pdf.set_fill_color(245, 246, 250)
        pdf.rect(10, pdf.get_y(), 190, 20, style="F")
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(50, 5, "  Calculated Risk Score:", ln=0)
        pdf.cell(50, 5, "  Risk Level:", ln=0)
        pdf.cell(50, 5, "  Triage Priority:", ln=0)
        pdf.cell(40, 5, "  AI Decision:", ln=1)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(50, 8, f"  {risk_assessment.risk_score} / 100", ln=0)
        
        # Color Risk Level
        lvl_color = c_risk_level.get(risk_assessment.risk_level, c_text)
        pdf.set_text_color(*lvl_color)
        pdf.cell(50, 8, f"  {risk_assessment.risk_level}", ln=0)
        
        # Color Priority
        pdf.cell(50, 8, f"  {risk_assessment.priority}", ln=0)
        
        # Color Decision
        dec_color = c_risk_level.get("High" if gemma_response.compliance_decision in ["REJECTED", "ESCALATED"] else "Low")
        pdf.set_text_color(*dec_color)
        pdf.cell(40, 8, f"  {gemma_response.compliance_decision}", ln=1)
        
        pdf.set_text_color(*c_text)
        pdf.ln(6)

        # Executive Summary Narrative
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 5, "AI Executive Summary:", ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        pdf.multi_cell(0, 4.5, gemma_response.executive_summary)
        pdf.ln(3)

        # Audit Summary Narrative
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 5, "AI Regulatory Audit Narrative:", ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        pdf.multi_cell(0, 4.5, gemma_response.audit_summary)
        pdf.ln(3)

        # Evidence Block
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 5, "AI Evidence Cited:", ln=1)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*c_text)
        pdf.multi_cell(0, 4.5, gemma_response.evidence)
        pdf.ln(3)

        # Recommendations
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*c_primary)
        pdf.cell(0, 5, "AI Regulatory Recommendations:", ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*c_text)
        for rec in gemma_response.recommendations:
            pdf.multi_cell(0, 4.5, f"- {rec}")
            pdf.ln(1)
            
        # Write PDF to file
        pdf.output(str(output_path))
        logger.info(f"PDF audit report generated successfully at: {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate PDF audit report: {e}")
        raise e

def compile_audit_report(
    profile: CustomerProfile,
    txn_summary: TransactionSummary,
    risk_assessment: RiskAssessment,
    gemma_response: GemmaResponse,
    rule_findings: list[RuleFinding]
) -> AuditReport:
    """
    Compiles all compliance metadata and triggers both Markdown and PDF report generation.
    Returns a typed AuditReport object containing file paths and metadata.
    """
    # Normalize Gemma response data types (Gemma may return lists for strings, or strings for lists)
    if isinstance(gemma_response.executive_summary, list):
        gemma_response.executive_summary = "\n".join(str(x) for x in gemma_response.executive_summary)
    else:
        gemma_response.executive_summary = str(gemma_response.executive_summary)

    if isinstance(gemma_response.audit_summary, list):
        gemma_response.audit_summary = "\n".join(str(x) for x in gemma_response.audit_summary)
    else:
        gemma_response.audit_summary = str(gemma_response.audit_summary)

    if isinstance(gemma_response.evidence, list):
        gemma_response.evidence = "\n".join(f"- {x}" for x in gemma_response.evidence)
    else:
        gemma_response.evidence = str(gemma_response.evidence)

    if isinstance(gemma_response.recommendations, str):
        gemma_response.recommendations = [gemma_response.recommendations]
    elif not isinstance(gemma_response.recommendations, list):
        gemma_response.recommendations = []

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_id = f"CC-{timestamp_str}"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format filename template: e.g. 20231027_High_audit_report
    formatted_base_name = config.AUDIT_FILENAME_TEMPLATE.format(
        date=datetime.now().strftime("%Y%m%d"),
        risk_level=risk_assessment.risk_level
    )
    
    md_filename = f"{formatted_base_name}_{report_id}.md"
    pdf_filename = f"{formatted_base_name}_{report_id}.pdf"
    
    md_path = config.REPORTS_DIR / md_filename
    pdf_path = config.REPORTS_DIR / pdf_filename

    # Ensure reports directory exists
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate Markdown Report
    generate_markdown_report(
        report_id=report_id,
        generated_at=generated_at,
        profile=profile,
        txn_summary=txn_summary,
        risk_assessment=risk_assessment,
        gemma_response=gemma_response,
        rule_findings=rule_findings,
        output_path=md_path
    )

    # 2. Generate PDF Report
    generate_pdf_report(
        report_id=report_id,
        generated_at=generated_at,
        profile=profile,
        txn_summary=txn_summary,
        risk_assessment=risk_assessment,
        gemma_response=gemma_response,
        rule_findings=rule_findings,
        output_path=pdf_path
    )

    return AuditReport(
        report_id=report_id,
        generated_at=generated_at,
        pdf_path=str(pdf_path),
        markdown_path=str(md_path),
        customer_profile=profile,
        transaction_summary=txn_summary,
        risk_assessment=risk_assessment,
        gemma_response=gemma_response
    )
