"""
ComplianceCore AI Transaction Analysis Module.
Performs deterministic pandas-based statistical and behavioral analysis on transaction CSV records.
Returns a typed TransactionSummary dataclass.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

import config
from utils import setup_logging, validate_file
from models import TransactionSummary

logger = logging.getLogger("ComplianceCore.Transactions")

REQUIRED_COLUMNS = {"transaction_id", "date", "amount", "beneficiary_name", "description", "country"}

def analyze_transaction_csv(file_path: Path) -> TransactionSummary:
    """
    Parses and analyzes the transaction CSV, performing schema validation,
    anomaly detection, statistical analysis, and velocity checks.
    """
    summary = TransactionSummary()
    
    if not validate_file(file_path, {"csv"}):
        summary.findings.append("Invalid transaction history file or file path.")
        summary.invalid_schema_count = 1
        return summary

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.exception(f"Failed to read CSV file {file_path}: {e}")
        summary.findings.append(f"Failed to read CSV: {e}")
        summary.invalid_schema_count = 1
        return summary

    # 1. Schema Validation
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    present_cols = set(df.columns)
    
    # Map synonyms if columns are slightly different
    column_mappings = {
        "txn_id": "transaction_id",
        "timestamp": "date",
        "datetime": "date",
        "value": "amount",
        "beneficiary": "beneficiary_name",
        "recipient": "beneficiary_name",
        "merchant": "beneficiary_name",
        "memo": "description",
        "purpose": "description",
        "country_code": "country"
    }
    
    for key, val in column_mappings.items():
        if key in present_cols and val not in present_cols:
            df.rename(columns={key: val}, inplace=True)
            present_cols = set(df.columns)

    missing_cols = REQUIRED_COLUMNS - present_cols
    if missing_cols:
        err_msg = f"Invalid CSV schema. Missing columns: {list(missing_cols)}"
        logger.error(err_msg)
        summary.findings.append(err_msg)
        summary.invalid_schema_count = len(missing_cols)
        return summary

    summary.total_transactions = len(df)
    if summary.total_transactions == 0:
        summary.findings.append("Transaction log is empty.")
        return summary

    # Clean amount and date fields
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # 2. Missing Fields Count
    missing_fields = df.isnull().sum().sum()
    summary.missing_fields_count = int(missing_fields)
    
    # Drop rows where critical amount or date is missing for stats, but record them
    corrupt_rows = df[df["amount"].isnull() | df["date"].isnull()]
    if not corrupt_rows.empty:
        summary.findings.append(f"Found {len(corrupt_rows)} rows with unparseable amounts or dates.")
        df = df.dropna(subset=["amount", "date"])
        
    if df.empty:
        summary.findings.append("No valid transactions remain after filtering unparseable date/amount fields.")
        return summary

    # Sort chronologically
    df = df.sort_values(by="date").reset_index(drop=True)

    # 3. Basic Stats
    summary.total_volume = float(df["amount"].sum())
    summary.average_amount = float(df["amount"].mean())
    summary.minimum_amount = float(df["amount"].min())
    summary.maximum_amount = float(df["amount"].max())

    # 4. Duplicate Transactions Check
    # (Same date, amount, beneficiary, and description)
    duplicates = df[df.duplicated(subset=["date", "amount", "beneficiary_name", "description"], keep=False)]
    summary.duplicate_transactions_count = len(duplicates)
    if summary.duplicate_transactions_count > 0:
        summary.findings.append(f"Flagged {summary.duplicate_transactions_count} duplicate transaction records.")

    # 5. High-Value Transfers
    high_val_df = df[df["amount"] > config.TXN_HIGH_VALUE_THRESHOLD]
    summary.high_value_transfers_count = len(high_val_df)
    for idx, row in high_val_df.iterrows():
        summary.findings.append(
            f"High-Value Transfer: Txn {row['transaction_id']} to {row['beneficiary_name']} "
            f"for amount {row['amount']} on {row['date'].strftime('%Y-%m-%d')}"
        )

    # 6. Repeated Beneficiary and Merchant Frequency
    merchant_counts = df["beneficiary_name"].value_counts().to_dict()
    summary.merchant_frequency = {str(k): int(v) for k, v in merchant_counts.items()}
    
    # Repeated Beneficiaries (>3 times)
    rep_beneficiaries = {str(k): int(v) for k, v in merchant_counts.items() if v > 3}
    summary.repeated_beneficiaries = rep_beneficiaries
    if rep_beneficiaries:
        summary.findings.append(f"Identified repeated transactions to beneficiaries: {list(rep_beneficiaries.keys())}")

    # 7. Cross-Border Transfers (not in "IN" / "India")
    df["country"] = df["country"].fillna("IN").astype(str).str.strip().str.upper()
    cross_border_df = df[~df["country"].isin(["IN", "INDIA"])]
    summary.cross_border_count = len(cross_border_df)
    for idx, row in cross_border_df.iterrows():
        summary.findings.append(
            f"Cross-Border Transfer: Txn {row['transaction_id']} sent to {row['country']} "
            f"({row['beneficiary_name']}) for amount {row['amount']}"
        )
        
    country_counts = df["country"].value_counts().to_dict()
    summary.country_summary = {str(k): int(v) for k, v in country_counts.items()}

    # 8. Daily Summary
    daily_df = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
    summary.daily_summary = {str(row["date"]): float(row["amount"]) for idx, row in daily_df.iterrows()}

    # 9. Velocity Violation Checks (Volume / Count spikes exceeding 3 std devs)
    daily_counts = df.groupby(df["date"].dt.date)["amount"].count()
    daily_vols = df.groupby(df["date"].dt.date)["amount"].sum()
    
    if len(daily_counts) >= 3:  # Need at least a few days to compute deviation
        mean_count, std_count = daily_counts.mean(), daily_counts.std()
        mean_vol, std_vol = daily_vols.mean(), daily_vols.std()
        
        # Avoid division by zero/NaN if std is 0
        std_count = std_count if std_count > 0 else 1.0
        std_vol = std_vol if std_vol > 0 else 1.0
        
        spike_days_count = daily_counts[daily_counts > (mean_count + config.TXN_VELOCITY_SPIKE_STD_DEV * std_count)]
        spike_days_vol = daily_vols[daily_vols > (mean_vol + config.TXN_VELOCITY_SPIKE_STD_DEV * std_vol)]
        
        velocity_flags = set(spike_days_count.index) | set(spike_days_vol.index)
        summary.velocity_violations_count = len(velocity_flags)
        
        for day in velocity_flags:
            summary.findings.append(
                f"Velocity Spike: Sudden spike in transaction activity on {day.strftime('%Y-%m-%d')}. "
                f"Volume: {daily_vols.get(day, 0.0)}, Count: {daily_counts.get(day, 0)}"
            )

    # 10. Transaction Bursts
    # (Detecting if window of config.TXN_BURST_WINDOW_MINUTES has more than config.TXN_BURST_COUNT_LIMIT txns)
    burst_count = 0
    if len(df) >= config.TXN_BURST_COUNT_LIMIT:
        window_td = pd.Timedelta(minutes=config.TXN_BURST_WINDOW_MINUTES)
        for i in range(len(df) - config.TXN_BURST_COUNT_LIMIT + 1):
            start_time = df.loc[i, "date"]
            end_time = start_time + window_td
            # Count how many txns fall in this window
            txns_in_window = df[(df["date"] >= start_time) & (df["date"] <= end_time)]
            if len(txns_in_window) >= config.TXN_BURST_COUNT_LIMIT:
                burst_count += 1
                summary.findings.append(
                    f"Transaction Burst: Found {len(txns_in_window)} transactions in a "
                    f"{config.TXN_BURST_WINDOW_MINUTES}-minute window starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                # Skip index to end of window to avoid spamming alerts for overlapping windows
                # (Simple heuristic to keep alerts readable)
                max_date_in_window = txns_in_window["date"].max()
                matching_indices = df[df["date"] == max_date_in_window].index
                if len(matching_indices) > 0:
                    i = matching_indices[0]
                    
    summary.transaction_bursts_count = burst_count

    # 11. Suspicious Descriptions Keywords
    suspicious_count = 0
    df["description"] = df["description"].fillna("").astype(str)
    for idx, row in df.iterrows():
        desc_lower = row["description"].lower()
        matched_kw = [kw for kw in config.SUSPICIOUS_DESCRIPTION_KEYWORDS if kw in desc_lower]
        if matched_kw:
            suspicious_count += 1
            summary.findings.append(
                f"Suspicious Description: Txn {row['transaction_id']} to {row['beneficiary_name']} "
                f"for amount {row['amount']} contains flagged terms: {matched_kw}"
            )
            
    summary.suspicious_descriptions_count = suspicious_count

    return summary
