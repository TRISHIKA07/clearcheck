"""
ComplianceCore AI Prompts Module.
Contains prompt builders for local Gemma. Prompts configure Gemma as a
Senior Financial Compliance Officer and enforce strict structured JSON output.
"""

import json
from typing import Tuple, List
from models import CustomerProfile, TransactionSummary, RuleFinding, RiskAssessment

# Shared system prompt setting the persona and forcing JSON output
SYSTEM_PERSONA = (
    "You are a Senior Financial Compliance Officer and Risk Analyst. "
    "Your duty is to review compliance evidence, identify regulatory risks, flag anomalies, "
    "and provide audit-quality risk assessments. "
    "You must analyze the inputs objectively. "
    "You must return your response in raw JSON format matching the specified schema. "
    "Do not include any preamble, conversational filler, markdown formatting (like ```json), or trailing commentary. "
    "Ensure all keys in the schema are present."
)

JSON_SCHEMA_INSTRUCTION = (
    "The output MUST be a valid JSON object matching the following structure:\n"
    "{\n"
    '  "executive_summary": "A concise, high-level summary of findings, risks, and reasoning.",\n'
    '  "compliance_decision": "APPROVED", "REJECTED", or "ESCALATED",\n'
    '  "evidence": "Bullet points listing key evidence, red flags, or validation passes.",\n'
    '  "severity": "Low", "Medium", "High", or "Critical",\n'
    '  "confidence": A float between 0.0 and 1.0 representing your confidence in this decision,\n'
    '  "audit_summary": "A detailed audit narrative summarizing regulatory adherence.",\n'
    '  "recommendations": ["A list of concrete next steps, e.g., Request additional documents, Block account, File SAR, etc."]\n'
    "}"
)

def build_identity_review_prompt(customer_profile: CustomerProfile) -> Tuple[str, str]:
    """
    Builds a prompt to ask Gemma to review customer profile data.
    """
    user_prompt = (
        f"Perform an identity and KYC compliance review for the following customer profile:\n\n"
        f"{json.dumps(customer_profile.to_dict(), indent=2)}\n\n"
        f"Analyze this customer profile for: expired documents, missing crucial fields, "
        f"inconsistent IDs, and risk factors (e.g. nationality/address mismatches).\n\n"
        f"{JSON_SCHEMA_INSTRUCTION}"
    )
    return SYSTEM_PERSONA, user_prompt

def build_transaction_review_prompt(transaction_summary: TransactionSummary) -> Tuple[str, str]:
    """
    Builds a prompt to ask Gemma to review transaction anomalies and statistics.
    """
    user_prompt = (
        f"Perform a transactional compliance review for the following transaction activity report:\n\n"
        f"{json.dumps(transaction_summary.to_dict(), indent=2)}\n\n"
        f"Analyze this report for: transaction bursts, high-value transfers, velocity spikes, "
        f"repeated round-number transfers, suspicious descriptions, and cross-border indicators.\n\n"
        f"{JSON_SCHEMA_INSTRUCTION}"
    )
    return SYSTEM_PERSONA, user_prompt

def build_compliance_prompt(
    customer_profile: CustomerProfile,
    transaction_summary: TransactionSummary,
    rule_findings: List[RuleFinding],
    risk_assessment: RiskAssessment
) -> Tuple[str, str]:
    """
    Builds a prompt that combines KYC profile, transaction statistics, rule engine alerts, 
    and preliminary risk calculations for Gemma to reason about.
    """
    findings_list = [f.to_dict() for f in rule_findings]
    
    user_prompt = (
        "Perform a comprehensive compliance and risk review.\n\n"
        "=== CUSTOMER PROFILE ===\n"
        f"{json.dumps(customer_profile.to_dict(), indent=2)}\n\n"
        "=== TRANSACTION SUMMARY ===\n"
        f"{json.dumps(transaction_summary.to_dict(), indent=2)}\n\n"
        "=== DETERMINISTIC COMPLIANCE RULE FINDINGS ===\n"
        f"{json.dumps(findings_list, indent=2)}\n\n"
        "=== PRELIMINARY RISK ASSESSMENT ===\n"
        f"{json.dumps(risk_assessment.to_dict(), indent=2)}\n\n"
        "Please provide your final regulatory audit decision, evidence, and recommendations.\n\n"
        f"{JSON_SCHEMA_INSTRUCTION}"
    )
    return SYSTEM_PERSONA, user_prompt

def build_executive_summary_prompt(
    customer_profile: CustomerProfile,
    transaction_summary: TransactionSummary,
    rule_findings: List[RuleFinding],
    risk_assessment: RiskAssessment
) -> Tuple[str, str]:
    """
    Builds a prompt focused specifically on writing a detailed executive summary narrative.
    """
    findings_list = [f.to_dict() for f in rule_findings]
    user_prompt = (
        "Draft a detailed executive summary for the compliance board based on these details:\n\n"
        f"Customer: {customer_profile.name}\n"
        f"Calculated Risk Level: {risk_assessment.risk_level} (Score: {risk_assessment.risk_score})\n"
        f"Total Transactions: {transaction_summary.total_transactions} with total volume {transaction_summary.total_volume}\n"
        f"Rules Failed: {[f['rule_name'] for f in findings_list if f['status'] == 'FAIL']}\n\n"
        f"Structure your response strictly into the requested JSON schema.\n\n"
        f"{JSON_SCHEMA_INSTRUCTION}"
    )
    return SYSTEM_PERSONA, user_prompt

def build_audit_prompt(
    customer_profile: CustomerProfile,
    transaction_summary: TransactionSummary,
    rule_findings: List[RuleFinding],
    risk_assessment: RiskAssessment
) -> Tuple[str, str]:
    """
    Builds a prompt specifically focused on generating a comprehensive regulatory audit summary report.
    """
    findings_list = [f.to_dict() for f in rule_findings]
    user_prompt = (
        "Generate a formal regulatory compliance audit report. Analyze the combination of KYC gaps and "
        "transaction patterns for structuring, money laundering indicators, and tax evasion risks.\n\n"
        f"Customer Data:\n{json.dumps(customer_profile.to_dict(), indent=2)}\n\n"
        f"Transaction Details:\n{json.dumps(transaction_summary.to_dict(), indent=2)}\n\n"
        f"Rule Alerts:\n{json.dumps(findings_list, indent=2)}\n\n"
        f"Risk Score:\n{json.dumps(risk_assessment.to_dict(), indent=2)}\n\n"
        f"{JSON_SCHEMA_INSTRUCTION}"
    )
    return SYSTEM_PERSONA, user_prompt
