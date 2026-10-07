def extract_medical_info(text: str) -> dict:
    """
    Extract structured medical information from text.
    Do NOT diagnose.
    Handle missing information safely.
    """
    result = {
        "patient_info": {},
        "symptoms": [],
        "medications": [],
        "test_results": []
    }
    
    if not text:
        return result
        
    text_lower = text.lower()
    
    symptoms_list = ["fever", "headache", "chest pain", "difficulty breathing", "severe bleeding"]
    medications_list = ["aspirin"]
    
    for sym in symptoms_list:
        if sym in text_lower:
            result["symptoms"].append(sym)
            
    for med in medications_list:
        if med in text_lower:
            result["medications"].append(med)
            
    return result
