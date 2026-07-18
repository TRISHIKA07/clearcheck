"""
ComplianceCore AI Main Streamlit Dashboard.
Integrates all modules: OCR, parsing, transaction processing, deterministic compliance checks,
numerical risk engine, local Gemma reasoning, and report generation into a premium dashboard interface.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
import logging
from datetime import datetime

import config
from utils import setup_logging
from ocr import extract_text_from_file
from parser import parse_customer_profile
from transactions import analyze_transaction_csv
from compliance import execute_compliance_rules
from risk_engine import evaluate_overall_risk
from ai import call_gemma
from prompts import build_compliance_prompt
from report import compile_audit_report
from models import CustomerProfile, TransactionSummary, RiskAssessment, GemmaResponse, AuditReport

# Set up logging
logger = setup_logging()

# Streamlit Page Config
st.set_page_config(
    page_title="ComplianceCore AI - Risk Triage Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling inject (Navy, Amber, Slate, Soft Red)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            color: #2C3E50;
        }
        
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #192A56;
            margin-bottom: 0.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .sub-header {
            font-size: 1rem;
            color: #7F8C8D;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(224, 224, 224, 0.5);
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 0.5rem;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #7F8C8D;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .decision-badge {
            font-size: 1.2rem;
            font-weight: 700;
            padding: 0.5rem 1.5rem;
            border-radius: 30px;
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .badge-approved {
            background-color: #D4EDDA;
            color: #155724;
            border: 1px solid #C3E6CB;
        }
        
        .badge-rejected {
            background-color: #F8D7DA;
            color: #721C24;
            border: 1px solid #F5C6CB;
        }
        
        .badge-escalated {
            background-color: #FFF3CD;
            color: #856404;
            border: 1px solid #FFEEBA;
        }
        
        .report-section {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            border-left: 5px solid #192A56;
        }
        
        .rule-card {
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
            border: 1px solid #E0E0E0;
        }
        
        .rule-fail {
            border-left: 4px solid #D32F2F;
            background-color: #FFEBEE;
        }
        
        .rule-pass {
            border-left: 4px solid #2ECC71;
            background-color: #E8F8F5;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States
if "profile" not in st.session_state:
    st.session_state.profile = None
if "txn_summary" not in st.session_state:
    st.session_state.txn_summary = None
if "risk_assessment" not in st.session_state:
    st.session_state.risk_assessment = None
if "gemma_response" not in st.session_state:
    st.session_state.gemma_response = None
if "rule_findings" not in st.session_state:
    st.session_state.rule_findings = []
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

# Sidebar settings and configurations
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/shield.png", width=80)
    st.markdown("### ComplianceCore AI")
    st.markdown("Financial Risk Triage & Audit Tool")
    st.markdown("---")
    
    st.markdown("#### System Configurations (Local)")
    model_name = st.text_input("Ollama Model Name", value=config.GEMMA_MODEL_NAME, disabled=True)
    host_url = st.text_input("Ollama Host URL", value=config.OLLAMA_BASE_URL, disabled=True)
    
    st.markdown("---")
    st.markdown("#### About the Sprint")
    st.markdown(
        "Built for Google's **Build with Gemma: Bengaluru AI Sprint**.\n\n"
        "Leverages local deterministic rule engines, PyMuPDF, Tesseract, and local Gemma via Ollama "
        "to ensure 100% data privacy and compliance."
    )
    
    if st.button("Clear Dashboard"):
        st.session_state.profile = None
        st.session_state.txn_summary = None
        st.session_state.risk_assessment = None
        st.session_state.gemma_response = None
        st.session_state.rule_findings = []
        st.session_state.audit_report = None
        st.session_state.ocr_text = ""
        st.rerun()

# Dashboard Title
st.markdown('<div class="main-header">🛡️ ComplianceCore AI Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Financial Compliance Audit & Triage Automation Hub</div>', unsafe_allow_html=True)

# Main Grid: File Uploader
u_col1, u_col2 = st.columns(2)

with u_col1:
    st.subheader("1. Customer KYC Document")
    uploaded_doc = st.file_uploader(
        "Upload Government ID / Utility Bill / Bank PDF or Image (PDF, PNG, JPG, JPEG)",
        type=["pdf", "png", "jpg", "jpeg"]
    )

with u_col2:
    st.subheader("2. Transaction History Log")
    uploaded_csv = st.file_uploader(
        "Upload Customer Transaction Log (CSV format)",
        type=["csv"]
    )

st.markdown("---")

# Execution Action Button
if uploaded_doc or uploaded_csv:
    if st.button("⚡ Run Deterministic & AI Triage Review", type="primary", use_container_width=True):
        with st.spinner("Processing documents, extracting identity, and running transaction engine..."):
            
            # Reset values
            profile = CustomerProfile()
            txn_summary = TransactionSummary()
            st.session_state.ocr_text = ""
            
            # --- Step 1: Handle KYC Document ---
            if uploaded_doc:
                # Save file
                doc_path = config.UPLOADS_DIR / uploaded_doc.name
                with open(doc_path, "wb") as f:
                    f.write(uploaded_doc.getbuffer())
                    
                # Run OCR
                logger.info(f"Running OCR on {uploaded_doc.name}")
                ocr_text = extract_text_from_file(doc_path)
                
                if ocr_text:
                    st.session_state.ocr_text = ocr_text
                    # Parse customer profile
                    profile = parse_customer_profile(ocr_text)
                else:
                    st.error("Failed to extract text from the KYC document. Please verify the file.")
            
            # --- Step 2: Handle Transactions CSV ---
            csv_path = None
            if uploaded_csv:
                csv_path = config.UPLOADS_DIR / uploaded_csv.name
                with open(csv_path, "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                
                # Analyze transactions
                logger.info(f"Analyzing transaction file: {uploaded_csv.name}")
                txn_summary = analyze_transaction_csv(csv_path)
                
            # Store in session state
            st.session_state.profile = profile
            st.session_state.txn_summary = txn_summary
            
            # --- Step 3: Run Deterministic Compliance Rules ---
            logger.info("Executing rule checks")
            rule_findings = execute_compliance_rules(
                profile=profile,
                txn_summary=txn_summary,
                txn_csv_path=str(csv_path) if csv_path else None
            )
            st.session_state.rule_findings = rule_findings
            
            # --- Step 4: Evaluate Risk Score ---
            logger.info("Evaluating risk score")
            risk_assessment = evaluate_overall_risk(rule_findings)
            st.session_state.risk_assessment = risk_assessment
            
            # --- Step 5: Send context to Local Gemma via Ollama ---
            with st.spinner("Invoking local Gemma for compliance reasoning and audit compilation..."):
                sys_prompt, user_prompt = build_compliance_prompt(
                    customer_profile=profile,
                    transaction_summary=txn_summary,
                    rule_findings=rule_findings,
                    risk_assessment=risk_assessment
                )
                
                # Inference
                gemma_json = call_gemma(prompt=user_prompt, system_prompt=sys_prompt)
                
                # Convert to dataclass
                gemma_response = GemmaResponse(
                    executive_summary=gemma_json.get("executive_summary", "N/A"),
                    compliance_decision=gemma_json.get("compliance_decision", "ESCALATED"),
                    evidence=gemma_json.get("evidence", "N/A"),
                    severity=gemma_json.get("severity", "Medium"),
                    confidence=float(gemma_json.get("confidence", 0.5)),
                    audit_summary=gemma_json.get("audit_summary", "N/A"),
                    recommendations=gemma_json.get("recommendations", [])
                )
                st.session_state.gemma_response = gemma_response
                
            # --- Step 6: Generate Audit Report Files ---
            logger.info("Generating report files")
            audit_report = compile_audit_report(
                profile=profile,
                txn_summary=txn_summary,
                risk_assessment=risk_assessment,
                gemma_response=gemma_response,
                rule_findings=rule_findings
            )
            st.session_state.audit_report = audit_report
            
            st.success("Triage analysis complete! Review findings below.")
            st.balloons()
else:
    st.info("💡 Please upload a KYC document and/or a transaction CSV to trigger the compliance triage review.")

# --- DISPLAY ANALYSIS RESULTS ---
if st.session_state.profile or st.session_state.txn_summary:
    profile = st.session_state.profile
    txn_summary = st.session_state.txn_summary
    risk_assessment = st.session_state.risk_assessment
    gemma_response = st.session_state.gemma_response
    rule_findings = st.session_state.rule_findings
    audit_report = st.session_state.audit_report
    
    # 1. Key Metrics Cards Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        score = risk_assessment.risk_score if risk_assessment else 0.0
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Calculated Risk Score</div>
                <div class="metric-value" style="color:#D32F2F;">{score} / 100</div>
            </div>
        """, unsafe_allow_html=True)
        
    with m_col2:
        level = risk_assessment.risk_level if risk_assessment else "Low"
        lvl_color = "#155724" if level == "Low" else ("#856404" if level == "Medium" else "#721C24")
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Risk Category</div>
                <div class="metric-value" style="color:{lvl_color};">{level}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with m_col3:
        priority = risk_assessment.priority if risk_assessment else "Low"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Triage Priority</div>
                <div class="metric-value" style="color:#192A56;">{priority}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with m_col4:
        decision = gemma_response.compliance_decision if gemma_response else "ESCALATED"
        bg_class = "badge-approved" if decision == "APPROVED" else ("badge-rejected" if decision == "REJECTED" else "badge-escalated")
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Gemma AI Decision</div>
                <div class="decision-badge {bg_class}">{decision}</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.ln = 3
    st.markdown("### Compliance Triage Insights")
    
    # Interactive Tabs for analysis view
    tab_kyc, tab_txn, tab_rules, tab_ai, tab_raw_ocr = st.tabs([
        "👤 Customer KYC Profile", 
        "📊 Transaction Analytics", 
        "🚨 Deterministic Rules Check", 
        "🤖 Local Gemma AI Review",
        "📄 Raw OCR Extraction"
    ])
    
    # Tab 1: Customer Profile
    with tab_kyc:
        st.subheader("Extracted Identity Information")
        st.markdown("Below is the identity profile extracted deterministically from the KYC documents:")
        
        # Display inputs allowing compliance officer verification
        with st.form("kyc_profile_form"):
            pk_col1, pk_col2 = st.columns(2)
            with pk_col1:
                e_name = st.text_input("Customer Name", value=profile.name or "")
                e_dob = st.text_input("Date of Birth", value=profile.dob or "")
                e_pan = st.text_input("PAN Number", value=profile.pan or "")
                e_aadhaar = st.text_input("Aadhaar Number", value=profile.aadhaar or "")
                e_passport = st.text_input("Passport Number", value=profile.passport_number or "")
            with pk_col2:
                e_dl = st.text_input("Driving License", value=profile.driving_license_number or "")
                e_expiry = st.text_input("Document Expiry", value=profile.expiry_date or "")
                e_address = st.text_area("Address", value=profile.address or "", height=80)
                e_utility = st.text_input("Utility Bill Info", value=profile.utility_bill_info or "")
                e_bank = st.text_input("Bank Statement Info", value=profile.bank_statement_info or "")
                
            submitted = st.form_submit_button("💾 Save & Update Profile Details")
            if submitted:
                # Update session state profile
                st.session_state.profile = CustomerProfile(
                    name=e_name if e_name else None,
                    dob=e_dob if e_dob else None,
                    address=e_address if e_address else None,
                    pan=e_pan if e_pan else None,
                    aadhaar=e_aadhaar if e_aadhaar else None,
                    passport_number=e_passport if e_passport else None,
                    driving_license_number=e_dl if e_dl else None,
                    expiry_date=e_expiry if e_expiry else None,
                    utility_bill_info=e_utility if e_utility else None,
                    bank_statement_info=e_bank if e_bank else None
                )
                st.success("Customer profile updated! Re-run Triage to update risk scores.")
                st.rerun()

    # Tab 2: Transaction Analytics
    with tab_txn:
        if txn_summary and txn_summary.total_transactions > 0:
            st.subheader("Transaction History Metrics")
            
            # Show summary stats
            st.write(
                f"**Total Volume Processed:** INR {txn_summary.total_volume:,.2f} | "
                f"**Average Transaction:** INR {txn_summary.average_amount:,.2f} | "
                f"**Min / Max:** INR {txn_summary.minimum_amount:,.2f} / INR {txn_summary.maximum_amount:,.2f}"
            )
            
            # Plot charts
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("#### Daily Volume Distribution")
                if txn_summary.daily_summary:
                    daily_df = pd.DataFrame(list(txn_summary.daily_summary.items()), columns=["Date", "Amount"])
                    daily_df = daily_df.sort_values(by="Date")
                    fig_line = px.line(daily_df, x="Date", y="Amount", title="Daily Transaction Volumes", markers=True)
                    fig_line.update_traces(line_color="#192A56")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Insufficient daily data for plotting.")
                    
            with c2:
                st.markdown("#### Merchant & Beneficiary Frequency")
                if txn_summary.merchant_frequency:
                    merch_df = pd.DataFrame(list(txn_summary.merchant_frequency.items()), columns=["Merchant", "Count"])
                    merch_df = merch_df.sort_values(by="Count", ascending=False).head(10)
                    fig_bar = px.bar(merch_df, x="Count", y="Merchant", orientation="h", title="Top Beneficiaries")
                    fig_bar.update_traces(marker_color="#27AE60")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Insufficient beneficiary data for plotting.")

            # Country pie chart
            st.markdown("#### Geographic Transaction Summary")
            if txn_summary.country_summary:
                country_df = pd.DataFrame(list(txn_summary.country_summary.items()), columns=["Country", "Txn Count"])
                fig_pie = px.pie(country_df, values="Txn Count", names="Country", title="Transaction Locations")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Anomaly Log
            st.markdown("#### Transaction Engine Warnings")
            if txn_summary.findings:
                for idx, finding in enumerate(txn_summary.findings):
                    st.warning(f"⚠️ {finding}")
            else:
                st.success("No anomalies detected by the transaction engine.")
        else:
            st.info("No transaction CSV has been uploaded or parsed.")

    # Tab 3: Deterministic Rules Checklist
    with tab_rules:
        st.subheader("Rules Evaluation Checklist")
        st.write("Deterministic compliance checks executed in the backend:")
        
        for f in rule_findings:
            card_class = "rule-fail" if f.status == "FAIL" else "rule-pass"
            icon = "❌" if f.status == "FAIL" else "✅"
            
            st.markdown(f"""
                <div class="rule-card {card_class}">
                    <strong>{icon} {f.rule_name}</strong> - Status: <strong>{f.status}</strong><br/>
                    <small>Rule ID: {f.rule_id} | Severity: <strong>{f.severity}</strong></small><br/>
                    <p style="margin-top:0.5rem; margin-bottom:0.2rem;"><strong>Findings:</strong> {f.findings}</p>
                    <p style="margin-bottom:0.2rem; font-size:0.85rem;"><strong>Evidence Cited:</strong> <code>{f.evidence}</code></p>
                    <p style="margin-bottom:0px; font-size:0.85rem;"><strong>Remediation:</strong> {f.recommendation}</p>
                </div>
            """, unsafe_allow_html=True)

    # Tab 4: Gemma AI Final Review & Download Reports
    with tab_ai:
        if gemma_response:
            st.subheader("Local Gemma Audit Summary")
            
            # Action Banner for Report Downloads
            if audit_report:
                st.markdown("#### 📥 Download Compliance Reports")
                d_col1, d_col2 = st.columns(2)
                
                # Read files to enable direct Streamlit download
                try:
                    with open(audit_report.pdf_path, "rb") as f:
                        pdf_data = f.read()
                    d_col1.download_button(
                        label="📄 Download PDF Audit Report",
                        data=pdf_data,
                        file_name=os.path.basename(audit_report.pdf_path),
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    d_col1.error(f"Failed to prepare PDF download: {e}")
                    
                try:
                    with open(audit_report.markdown_path, "r", encoding="utf-8") as f:
                        md_data = f.read()
                    d_col2.download_button(
                        label="📝 Download Markdown Report",
                        data=md_data,
                        file_name=os.path.basename(audit_report.markdown_path),
                        mime="text/markdown",
                        use_container_width=True
                    )
                except Exception as e:
                    d_col2.error(f"Failed to prepare Markdown download: {e}")
                st.markdown("---")
            
            # AI findings
            st.markdown('<div class="report-section">', unsafe_allow_html=True)
            st.markdown(f"#### Final Decision: **{gemma_response.compliance_decision}**")
            st.markdown(f"**AI Severity Rating:** {gemma_response.severity} | **Reasoning Confidence:** {gemma_response.confidence:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("#### Executive Summary")
            st.write(gemma_response.executive_summary)
            
            st.markdown("#### Detailed Audit Summary")
            st.write(gemma_response.audit_summary)
            
            st.markdown("#### Key Evidence")
            st.info(gemma_response.evidence)
            
            st.markdown("#### AI Recommendations")
            for rec in gemma_response.recommendations:
                st.write(f"- {rec}")
        else:
            st.info("Verify data inputs and click 'Run Triage' to trigger local Gemma compliance analysis.")

    # Tab 5: Raw OCR Text
    with tab_raw_ocr:
        if st.session_state.ocr_text:
            st.subheader("Raw Document OCR Extraction Stream")
            st.text_area("OCR Raw Stream", value=st.session_state.ocr_text, height=350)
        else:
            st.info("No document OCR text stream has been captured.")
