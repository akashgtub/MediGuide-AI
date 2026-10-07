def create_review_request(extracted_info: dict, summary: str, risk_result: dict) -> dict:
    """
    Create a structured human-review request.
    Include the relevant extracted information, summary, risk result, and reason for escalation.
    Clearly mark that final clinical decisions belong to a qualified healthcare professional.
    """
    request = {
        "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
        "escalation_reasons": risk_result.get("reasons", []),
        "risk_level": "HIGH" if risk_result.get("is_high_risk") else ("UNCERTAIN" if risk_result.get("uncertainty_flag") else "LOW"),
        "summary": summary,
        "extracted_data": extracted_info,
        "status": "PENDING_REVIEW"
    }
    return request
