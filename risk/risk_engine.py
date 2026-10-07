def evaluate_risk(extracted_info: dict) -> dict:
    """
    Detect incomplete information, uncertainty, and predefined high-risk indicators.
    Never claim that the patient has a disease.
    """
    risk_result = {
        "is_high_risk": False,
        "uncertainty_flag": False,
        "reasons": []
    }
    
    if not extracted_info:
        risk_result["uncertainty_flag"] = True
        risk_result["reasons"].append("No information provided.")
        return risk_result
        
    symptoms = extracted_info.get("symptoms", [])
    high_risk_keywords = ["chest pain", "difficulty breathing", "severe bleeding"]
    
    for symptom in symptoms:
        if symptom.lower() in high_risk_keywords:
            risk_result["is_high_risk"] = True
            risk_result["reasons"].append(f"High risk symptom detected: {symptom}")
            
    if not symptoms and not extracted_info.get("medications"):
        risk_result["uncertainty_flag"] = True
        risk_result["reasons"].append("Incomplete medical information.")
        
    return risk_result
