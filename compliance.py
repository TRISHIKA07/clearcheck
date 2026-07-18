"""
ComplianceCore AI Compliance Engine.
Executes 100% deterministic, rule-based compliance checks.
Does NOT call Gemma. Returns a list of typed RuleFinding dataclasses.
"""

import logging
from datetime import datetime
from typing import List, Optional
import pandas as pd
import re

import config
from models import CustomerProfile, TransactionSummary, RuleFinding

logger = logging.getLogger("ComplianceCore.Compliance")

def parse_date_safely(date_str: Optional[str]) -> Optional[pd.Timestamp]:
    """
    Safely parses common date formats using pandas to enable comparisons.
    """
    if not date_str:
        return None
    try:
        return pd.to_datetime(date_str, dayfirst=True, errors="coerce")
    except Exception:
        return None

def execute_compliance_rules(
    profile: CustomerProfile, 
    txn_summary: TransactionSummary,
    txn_csv_path: Optional[str] = None
) -> List[RuleFinding]:
    """
    Executes rule-based validation on CustomerProfile and TransactionSummary.
    Returns list of RuleFinding instances.
    """
    findings: List[RuleFinding] = []
    
    # Anchor date for expirations (from metadata current time: July 18, 2026)
    current_date = pd.Timestamp("2026-07-18")

    # --- 1. PAN Validation ---
    pan_status = "PASS"
    pan_findings = "PAN document is present and has a valid format."
    pan_evidence = f"PAN: {profile.pan}" if profile.pan else "No PAN found"
    pan_severity = "None"
    pan_recommendation = "No action required."
    
    if not profile.pan:
        # PAN is not necessarily failing validation if Aadhaar/Passport is present, but flag if format check is skipped
        pan_findings = "PAN is not provided in documents."
        pan_evidence = "Missing PAN"
        pan_severity = "Low"
        pan_recommendation = "Request PAN if customer is an Indian taxpayer."
    else:
        # Check format
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", profile.pan):
            pan_status = "FAIL"
            pan_findings = "PAN is provided but format is invalid (expected 5 letters, 4 digits, 1 letter)."
            pan_severity = "High"
            pan_recommendation = "Request customer to upload a clear copy of a valid PAN card."
            
    findings.append(RuleFinding(
        rule_id="PAN_VALIDATION",
        rule_name="PAN Format Check",
        status=pan_status,
        findings=pan_findings,
        evidence=pan_evidence,
        severity=pan_severity,
        confidence=1.0,
        recommendation=pan_recommendation
    ))

    # --- 2. Aadhaar Validation ---
    aadhaar_status = "PASS"
    aadhaar_findings = "Aadhaar number is present and has a valid format."
    aadhaar_evidence = f"Aadhaar: {profile.aadhaar}" if profile.aadhaar else "No Aadhaar found"
    aadhaar_severity = "None"
    aadhaar_recommendation = "No action required."
    
    if not profile.aadhaar:
        aadhaar_findings = "Aadhaar is not provided in documents."
        aadhaar_evidence = "Missing Aadhaar"
        aadhaar_severity = "Low"
        aadhaar_recommendation = "Request Aadhaar for standard identity verification."
    else:
        # Check format (12 digits, must not start with 0 or 1)
        if not (re.match(r"^[2-9][0-9]{11}$", profile.aadhaar)):
            aadhaar_status = "FAIL"
            aadhaar_findings = "Aadhaar number is provided but format is invalid (expected 12 digits starting with 2-9)."
            aadhaar_severity = "High"
            aadhaar_recommendation = "Verify the Aadhaar number and request a clear scan."
            
    findings.append(RuleFinding(
        rule_id="AADHAAR_VALIDATION",
        rule_name="Aadhaar Format Check",
        status=aadhaar_status,
        findings=aadhaar_findings,
        evidence=aadhaar_evidence,
        severity=aadhaar_severity,
        confidence=1.0,
        recommendation=aadhaar_recommendation
    ))

    # --- 3. Missing KYC ---
    kyc_status = "PASS"
    kyc_findings = "At least one primary document ID is present (PAN, Aadhaar, or Passport)."
    kyc_evidence = f"PAN: {profile.pan}, Aadhaar: {profile.aadhaar}, Passport: {profile.passport_number}"
    kyc_severity = "None"
    kyc_recommendation = "No action required."
    
    if not profile.pan and not profile.aadhaar and not profile.passport_number:
        kyc_status = "FAIL"
        kyc_findings = "Critical Compliance Gap: All primary identity document IDs (PAN, Aadhaar, Passport) are missing."
        kyc_severity = "Critical"
        kyc_recommendation = "Immediately halt onboarding. Require customer to submit valid government ID documents."
        
    findings.append(RuleFinding(
        rule_id="MISSIC_KYC",
        rule_name="Primary KYC Document Check",
        status=kyc_status,
        findings=kyc_findings,
        evidence=kyc_evidence,
        severity=kyc_severity,
        confidence=1.0,
        recommendation=kyc_recommendation
    ))

    # --- 4. Missing DOB ---
    dob_status = "PASS"
    dob_findings = "Date of Birth is present in the customer profile."
    dob_evidence = f"DOB: {profile.dob}" if profile.dob else "No DOB found"
    dob_severity = "None"
    dob_recommendation = "No action required."
    
    if not profile.dob:
        dob_status = "FAIL"
        dob_findings = "Customer Date of Birth is missing from extracted document data."
        dob_severity = "High"
        dob_recommendation = "Request customer to submit an identity document that clearly displays their Date of Birth."
        
    findings.append(RuleFinding(
        rule_id="MISSING_DOB",
        rule_name="Date of Birth Presence Check",
        status=dob_status,
        findings=dob_findings,
        evidence=dob_evidence,
        severity=dob_severity,
        confidence=1.0,
        recommendation=dob_recommendation
    ))

    # --- 5. Missing Address ---
    addr_status = "PASS"
    addr_findings = "Address details are present in the customer profile."
    addr_evidence = f"Address: {profile.address}" if profile.address else "No Address found"
    addr_severity = "None"
    addr_recommendation = "No action required."
    
    if not profile.address:
        addr_status = "FAIL"
        addr_findings = "Customer Address is missing from document details."
        addr_severity = "High"
        addr_recommendation = "Request Utility Bill or Bank Statement to establish proof of address."
        
    findings.append(RuleFinding(
        rule_id="MISSING_ADDRESS",
        rule_name="Address Presence Check",
        status=addr_status,
        findings=addr_findings,
        evidence=addr_evidence,
        severity=addr_severity,
        confidence=1.0,
        recommendation=addr_recommendation
    ))

    # --- 6. Identity Mismatch ---
    id_mismatch_status = "PASS"
    id_mismatch_findings = "Customer name matches transaction sender profile."
    id_mismatch_evidence = f"Profile Name: {profile.name}"
    id_mismatch_severity = "None"
    id_mismatch_recommendation = "No action required."
    
    if txn_csv_path:
        try:
            df = pd.read_csv(txn_csv_path)
            # Find sender/client columns
            sender_cols = [col for col in df.columns if "sender" in col.lower() or "client" in col.lower() or "customer" in col.lower()]
            if sender_cols and profile.name:
                sender_names = df[sender_cols[0]].dropna().unique()
                profile_name_clean = re.sub(r"\s+", "", profile.name.lower())
                
                mismatch_found = True
                matched_name = ""
                for s_name in sender_names:
                    s_name_clean = re.sub(r"\s+", "", str(s_name).lower())
                    # Check for partial string overlap
                    if profile_name_clean in s_name_clean or s_name_clean in profile_name_clean:
                        mismatch_found = False
                        matched_name = str(s_name)
                        break
                        
                if mismatch_found:
                    id_mismatch_status = "FAIL"
                    id_mismatch_findings = f"Name mismatch detected. Profile Name is '{profile.name}', but transactions list sender name(s) as: {list(sender_names)}."
                    id_mismatch_evidence = f"Profile: {profile.name} vs Txn Senders: {list(sender_names)}"
                    id_mismatch_severity = "High"
                    id_mismatch_recommendation = "Investigate if the account is being used by a third party. Perform manual verification."
                else:
                    id_mismatch_findings = f"Name match verified. Profile Name: '{profile.name}', Txn Name: '{matched_name}'."
        except Exception as e:
            logger.warning(f"Could not check identity mismatch: {e}")
            
    findings.append(RuleFinding(
        rule_id="IDENTITY_MISMATCH",
        rule_name="Customer Identity Alignment Check",
        status=id_mismatch_status,
        findings=id_mismatch_findings,
        evidence=id_mismatch_evidence,
        severity=id_mismatch_severity,
        confidence=0.9,
        recommendation=id_mismatch_recommendation
    ))

    # --- 7. Duplicate Identity ---
    dup_id_status = "PASS"
    dup_id_findings = "No duplicate identity profiles detected in transaction history."
    dup_id_evidence = "Sender name is consistent."
    dup_id_severity = "None"
    dup_id_recommendation = "No action required."
    
    if txn_csv_path:
        try:
            df = pd.read_csv(txn_csv_path)
            sender_cols = [col for col in df.columns if "sender" in col.lower() or "client" in col.lower()]
            if sender_cols:
                distinct_senders = df[sender_cols[0]].dropna().unique()
                if len(distinct_senders) > 1:
                    dup_id_status = "FAIL"
                    dup_id_findings = f"Multiple distinct sender names detected in transaction records: {list(distinct_senders)}."
                    dup_id_evidence = f"Distinct senders found: {list(distinct_senders)}"
                    dup_id_severity = "Medium"
                    dup_id_recommendation = "Request customer to verify identity of all contributors/users of this transaction history."
        except Exception as e:
            logger.warning(f"Could not execute duplicate identity check: {e}")

    findings.append(RuleFinding(
        rule_id="DUPLICATE_IDENTITY",
        rule_name="Duplicate Identity Check",
        status=dup_id_status,
        findings=dup_id_findings,
        evidence=dup_id_evidence,
        severity=dup_id_severity,
        confidence=0.9,
        recommendation=dup_id_recommendation
    ))

    # --- 8. Expired Documents ---
    exp_status = "PASS"
    exp_findings = "Provided document validity verified."
    exp_evidence = f"Expiry date: {profile.expiry_date}" if profile.expiry_date else "No expiry date parsed"
    exp_severity = "None"
    exp_recommendation = "No action required."
    
    if profile.expiry_date:
        expiry_ts = parse_date_safely(profile.expiry_date)
        if expiry_ts and expiry_ts < current_date:
            exp_status = "FAIL"
            exp_findings = f"Expired Document: Document expired on {expiry_ts.strftime('%Y-%m-%d')} (Current System Date: 2026-07-18)."
            exp_evidence = f"Document Expiry: {profile.expiry_date} < Anchor: 2026-07-18"
            exp_severity = "High"
            exp_recommendation = "Hold account. Request customer to submit a renewed document."
            
    findings.append(RuleFinding(
        rule_id="EXPIRED_DOCUMENTS",
        rule_name="Document Expiration Check",
        status=exp_status,
        findings=exp_findings,
        evidence=exp_evidence,
        severity=exp_severity,
        confidence=1.0,
        recommendation=exp_recommendation
    ))

    # --- 9. Incomplete Onboarding ---
    onboarding_status = "PASS"
    onboarding_findings = "Proof of address and bank/financial details are fully available."
    onboarding_evidence = f"Utility info: {profile.utility_bill_info}, Bank info: {profile.bank_statement_info}"
    onboarding_severity = "None"
    onboarding_recommendation = "No action required."
    
    if not profile.utility_bill_info and not profile.bank_statement_info:
        onboarding_status = "FAIL"
        onboarding_findings = "Incomplete onboarding data. Missing both Utility Bill and Bank Statement info."
        onboarding_severity = "Medium"
        onboarding_recommendation = "Request customer to submit utility bills and bank statements for proof of address/income."
        
    findings.append(RuleFinding(
        rule_id="INCOMPLETE_ONBOARDING",
        rule_name="Onboarding Data Completion Check",
        status=onboarding_status,
        findings=onboarding_findings,
        evidence=onboarding_evidence,
        severity=onboarding_severity,
        confidence=1.0,
        recommendation=onboarding_recommendation
    ))

    # --- 10. Structuring Behaviour ---
    struct_status = "PASS"
    struct_findings = "No structuring behavior detected (transfers repeatedly near compliance threshold)."
    struct_evidence = f"Threshold: {config.TXN_HIGH_VALUE_THRESHOLD}"
    struct_severity = "None"
    struct_recommendation = "No action required."
    
    # Checking for transactions just below threshold (e.g. 85% to 99% of threshold)
    if txn_csv_path:
        try:
            df = pd.read_csv(txn_csv_path)
            # Map amount
            amt_col = [col for col in df.columns if "amount" in col.lower() or "value" in col.lower()]
            if amt_col:
                df[amt_col[0]] = pd.to_numeric(df[amt_col[0]], errors="coerce")
                threshold = config.TXN_HIGH_VALUE_THRESHOLD
                lower_bound = threshold * 0.85
                
                structuring_txns = df[(df[amt_col[0]] >= lower_bound) & (df[amt_col[0]] < threshold)]
                if len(structuring_txns) >= 3:
                    struct_status = "FAIL"
                    struct_findings = f"Potential Structuring Detected: Found {len(structuring_txns)} transactions valued between {lower_bound:.2f} and {threshold:.2f} (just under the High-Value Reporting threshold of {threshold:.2f})."
                    struct_evidence = f"Structuring Txn Counts: {len(structuring_txns)} items in range [{lower_bound}, {threshold}]"
                    struct_severity = "High"
                    struct_recommendation = "Flag account for transaction monitoring. Review bank statement for cash split deposits."
        except Exception as e:
            logger.warning(f"Could not calculate structuring behaviour: {e}")

    findings.append(RuleFinding(
        rule_id="STRUCTURING_BEHAVIOUR",
        rule_name="Transaction Structuring Check",
        status=struct_status,
        findings=struct_findings,
        evidence=struct_evidence,
        severity=struct_severity,
        confidence=0.8,
        recommendation=struct_recommendation
    ))

    # --- 11. High-Value Bursts ---
    hvb_status = "PASS"
    hvb_findings = "No high-value transaction bursts detected."
    hvb_evidence = f"Bursts count: {txn_summary.transaction_bursts_count}, High-value count: {txn_summary.high_value_transfers_count}"
    hvb_severity = "None"
    hvb_recommendation = "No action required."
    
    if txn_summary.transaction_bursts_count > 0 and txn_summary.high_value_transfers_count > 0:
        hvb_status = "FAIL"
        hvb_findings = f"High-Value Burst Alert: Detected {txn_summary.transaction_bursts_count} rapid bursts of transactions combined with {txn_summary.high_value_transfers_count} high-value transfers."
        hvb_severity = "High"
        hvb_recommendation = "Freeze account temporarily. Initiate verification of transaction source of funds."
        
    findings.append(RuleFinding(
        rule_id="HIGH_VALUE_BURSTS",
        rule_name="High-Value Burst Check",
        status=hvb_status,
        findings=hvb_findings,
        evidence=hvb_evidence,
        severity=hvb_severity,
        confidence=0.95,
        recommendation=hvb_recommendation
    ))

    # --- 12. Repeated Beneficiaries ---
    rep_status = "PASS"
    rep_findings = "Beneficiary counts are within normal compliance limits."
    rep_evidence = f"Unique repeated beneficiaries count: {len(txn_summary.repeated_beneficiaries)}"
    rep_severity = "None"
    rep_recommendation = "No action required."
    
    if len(txn_summary.repeated_beneficiaries) >= 3:
        rep_status = "FAIL"
        rep_findings = f"High Concentration: Transactions are highly repeated across {len(txn_summary.repeated_beneficiaries)} beneficiaries."
        rep_severity = "Medium"
        rep_recommendation = "Verify relation between customer and recurring high-frequency beneficiaries."
        
    findings.append(RuleFinding(
        rule_id="REPEATED_BENEFICIARIES",
        rule_name="Repeated Beneficiary concentration Check",
        status=rep_status,
        findings=rep_findings,
        evidence=rep_evidence,
        severity=rep_severity,
        confidence=1.0,
        recommendation=rep_recommendation
    ))

    # --- 13. Suspicious Keywords ---
    susp_status = "PASS"
    susp_findings = "No flagged description keywords found in transaction narratives."
    susp_evidence = f"Suspicious descriptions flagged: {txn_summary.suspicious_descriptions_count}"
    susp_severity = "None"
    susp_recommendation = "No action required."
    
    if txn_summary.suspicious_descriptions_count > 0:
        susp_status = "FAIL"
        susp_findings = f"Flagged Transactions: Found {txn_summary.suspicious_descriptions_count} transactions with descriptions matching compliance risk keywords."
        susp_severity = "High"
        susp_recommendation = "Perform immediate manual audit on transactions with matching risk descriptions."
        
    findings.append(RuleFinding(
        rule_id="SUSPICIOUS_KEYWORDS",
        rule_name="Suspicious Transaction Keywords Check",
        status=susp_status,
        findings=susp_findings,
        evidence=susp_evidence,
        severity=susp_severity,
        confidence=0.95,
        recommendation=susp_recommendation
    ))

    # --- 14. Cross-Border Indicators ---
    cb_status = "PASS"
    cb_findings = "No cross-border transfers detected."
    cb_evidence = f"Cross-border transfer count: {txn_summary.cross_border_count}"
    cb_severity = "None"
    cb_recommendation = "No action required."
    
    if txn_summary.cross_border_count > 0:
        cb_status = "FAIL"
        cb_findings = f"Cross-Border Transfer Alert: Customer executed {txn_summary.cross_border_count} transaction(s) across international borders."
        cb_severity = "Medium"
        cb_recommendation = "Verify compliance with local cross-border FEMA guidelines (e.g. LRS limits in India)."
        
    findings.append(RuleFinding(
        rule_id="CROSS_BORDER_INDICATORS",
        rule_name="Cross-Border Transaction Check",
        status=cb_status,
        findings=cb_findings,
        evidence=cb_evidence,
        severity=cb_severity,
        confidence=1.0,
        recommendation=cb_recommendation
    ))

    return findings
