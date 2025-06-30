import pdfplumber
import re

def extract_lab_results(pdf_path):
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    patterns = {
        "hemoglobin": r"Hemoglobin\s*[:\-]?\s*([\d,\.]+)",
        "glucose": r"Glukoz\s*[:\-]?\s*([\d,\.]+)",
        "creatinine": r"Kreatinin\s*[:\-]?\s*([\d,\.]+)",
        "uric_acid": r"Ürik Asit\s*[:\-]?\s*([\d,\.]+)",
        "sodium": r"Sodyum\s*[:\-]?\s*([\d,\.]+)",
        "potassium": r"Potasyum\s*[:\-]?\s*([\d,\.]+)",
        "urine_ph": r"Ýdrar pH\s*[:\-]?\s*([\d,\.]+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '.')
            try:
                results[key] = float(value)
            except ValueError:
                results[key] = None
        else:
            results[key] = None
    return results
