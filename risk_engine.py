"""
ComplianceCore AI Risk Engine.
Aggregates deterministic rule findings, computes a numerical risk score (0-100),
determines risk level and triage priority. Returns a typed RiskAssessment dataclass.
Does NOT run any LLM calls.
"""

import logging
from typing import List

import config
from models import RuleFinding, RiskAssessment

logger = logging.getLogger("ComplianceCore.RiskEngine")

def evaluate_overall_risk(rule_findings: List[RuleFinding]) -> RiskAssessment:
    """
    Computes numerical risk score, aggregates failed rule summaries, and determines
    overall risk level, priority, and confidence.
    """
    # 1. Base Score calculation by summing weights of failed rules
    failed_rules = [f for f in rule_findings if f.status == "FAIL"]
    
    score_sum = 0.0
    for finding in failed_rules:
        weight = config.RULE_RISK_WEIGHTS.get(finding.rule_id, 10.0)
        score_sum += weight
        
    # Cap risk score at 100.0
    risk_score = min(score_sum, 100.0)

    # 2. Extract findings summary list
    findings_summary = []
    for f in failed_rules:
        findings_summary.append(f"{f.rule_name} failed: {f.findings} (Severity: {f.severity})")

    # If no rules failed, report clean
    if not failed_rules:
        findings_summary.append("All deterministic compliance rules passed successfully.")

    # 3. Determine Risk Level, Priority and Check for Critical rules
    # Check if there is any critical rule failure
    has_critical_failure = any(f.severity == "Critical" for f in failed_rules)
    has_high_failure = any(f.severity == "High" for f in failed_rules)

    if has_critical_failure or risk_score >= 80.0:
        risk_level = "Critical"
        priority = "Immediate"
    elif has_high_failure or risk_score >= 50.0:
        risk_level = "High"
        priority = "High"
    elif risk_score >= 20.0:
        risk_level = "Medium"
        priority = "Medium"
    else:
        risk_level = "Low"
        priority = "Low"

    # 4. Average confidence calculation across all executed rules
    if rule_findings:
        avg_confidence = sum(f.confidence for f in rule_findings) / len(rule_findings)
    else:
        avg_confidence = 1.0

    assessment = RiskAssessment(
        risk_score=float(round(risk_score, 2)),
        risk_level=risk_level,
        priority=priority,
        confidence=float(round(avg_confidence, 2)),
        findings_summary=findings_summary
    )
    
    logger.info(
        f"Calculated Risk Score: {assessment.risk_score}, "
        f"Risk Level: {assessment.risk_level}, "
        f"Priority: {assessment.priority}"
    )
    return assessment
