import requests
import json

# Replace with your teammate's actual IP
TEAMMATE_IP = "192.168.1.XX" 
URL = f"http://{TEAMMATE_IP}:11434/api/generate"

def get_compliance_report(document_text):
    system_prompt = """You are a Senior Financial Compliance Auditor. Analyze the provided text for risks.
    Check for: 1. Missing info, 2. Transactions > $5,000, 3. Logical inconsistencies.
    Output ONLY valid JSON: {"risk_status": "Low/Medium/High", "reasoning": "...", "source_quote": "..."}"""
    
    payload = {
        "model": "gemma",
        "prompt": f"{system_prompt}\n\nINPUT TEXT:\n{document_text}",
        "stream": False
    }
    
    try:
        response = requests.post(URL, json=payload)
        # Extract the JSON string from the response
        result_text = response.json()['response']
        # Clean up in case the model adds extra text
        return json.loads(result_text)
    except Exception as e:
        return {"risk_status": "Error", "reasoning": str(e)}