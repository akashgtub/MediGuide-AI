"""
Deterministic Agent Tools for MediGuide-AI.
Provides narrowly-scoped, read-only tools for the patient assistant agent:
- tool_get_user_reports: Retrieve metadata for reports owned by the authenticated patient.
- tool_find_metric: Extract verified lab measurements, values, units, reference ranges, and dates.
- tool_get_report_summary: Retrieve verified clinical summary of an authorized report.
- tool_search_report_observations: Search extracted observations and findings without hallucination.

Safety Guarantees:
- Strict Patient Data Isolation: Every tool verifies ownership against the SQLite database.
- Never trust client-supplied user ID or report ID without database verification.
- Zero Hallucination: Never infer, calculate, or guess missing lab values or measurements.
- Non-Diagnostic: Only surfaces recorded report data.
"""

import re
import logging
from typing import Dict, List, Optional, Any

from backend.database import get_report_by_id, get_reports_by_user

logger = logging.getLogger("mediguide_agent_tools")

# Common clinical metric aliases to support patient phrasing
METRIC_ALIASES: Dict[str, List[str]] = {
    "hemoglobin": ["hemoglobin", "haemoglobin", "hb", "hgb", "ஹீமோகுளோபின்", "हीमोग्लोबिन", "హిమోగ్లోబిన్", "ഹീമോഗ്ലോബിൻ", "ಹಿಮೋಗ್ಲೋಬಿನ್"],
    "platelets": ["platelets", "platelet count", "platelet", "plt", "இரத்த தட்டணுக்கள்", "प्लेटलेट्स", "ప్లేట్‌లెట్స్", "പ്ലേറ്റ്‌ലെറ്റുകൾ", "ಪ್ಲೇಟ್‌ಲೆಟ್‌ಗಳು"],
    "white blood cells": ["white blood cells", "wbc", "leukocytes", "white blood cell count", "வெள்ளை இரத்த அணுக்கள்", "श्वेत रक्त कोशिकाएं", "తెల్ల రక్త కణాలు", "ശ്വേത രക്താണുക്കൾ", "ಬಿಳಿ ರಕ್ತ ಕಣಗಳು"],
    "blood pressure": ["blood pressure", "bp", "systolic", "diastolic", "இரத்த அழுத்தம்", "रक्तचाप", "రక్తపోటు", "രക്തസമ്മർദ്ദം", "ರಕ್ತದೊತ್ತಡ"],
    "glucose": ["glucose", "blood sugar", "sugar", "fasting glucose", "fbs", "rbs", "hba1c", "குளுக்கோஸ்", "ग्लूकोज", "గ్లూకోజ్", "ഗ്ലൂക്കോസ്", "ಗ್ಲೂಕೋಸ್"],
    "cholesterol": ["cholesterol", "lipid", "hdl", "ldl", "triglycerides", "கொலஸ்ட்ரால்", "कोलेस्ट्रॉल"],
    "inr": ["inr", "prothrombin", "pt/inr"],
    "creatinine": ["creatinine", "serum creatinine"],
}


def tool_get_user_reports(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve metadata for all reports belonging to the authenticated patient.
    Strictly isolated: queries only reports matching user_id.
    """
    if not user_id:
        return []

    reports = get_reports_by_user(user_id=str(user_id))
    metadata_list = []
    for r in reports:
        # Enforce server-side isolation check
        if str(r.get("user_id")) != str(user_id):
            continue

        ext_info = r.get("extracted_info", {})
        metadata_list.append({
            "report_id": r["id"],
            "filename": r.get("filename", "Report"),
            "created_at": r.get("created_at", ""),
            "summary_preview": (r.get("summary", "")[:140] + "...") if len(r.get("summary", "")) > 140 else r.get("summary", ""),
            "test_names": ext_info.get("test_names", []),
            "dates": ext_info.get("dates", []),
            "is_high_risk": r.get("risk_assessment", {}).get("is_high_risk", False),
        })

    return metadata_list


def tool_get_report_summary(user_id: str, report_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the verified clinical summary and guidance of an authorized report.
    Returns None if report does not exist or does not belong to user_id.
    """
    if not user_id or not report_id:
        return None

    report = get_report_by_id(report_id)
    if not report:
        return None

    # Strict isolation check
    if str(report.get("user_id")) != str(user_id):
        logger.warning("Unauthorized access attempt: user %s requested report %s owned by %s", user_id, report_id, report.get("user_id"))
        return None

    return {
        "report_id": report["id"],
        "filename": report.get("filename", "Report"),
        "created_at": report.get("created_at", ""),
        "summary": report.get("summary", ""),
        "guidance": report.get("guidance", []),
        "risk_assessment": report.get("risk_assessment", {}),
        "disclaimer": report.get("disclaimer", ""),
        "test_names": report.get("extracted_info", {}).get("test_names", []),
    }


def _match_metric_alias(query: str) -> Optional[str]:
    """Find standardized metric canonical name from free-form user query."""
    q_lower = query.lower()
    for canonical, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            if any(ord(c) > 127 for c in alias):
                if alias in q_lower:
                    return canonical
            elif re.search(r'\b' + re.escape(alias) + r'\b', q_lower):
                return canonical
    return None


def _extract_metric_from_report_record(report: Dict[str, Any], canonical_metric: str) -> Optional[Dict[str, Any]]:
    """Inspect structured extracted_info and raw extracted_text of a report for metric."""
    ext_info = report.get("extracted_info", {})
    test_names = [t.lower() for t in ext_info.get("test_names", [])]
    test_values = ext_info.get("test_values", [])
    units = ext_info.get("units", [])
    dates = ext_info.get("dates", [])
    raw_text = report.get("extracted_text", "")

    # 1. Match against parallel structured test_names and test_values arrays
    aliases = METRIC_ALIASES.get(canonical_metric, [canonical_metric])
    for idx, tname in enumerate(test_names):
        if any(alias in tname for alias in aliases):
            val = test_values[idx] if idx < len(test_values) else None
            unit = units[idx] if idx < len(units) else ""
            date_str = dates[0] if dates else report.get("created_at", "")[:10]
            if val is not None:
                return {
                    "found": True,
                    "metric": tname.title(),
                    "canonical_metric": canonical_metric,
                    "value": str(val),
                    "unit": unit,
                    "date": date_str,
                    "report_id": report["id"],
                    "filename": report.get("filename", "Report"),
                    "source": "structured_data"
                }

    # 2. Match against raw extracted_text with regex if not aligned in parallel arrays
    # e.g., "Hemoglobin: 14.2 g/dL", "Blood Pressure: 180/110 mmHg", "Platelets: 250,000 /uL"
    for alias in aliases:
        pattern = re.compile(
            rf'(?:{re.escape(alias)})[\s:]+([0-9]+(?:/[0-9]+)?(?:\.[0-9]+)?(?:,[0-9]+)?)\s*([a-zA-Z/%^0-9/]+)?',
            re.IGNORECASE
        )
        match = pattern.search(raw_text)
        if match:
            val = match.group(1).replace(",", "")
            unit = match.group(2) or (units[0] if units else "")
            date_str = dates[0] if dates else report.get("created_at", "")[:10]
            return {
                "found": True,
                "metric": alias.title(),
                "canonical_metric": canonical_metric,
                "value": val,
                "unit": unit,
                "date": date_str,
                "report_id": report["id"],
                "filename": report.get("filename", "Report"),
                "source": "extracted_text"
            }

    return None


def tool_find_metric(user_id: str, report_id: Optional[str], query: str) -> Dict[str, Any]:
    """
    Retrieve a matching recorded measurement, value, unit, and test date from authorized report data.
    Enforces server-side isolation: only accesses reports owned by user_id.
    Never hallucinates or guesses absent metrics.
    """
    if not user_id:
        return {
            "found": False,
            "error": "authentication_required",
            "message": "Authentication is required to look up your personal test results."
        }

    canonical_metric = _match_metric_alias(query)
    if not canonical_metric:
        # Check if the query itself is a raw test name
        canonical_metric = query.strip().lower()

    # Case A: Specific report requested
    if report_id:
        report = get_report_by_id(report_id)
        if not report or str(report.get("user_id")) != str(user_id):
            return {
                "found": False,
                "error": "unauthorized_or_not_found",
                "message": "The requested report was not found or you do not have permission to view it."
            }

        res = _extract_metric_from_report_record(report, canonical_metric)
        if res:
            return res

        return {
            "found": False,
            "metric": canonical_metric,
            "report_id": report_id,
            "filename": report.get("filename", "Report"),
            "available_tests": report.get("extracted_info", {}).get("test_names", []),
            "message": f"Could not find a recorded value for '{canonical_metric}' in report {report.get('filename')}."
        }

    # Case B: No report_id specified -> search across all authorized reports of this user
    user_reports = get_reports_by_user(user_id=str(user_id))
    if not user_reports:
        return {
            "found": False,
            "error": "no_reports",
            "message": "You do not have any uploaded medical reports in your account. Please upload a report to inspect your values."
        }

    # Search each report
    for rep in user_reports:
        res = _extract_metric_from_report_record(rep, canonical_metric)
        if res:
            return res

    # Metric not found in any report
    all_tests = []
    for rep in user_reports:
        all_tests.extend(rep.get("extracted_info", {}).get("test_names", []))

    return {
        "found": False,
        "metric": canonical_metric,
        "searched_reports_count": len(user_reports),
        "available_tests": sorted(list(set(all_tests))),
        "message": f"Could not find a recorded value for '{canonical_metric}' across your {len(user_reports)} uploaded reports."
    }


def tool_search_report_observations(user_id: str, report_id: Optional[str], query: str) -> Dict[str, Any]:
    """
    Search available extracted clinical findings and observations without inventing missing values.
    Enforces patient data isolation.
    """
    if not user_id:
        return {
            "found": False,
            "error": "authentication_required",
            "message": "Authentication required."
        }

    reports_to_search = []
    if report_id:
        rep = get_report_by_id(report_id)
        if not rep or str(rep.get("user_id")) != str(user_id):
            return {"found": False, "error": "unauthorized_or_not_found"}
        reports_to_search.append(rep)
    else:
        reports_to_search = get_reports_by_user(user_id=str(user_id))

    if not reports_to_search:
        return {
            "found": False,
            "error": "no_reports",
            "message": "No reports found."
        }

    q_lower = query.lower()
    matches = []
    for r in reports_to_search:
        obs = r.get("extracted_info", {}).get("observations", [])
        for o in obs:
            if any(word in o.lower() for word in q_lower.split() if len(word) > 3):
                matches.append({
                    "observation": o,
                    "report_id": r["id"],
                    "filename": r.get("filename", "Report"),
                    "date": r.get("extracted_info", {}).get("dates", [""])[0] or r.get("created_at", "")[:10]
                })

    return {
        "found": len(matches) > 0,
        "matches": matches,
        "searched_reports_count": len(reports_to_search)
    }
