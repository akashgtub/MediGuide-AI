def summarize_medical_info(extracted_info: dict) -> str:
    """
    Convert extracted information into a simple, patient-friendly summary.
    Do not provide diagnosis or treatment recommendations.
    """
    if not extracted_info:
        return "No information could be summarized."
        
    summary_parts = []
    summary_parts.append("This is a summary of the provided document. Please note this is not a diagnosis or clinical recommendation.")
    
    symptoms = extracted_info.get("symptoms", [])
    if symptoms:
        summary_parts.append(f"Reported symptoms: {', '.join(symptoms)}.")
    
    medications = extracted_info.get("medications", [])
    if medications:
        summary_parts.append(f"Mentioned medications: {', '.join(medications)}.")
        
    test_names = extracted_info.get("test_names", [])
    if test_names:
        summary_parts.append(f"Tests mentioned: {', '.join(test_names)}.")
        
    dates = extracted_info.get("dates", [])
    if dates:
        summary_parts.append(f"Dates found: {', '.join(dates)}.")
        
    obs = extracted_info.get("observations", [])
    if obs:
        summary_parts.append(f"Observations: {', '.join(obs)}.")
        
    if not any([symptoms, medications, test_names, dates, obs]):
        summary_parts.append("Information appears incomplete or no specific medical data was detected.")
        
    return " ".join(summary_parts)
