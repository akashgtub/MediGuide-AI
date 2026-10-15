import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# In-memory registry of human review requests
_review_store: Dict[str, Dict[str, Any]] = {}

def _seed_initial_cases():
    """Seed initial clinical cases so the clinician dashboard is populated out-of-the-box."""
    initial_cases = [
        {
            "id": "MG-1024",
            "patient_id": "PT-8821 (Anonymized)",
            "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
            "escalation_reasons": ["Reported severe chest pain and shortness of breath."],
            "risk_level": "HIGH",
            "summary": "Patient reports severe chest pain and shortness of breath for 4 hours. Taking Aspirin 81mg. Blood pressure elevated at 145/95 mmHg.",
            "extracted_data": {
                "symptoms": ["chest pain", "shortness of breath"],
                "medications": ["aspirin"],
                "test_names": ["blood pressure"],
                "test_values": ["145/95"],
                "units": ["mmhg"],
                "dates": ["15 October 2026"],
                "observations": ["Patient reports severe chest pain and shortness of breath."],
            },
            "status": "PENDING_REVIEW",
            "created_at": "2026-10-15T09:30:00Z",
            "decision": None,
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
        },
        {
            "id": "MG-1025",
            "patient_id": "PT-3419 (Anonymized)",
            "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
            "escalation_reasons": ["Extremely elevated blood pressure (180/110 mmHg)."],
            "risk_level": "HIGH",
            "summary": "Routine vitals recorded blood pressure of 180/110 mmHg with accompanying occipital headache. No prior antihypertensive medications reported.",
            "extracted_data": {
                "symptoms": ["headache"],
                "medications": [],
                "test_names": ["blood pressure"],
                "test_values": ["180/110"],
                "units": ["mmhg"],
                "dates": ["15 October 2026"],
                "observations": ["Severe occipital throbbing headache."],
            },
            "status": "PENDING_REVIEW",
            "created_at": "2026-10-15T10:15:00Z",
            "decision": None,
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
        },
        {
            "id": "MG-1021",
            "patient_id": "PT-5512 (Anonymized)",
            "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
            "escalation_reasons": ["Uncertain medication interaction with OTC analgesics."],
            "risk_level": "UNCERTAIN",
            "summary": "Patient taking Warfarin along with high-dose Ibuprofen. Elevated INR test value recorded.",
            "extracted_data": {
                "symptoms": ["bruising"],
                "medications": ["warfarin", "ibuprofen"],
                "test_names": ["inr"],
                "test_values": ["3.8"],
                "units": [],
                "dates": ["14 October 2026"],
                "observations": ["Minor bruising noticed on forearms."],
            },
            "status": "COMPLETED",
            "created_at": "2026-10-14T14:20:00Z",
            "decision": "Schedule urgent telehealth consult",
            "review_notes": "Advising immediate cessation of NSAID (Ibuprofen) due to potentiating bleeding risk with Warfarin. Re-check INR in 48 hours.",
            "reviewed_by": "Dr. Sarah Wilson, MD",
            "reviewed_at": "2026-10-14T15:45:00Z",
        },
    ]
    for case in initial_cases:
        _review_store[case["id"]] = case

# Initialize store with seed cases
_seed_initial_cases()


def create_review_request(extracted_info: dict, summary: str, risk_result: dict) -> dict:
    """
    Create a structured human-review request.
    Include the relevant extracted information, summary, risk result, and reason for escalation.
    Clearly mark that final clinical decisions belong to a qualified healthcare professional.
    """
    req_id = f"MG-{str(uuid.uuid4())[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    request = {
        "id": req_id,
        "patient_id": f"PT-{str(uuid.uuid4())[:4].upper()} (Anonymized)",
        "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
        "escalation_reasons": risk_result.get("reasons", []),
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

    # Automatically persist to registry
    _review_store[req_id] = request
    return request


def add_review_request(request: dict) -> dict:
    """Store an existing or newly constructed review request."""
    req_id = request.get("id") or f"MG-{str(uuid.uuid4())[:8].upper()}"
    request["id"] = req_id
    if "created_at" not in request:
        request["created_at"] = datetime.now(timezone.utc).isoformat()
    _review_store[req_id] = request
    return request


def get_review_requests(
    status: Optional[str] = None, risk_level: Optional[str] = None
) -> List[dict]:
    """Retrieve all review requests matching optional status and risk filters."""
    results = list(_review_store.values())
    if status:
        results = [r for r in results if r.get("status") == status]
    if risk_level:
        results = [r for r in results if r.get("risk_level") == risk_level]

    # Sort newest first
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


def get_review_request_by_id(request_id: str) -> Optional[dict]:
    """Retrieve a single review request by its identifier."""
    return _review_store.get(request_id)


def submit_review_decision(
    request_id: str, decision: str, notes: str, reviewer_name: str = "Dr. Sarah Wilson"
) -> Optional[dict]:
    """
    Submit a healthcare professional's review decision and clinical notes.
    Transitions status to COMPLETED and records audit timestamp.
    """
    req = _review_store.get(request_id)
    if not req:
        return None

    req["status"] = "COMPLETED"
    req["decision"] = decision
    req["review_notes"] = notes
    req["reviewed_by"] = reviewer_name
    req["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    return req


def get_review_stats() -> dict:
    """Return summary counts of pending, completed, and high priority reviews."""
    all_cases = list(_review_store.values())
    pending = [c for c in all_cases if c.get("status") == "PENDING_REVIEW"]
    completed = [c for c in all_cases if c.get("status") == "COMPLETED"]
    high_priority = [c for c in pending if c.get("risk_level") == "HIGH"]

    return {
        "total": len(all_cases),
        "pending": len(pending),
        "completed": len(completed),
        "high_priority": len(high_priority),
        "reviewed_today": len(
            [
                c
                for c in completed
                if c.get("reviewed_at", "").startswith(
                    datetime.now(timezone.utc).strftime("%Y-%m-%d")
                )
            ]
        ),
    }
