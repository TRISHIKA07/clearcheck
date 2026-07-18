<div align="center">

# 🛡️ ComplianceCore AI

### AI-Powered Financial Compliance & Risk Triage Platform

**Built for Google's Build with Gemma — Bengaluru AI Sprint**

Runs 100% locally on **Gemma (via Ollama)** — no cloud, no external APIs, no data leaves your machine.

![Status](https://img.shields.io/badge/status-hackathon%20prototype-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Model](https://img.shields.io/badge/model-gemma4%3Ae4b-4285F4)
![License](https://img.shields.io/badge/license-MIT-green)
![Privacy](https://img.shields.io/badge/data-100%25%20local-brightgreen)

</div>

---

## 📑 Table of Contents

- [Introduction](#-introduction)
- [Problem Statement](#-problem-statement)
- [Our Solution](#-our-solution)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Running the App](#-running-the-app)
- [Project Structure](#-project-structure)
- [Future Scope](#-future-scope)
- [License](#-license)

---

## 📖 Introduction

**ComplianceCore AI** is an AI-powered compliance and risk triage platform built for FinTech and banking teams. It automatically reviews KYC documents and transaction records, flags inconsistencies, and produces audit-ready risk reports — combining deterministic rule checks with local AI reasoning powered by **Gemma**, running entirely offline through **Ollama**.

## ❗ Problem Statement

Compliance teams at banks and FinTechs are drowning in manual review work:

- Every onboarding document and transaction batch needs human eyes
- Alert fatigue leads to missed red flags
- Sending sensitive KYC data to cloud AI services creates serious privacy and regulatory risk
- Manual review doesn't scale with growing customer volume

## 💡 Our Solution

ComplianceCore AI automates the first pass of compliance review using a **two-layer intelligence model**:

1. **Deterministic rule engine** — fast, explainable, provable checks (missing fields, expired IDs, threshold breaches)
2. **Gemma AI reasoning layer** — interprets flagged findings the way a human analyst would, reducing false positives and adding context a rulebook alone can't catch

Because Gemma runs **locally via Ollama**, no document, ID, or transaction record ever leaves the institution's own infrastructure.

## ✨ Features

-  **Document Upload** — KYC documents, identity proofs, and transaction CSVs
-  **OCR Extraction** — reads scanned/image-based documents via Tesseract
-  **Compliance Rule Engine** — deterministic checks for missing, mismatched, or expired data
-  **Gemma-Powered Reasoning** — contextual risk interpretation, fully offline
-  **Risk Scoring** — Low / Medium / High classification per case
-  **Audit-Ready Reports** — downloadable PDF summaries with supporting evidence
-  **100% Local & Private** — no cloud calls, no external API keys, no data egress

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Dashboard | Streamlit |
| AI Runtime | Ollama (local) |
| AI Model | Gemma 4 — `gemma4:e4b` |
| PDF Parsing | PyMuPDF |
| OCR | Tesseract OCR |
| Data Processing | Pandas |
| Visualization | Plotly |
| Report Generation | FPDF |
| Documentation | Markdown |

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/compliancecore-ai.git
cd compliancecore-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate it
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull the Gemma model via Ollama

```bash
ollama pull gemma4:e4b
```

> Make sure [Ollama](https://ollama.com) is installed on your system before running this step.

## 🚀 Running the App

### 1. Start the Ollama server

```bash
ollama serve
```

### 2. Launch the Streamlit dashboard

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## 📁 Project Structure

```
compliancecore-ai/
├── app.py                 # Streamlit entry point
├── ocr.py                 # OCR extraction (Tesseract)
├── parser.py               # Document field parsing
├── transactions.py        # Transaction CSV parsing
├── compliance.py          # Deterministic rule engine
├── risk_engine.py         # Risk scoring logic
├── ai.py                  # Gemma / Ollama integration
├── prompts.py              # Prompt templates for Gemma
├── report.py               # PDF report generation
├── config.py               # Configuration and constants
├── utils.py                 # Shared helper functions
├── requirements.txt
└── README.md
```

## 🔮 Future Scope

- AML (Anti-Money Laundering) pattern detection
- PEP (Politically Exposed Person) screening
- Sanctions list screening
- Real-time transaction monitoring
- Voice-based KYC
- Face verification
- Blockchain-based audit trails
- Multi-language document support
- Multi-bank / multi-tenant deployment
- Optional secure cloud deployment for enterprise scale

## 📄 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

<div align="center">
<sub>Built with 🧠 Gemma, running 100% locally — for Google's Build with Gemma, Bengaluru AI Sprint.</sub>
</div>
