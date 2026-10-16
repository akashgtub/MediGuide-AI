import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from backend.database import (
    insert_or_update_review_request,
    get_review_by_id,
    query_review_requests,
    submit_review_decision_db,
    get_db_review_stats,
)


def create_review_request(
    extracted_info: dict,
    summary: str,
    risk_result: dict,
    patient_id: Optional[str] = None,
    report_id: Optional[str] = None,
) -> dict:
    """
    Create a structured human-review request and persist it to SQLite.
    Include the relevant extracted information, summary, risk result, and reason for escalation.
    Clearly mark that final clinical decisions belong to a qualified healthcare professional.
    Prevents duplicate pending escalation tickets for the same patient and reasons.
    """
    reasons = risk_result.get("reasons", [])

    # Check for existing identical pending escalation to prevent ticket flooding
    if patient_id:
        try:
            pending_cases = query_review_requests(status="PENDING_REVIEW")
            for c in pending_cases:
                if str(c.get("patient_id")) == str(patient_id):
                    if report_id and c.get("report_id") != report_id:
                        continue
                    if c.get("escalation_reasons") == reasons or (not reasons and c.get("summary") == summary):
                        return c
        except Exception:
            pass

    req_id = f"MG-{str(uuid.uuid4())[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    resolved_patient_id = str(patient_id) if patient_id else f"PT-{str(uuid.uuid4())[:4].upper()} (Anonymized)"

    request = {
        "id": req_id,
        "patient_id": resolved_patient_id,
        "report_id": report_id,
        "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
        "escalation_reasons": reasons,
        "risk_level": "HIGH" if risk_result.get("is_high_risk") else ("UNCERTAIN" if risk_result.get("uncertainty_flag") else "LOW"),
        "summary": summary,
        "extracted_data": extracted_info,
        "status": "PENDING_REVIEW",
        "created_at": now_iso,
        "decision": None,
        "review_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
    }

    # Automatically persist to SQLite database
    insert_or_update_review_request(request)
    return request


def add_review_request(request: dict) -> dict:
    """Store an existing or newly constructed review request into SQLite."""
    req_id = request.get("id") or f"MG-{str(uuid.uuid4())[:8].upper()}"
    request["id"] = req_id
    if "created_at" not in request:
        request["created_at"] = datetime.now(timezone.utc).isoformat()
    insert_or_update_review_request(request)
    return request


def get_review_requests(
    status: Optional[str] = None, risk_level: Optional[str] = None
) -> List[dict]:
    """Retrieve all review requests matching optional status and risk filters from SQLite."""
    return query_review_requests(status=status, risk_level=risk_level)


def get_review_request_by_id(request_id: str) -> Optional[dict]:
    """Retrieve a single review request by its identifier from SQLite."""
    return get_review_by_id(request_id)


def submit_review_decision(
    request_id: str, decision: str, notes: str, reviewer_name: str = "Dr. Sarah Wilson"
) -> Optional[dict]:
    """
    Submit a healthcare professional's review decision and clinical notes.
    Transitions status to COMPLETED and records audit timestamp in SQLite.
    """
    return submit_review_decision_db(
        review_id=request_id,
        decision=decision,
        notes=notes,
        reviewer_name=reviewer_name,
    )


def get_review_stats() -> dict:
    """Return summary counts of pending, completed, and high priority reviews from SQLite."""
    return get_db_review_stats()
