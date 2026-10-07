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
        
    if not symptoms and not medications:
        summary_parts.append("Information appears incomplete or no specific symptoms/medications were detected.")
        
    return " ".join(summary_parts)
