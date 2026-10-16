"""
SQLite Database Layer for MediGuide-AI.
Provides persistent storage for reports, clinical review requests, decisions,
user accounts, and audit logging.

Preserves SQLite schema integrity across application restarts with full ACID transactions.
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

DB_PATH = os.environ.get("MEDIGUIDE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "mediguide.db"))
DB_PATH = os.path.abspath(DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    """Create and return a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash a password using salted PBKDF2-HMAC-SHA256 (100,000 iterations)."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return dk.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a plain password against stored salt and hash."""
    dk, _ = _hash_password(password, salt)
    return secrets.compare_digest(dk, password_hash)


def init_db() -> None:
    """Initialize database tables and seed baseline accounts and cases if empty."""
    conn = get_db_connection()
    try:
        with conn:
            # 1. Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('patient', 'doctor', 'admin')),
                    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Suspended')),
                    specialty TEXT,
                    license TEXT,
                    hospital TEXT,
                    preferred_language TEXT DEFAULT 'en',
                    created_at TEXT NOT NULL
                );
            """)

            # 2. Reports table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    extracted_text TEXT NOT NULL,
                    extracted_info_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    risk_assessment_json TEXT NOT NULL,
                    guidance_json TEXT NOT NULL,
                    disclaimer TEXT NOT NULL,
                    timings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """)

            # 3. Clinical review requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_requests (
                    id TEXT PRIMARY KEY,
                    report_id TEXT,
                    patient_id TEXT NOT NULL,
                    risk_level TEXT NOT NULL CHECK(risk_level IN ('HIGH', 'UNCERTAIN', 'LOW')),
                    escalation_reasons_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    extracted_data_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PENDING_REVIEW', 'COMPLETED')),
                    decision TEXT,
                    review_notes TEXT,
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    created_at TEXT NOT NULL
                );
            """)

            # 4. Audit logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_id TEXT,
                    details_json TEXT
                );
            """)

            # Backward-compatible migration: ensure preferred_language column exists
            cursor = conn.execute("PRAGMA table_info(users);")
            cols = [r["name"] for r in cursor.fetchall()]
            if "preferred_language" not in cols:
                conn.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'en';")

            # Seed default users if users table is empty
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM users;")
            if cursor.fetchone()["cnt"] == 0:
                now_iso = datetime.now(timezone.utc).isoformat()
                seed_users = [
                    ("1", "Alex Morgan", "alex@example.com", "patient123", "patient", "Active", None, None, None),
                    ("2", "Dr. Sarah Wilson", "sarah@example.com", "doctor123", "doctor", "Active", "Cardiology", "MED-NY-849201", "Metropolitan Health Center"),
                    ("3", "System Administrator", "admin@example.com", "admin123", "admin", "Active", None, None, None),
                    ("4", "Maria Gonzalez", "maria@example.com", "patient123", "patient", "Active", None, None, None),
                    ("5", "Dr. Marcus Vance", "marcus.vance@clinic.org", "doctor123", "doctor", "Active", "General Practice", "MED-CA-920412", "Pacific Wellness Clinic"),
                ]
                for uid, name, email, pwd, role, status, spec, lic, hosp in seed_users:
                    pwd_hash, salt = _hash_password(pwd)
                    conn.execute("""
                        INSERT INTO users (id, name, email, password_hash, salt, role, status, specialty, license, hospital, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (uid, name, email, pwd_hash, salt, role, status, spec, lic, hosp, now_iso))

            # Seed baseline clinical review cases if empty
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM review_requests;")
            if cursor.fetchone()["cnt"] == 0:
                seed_cases = [
                    (
                        "MG-1024",
                        None,
                        "PT-8821 (Anonymized)",
                        "HIGH",
                        json.dumps(["Reported severe chest pain and shortness of breath."]),
                        "Patient reports severe chest pain and shortness of breath for 4 hours. Taking Aspirin 81mg. Blood pressure elevated at 145/95 mmHg.",
                        json.dumps({
                            "symptoms": ["chest pain", "shortness of breath"],
                            "medications": ["aspirin"],
                            "test_names": ["blood pressure"],
                            "test_values": ["145/95"],
                            "units": ["mmhg"],
                            "dates": ["15 October 2026"],
                            "observations": ["Patient reports severe chest pain and shortness of breath."],
                        }),
                        "PENDING_REVIEW",
                        None,
                        None,
                        None,
                        None,
                        "2026-10-15T09:30:00Z"
                    ),
                    (
                        "MG-1025",
                        None,
                        "PT-3419 (Anonymized)",
                        "HIGH",
                        json.dumps(["Extremely elevated blood pressure (180/110 mmHg)."]),
                        "Routine vitals recorded blood pressure of 180/110 mmHg with accompanying occipital headache. No prior antihypertensive medications reported.",
                        json.dumps({
                            "symptoms": ["headache"],
                            "medications": [],
                            "test_names": ["blood pressure"],
                            "test_values": ["180/110"],
                            "units": ["mmhg"],
                            "dates": ["15 October 2026"],
                            "observations": ["Severe occipital throbbing headache."],
                        }),
                        "PENDING_REVIEW",
                        None,
                        None,
                        None,
                        None,
                        "2026-10-15T10:15:00Z"
                    ),
                    (
                        "MG-1021",
                        None,
                        "PT-5512 (Anonymized)",
                        "UNCERTAIN",
                        json.dumps(["Uncertain medication interaction with OTC analgesics."]),
                        "Patient taking Warfarin along with high-dose Ibuprofen. Elevated INR test value recorded.",
                        json.dumps({
                            "symptoms": ["bruising"],
                            "medications": ["warfarin", "ibuprofen"],
                            "test_names": ["inr"],
                            "test_values": ["3.8"],
                            "units": [],
                            "dates": ["14 October 2026"],
                            "observations": ["Minor bruising noticed on forearms."],
                        }),
                        "COMPLETED",
                        "Schedule urgent telehealth consult",
                        "Advising immediate cessation of NSAID (Ibuprofen) due to potentiating bleeding risk with Warfarin. Re-check INR in 48 hours.",
                        "Dr. Sarah Wilson, MD",
                        "2026-10-14T15:45:00Z",
                        "2026-10-14T14:20:00Z"
                    )
                ]
                for sc in seed_cases:
                    conn.execute("""
                        INSERT INTO review_requests (
                            id, report_id, patient_id, risk_level, escalation_reasons_json,
                            summary, extracted_data_json, status, decision, review_notes,
                            reviewed_by, reviewed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, sc)

            # Seed demo reports for user 1 (Alex Morgan) if reports table is empty
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM reports;")
            if cursor.fetchone()["cnt"] == 0:
                demo_reports = [
                    (
                        "101",
                        "1",
                        "Complete_Blood_Count.pdf",
                        "Complete Blood Count on 2026-10-12. Hemoglobin: 14.2 g/dL. Platelets: 250,000 /uL. White Blood Cells: 6.5 x10^3/uL. Normal ranges observed.",
                        json.dumps({
                            "symptoms": [],
                            "medications": [],
                            "test_names": ["hemoglobin", "platelets", "white blood cells"],
                            "test_values": ["14.2", "250000", "6.5"],
                            "units": ["g/dl", "/ul", "x10^3/ul"],
                            "dates": ["2026-10-12"],
                            "observations": ["Normal hematologic ranges observed."],
                        }),
                        "This is a summary of the provided document. Complete Blood Count recorded normal hematologic markers including Hemoglobin 14.2 g/dL. Not a diagnosis or clinical recommendation.",
                        json.dumps({"is_high_risk": False, "reasons": [], "uncertainty_flag": False}),
                        json.dumps(["Prepare questions for a doctor and bring relevant documents to your next consultation."]),
                        "This system does not diagnose conditions, prescribe medications, or replace professional clinical consultation.",
                        json.dumps({"ocr_seconds": 0.05, "ner_seconds": 0.4, "summarizer_seconds": 0.6, "risk_seconds": 0.01, "total_seconds": 1.06}),
                        "2026-10-12T10:00:00Z"
                    ),
                    (
                        "102",
                        "1",
                        "General_Health_Report.png",
                        "General Health Report. Date: 2026-11-05. Blood Pressure: 180/110 mmHg. Patient reports severe throbbing headache.",
                        json.dumps({
                            "symptoms": ["headache"],
                            "medications": [],
                            "test_names": ["blood pressure"],
                            "test_values": ["180/110"],
                            "units": ["mmhg"],
                            "dates": ["2026-11-05"],
                            "observations": ["Severe throbbing headache reported."],
                        }),
                        "This is a summary of the provided document. Blood pressure recorded at 180/110 mmHg with accompanying headache. Not a diagnosis or clinical recommendation.",
                        json.dumps({"is_high_risk": True, "reasons": ["Extremely elevated blood pressure (180/110 mmHg)."], "uncertainty_flag": False}),
                        json.dumps(["Please seek professional medical review based on the flagged information."]),
                        "This system does not diagnose conditions, prescribe medications, or replace professional clinical consultation.",
                        json.dumps({"ocr_seconds": 0.12, "ner_seconds": 0.35, "summarizer_seconds": 0.5, "risk_seconds": 0.01, "total_seconds": 0.98}),
                        "2026-11-05T14:30:00Z"
                    ),
                ]
                for r in demo_reports:
                    conn.execute("""
                        INSERT INTO reports (
                            id, user_id, filename, extracted_text, extracted_info_json,
                            summary, risk_assessment_json, guidance_json, disclaimer,
                            timings_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, r)
    finally:
        conn.close()


# Ensure DB tables are initialized
init_db()


# ==========================================
# Report Persistence Operations
# ==========================================

def save_report(
    report_id: str,
    user_id: str,
    filename: str,
    extracted_text: str,
    extracted_info: Dict[str, Any],
    summary: str,
    risk_assessment: Dict[str, Any],
    guidance: List[str],
    disclaimer: str,
    timings: Dict[str, Any],
) -> Dict[str, Any]:
    """Persist a newly analyzed medical report to SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO reports (
                    id, user_id, filename, extracted_text, extracted_info_json,
                    summary, risk_assessment_json, guidance_json, disclaimer,
                    timings_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    filename = excluded.filename,
                    extracted_text = excluded.extracted_text,
                    extracted_info_json = excluded.extracted_info_json,
                    summary = excluded.summary,
                    risk_assessment_json = excluded.risk_assessment_json,
                    guidance_json = excluded.guidance_json,
                    disclaimer = excluded.disclaimer,
                    timings_json = excluded.timings_json;
            """, (
                report_id,
                user_id,
                filename,
                extracted_text,
                json.dumps(extracted_info),
                summary,
                json.dumps(risk_assessment),
                json.dumps(guidance),
                disclaimer,
                json.dumps(timings),
                now_iso,
            ))
            log_audit(user_id=user_id, action="REPORT_CREATED", resource_id=report_id, conn=conn)
    finally:
        conn.close()

    return {
        "report_id": report_id,
        "id": report_id,
        "user_id": user_id,
        "filename": filename,
        "extracted_text": extracted_text,
        "extracted_info": extracted_info,
        "summary": summary,
        "risk_assessment": risk_assessment,
        "guidance": guidance,
        "disclaimer": disclaimer,
        "timings": timings,
        "created_at": now_iso,
    }


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single report record by ID."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM reports WHERE id = ?;", (report_id,)).fetchone()
        if not row:
            return None
        return _format_report_row(row)
    finally:
        conn.close()


def find_duplicate_report(user_id: str, filename: str, extracted_text: str) -> Optional[Dict[str, Any]]:
    """
    Find existing report for user with identical filename and extracted text
    to prevent creating duplicate reports on client retries or re-uploads.
    """
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE user_id = ? AND filename = ? AND extracted_text = ? ORDER BY created_at DESC LIMIT 1;",
            (str(user_id), filename, extracted_text)
        ).fetchone()
        if not row:
            return None
        return _format_report_row(row)
    finally:
        conn.close()



def get_reports_by_user(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all reports for a specific user, or all reports if user_id is None."""
    conn = get_db_connection()
    try:
        if user_id:
            rows = conn.execute(
                "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC;",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM reports ORDER BY created_at DESC;"
            ).fetchall()
        return [_format_report_row(r) for r in rows]
    finally:
        conn.close()


def _format_report_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database report row into a cleanly deserialized response dictionary."""
    return {
        "report_id": row["id"],
        "id": row["id"],
        "user_id": row["user_id"],
        "filename": row["filename"],
        "extracted_text": row["extracted_text"],
        "extracted_info": json.loads(row["extracted_info_json"]),
        "summary": row["summary"],
        "risk_assessment": json.loads(row["risk_assessment_json"]),
        "guidance": json.loads(row["guidance_json"]),
        "disclaimer": row["disclaimer"],
        "timings": json.loads(row["timings_json"]),
        "created_at": row["created_at"],
    }


# ==========================================
# Review Request Operations (Persistent)
# ==========================================

def insert_or_update_review_request(case_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Insert or update a human review request record."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO review_requests (
                    id, report_id, patient_id, risk_level, escalation_reasons_json,
                    summary, extracted_data_json, status, decision, review_notes,
                    reviewed_by, reviewed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    decision = excluded.decision,
                    review_notes = excluded.review_notes,
                    reviewed_by = excluded.reviewed_by,
                    reviewed_at = excluded.reviewed_at;
            """, (
                case_dict["id"],
                case_dict.get("report_id"),
                case_dict.get("patient_id", "Anonymized Patient"),
                case_dict.get("risk_level", "HIGH"),
                json.dumps(case_dict.get("escalation_reasons", [])),
                case_dict.get("summary", ""),
                json.dumps(case_dict.get("extracted_data", {})),
                case_dict.get("status", "PENDING_REVIEW"),
                case_dict.get("decision"),
                case_dict.get("review_notes"),
                case_dict.get("reviewed_by"),
                case_dict.get("reviewed_at"),
                case_dict.get("created_at", datetime.now(timezone.utc).isoformat()),
            ))
        return get_review_by_id(case_dict["id"])
    finally:
        conn.close()


def get_review_by_id(review_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single review request by ID from SQLite."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM review_requests WHERE id = ?;", (review_id,)).fetchone()
        if not row:
            return None
        return _format_review_row(row)
    finally:
        conn.close()


def query_review_requests(
    status: Optional[str] = None, risk_level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve review requests with optional status and risk filters, newest first."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM review_requests WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        query += " ORDER BY created_at DESC;"

        rows = conn.execute(query, params).fetchall()
        return [_format_review_row(r) for r in rows]
    finally:
        conn.close()


def submit_review_decision_db(
    review_id: str, decision: str, notes: str, reviewer_name: str
) -> Optional[Dict[str, Any]]:
    """Record physician review decision, notes, and timestamp with an audit entry."""
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute("""
                UPDATE review_requests
                SET status = 'COMPLETED',
                    decision = ?,
                    review_notes = ?,
                    reviewed_by = ?,
                    reviewed_at = ?
                WHERE id = ?;
            """, (decision, notes, reviewer_name, now_iso, review_id))
            if cur.rowcount == 0:
                return None
            log_audit(
                user_id=reviewer_name,
                action="REVIEW_DECISION_SUBMITTED",
                resource_id=review_id,
                details={"decision": decision},
                conn=conn,
            )
        return get_review_by_id(review_id)
    finally:
        conn.close()


def get_db_review_stats() -> Dict[str, int]:
    """Compute aggregate counts for the review queue."""
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM review_requests;").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) as c FROM review_requests WHERE status = 'PENDING_REVIEW';").fetchone()["c"]
        completed = conn.execute("SELECT COUNT(*) as c FROM review_requests WHERE status = 'COMPLETED';").fetchone()["c"]
        high_pri = conn.execute("SELECT COUNT(*) as c FROM review_requests WHERE status = 'PENDING_REVIEW' AND risk_level = 'HIGH';").fetchone()["c"]
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        reviewed_today = conn.execute(
            "SELECT COUNT(*) as c FROM review_requests WHERE status = 'COMPLETED' AND reviewed_at LIKE ?;",
            (f"{today_str}%",)
        ).fetchone()["c"]

        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "high_priority": high_pri,
            "reviewed_today": reviewed_today,
        }
    finally:
        conn.close()


def _format_review_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite row to standardized review dictionary."""
    return {
        "id": row["id"],
        "report_id": row["report_id"],
        "patient_id": row["patient_id"],
        "risk_level": row["risk_level"],
        "escalation_reasons": json.loads(row["escalation_reasons_json"]),
        "summary": row["summary"],
        "extracted_data": json.loads(row["extracted_data_json"]),
        "status": row["status"],
        "decision": row["decision"],
        "review_notes": row["review_notes"],
        "reviewed_by": row["reviewed_by"],
        "reviewed_at": row["reviewed_at"],
        "created_at": row["created_at"],
        "disclaimer": "FINAL CLINICAL DECISIONS BELONG TO A QUALIFIED HEALTHCARE PROFESSIONAL.",
    }


# ==========================================
# User & Authentication Operations
# ==========================================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by email address."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?);", (email.strip(),)).fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by ID."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def get_all_users() -> List[Dict[str, Any]]:
    """List all users (passwords and salts stripped for privacy)."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT id, name, email, role, status, specialty, license, hospital, preferred_language, created_at FROM users ORDER BY created_at DESC;").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_user(
    name: str,
    email: str,
    password: str,
    role: str = "patient",
    preferred_language: str = "en",
) -> Optional[Dict[str, Any]]:
    """Register a new user with salted hash and preferred language."""
    now_iso = datetime.now(timezone.utc).isoformat()
    pwd_hash, salt = _hash_password(password)
    user_id = f"USR-{secrets.token_hex(4).upper()}"
    pref_lang = preferred_language if preferred_language in ("en", "ta", "hi", "te", "ml", "kn") else "en"

    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO users (id, name, email, password_hash, salt, role, status, preferred_language, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'Active', ?, ?);
            """, (user_id, name.strip(), email.strip().lower(), pwd_hash, salt, role, pref_lang, now_iso))
            log_audit(user_id=user_id, action="USER_REGISTERED", resource_id=user_id, conn=conn)
        return {
            "id": user_id,
            "name": name,
            "email": email.strip().lower(),
            "role": role,
            "status": "Active",
            "preferred_language": pref_lang,
            "created_at": now_iso,
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def update_user_status(user_id: str, new_status: str) -> bool:
    """Update user account status (Active or Suspended)."""
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute("UPDATE users SET status = ? WHERE id = ?;", (new_status, user_id))
            log_audit(user_id=user_id, action=f"USER_STATUS_{new_status.upper()}", resource_id=user_id, conn=conn)
            return cur.rowcount > 0
    finally:
        conn.close()


def update_user_language(user_id: str, new_language: str) -> bool:
    """Update user preferred language setting with audit tracking."""
    if new_language not in ("en", "ta", "hi", "te", "ml", "kn"):
        return False
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute("UPDATE users SET preferred_language = ? WHERE id = ?;", (new_language, user_id))
            log_audit(
                user_id=user_id,
                action="USER_LANGUAGE_UPDATED",
                resource_id=user_id,
                details={"preferred_language": new_language},
                conn=conn,
            )
            return cur.rowcount > 0
    finally:
        conn.close()


# ==========================================
# Audit Logging
# ==========================================

def log_audit(
    user_id: Optional[str],
    action: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Record an audit trail event without capturing PHI or sensitive document content."""
    now_iso = datetime.now(timezone.utc).isoformat()
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    try:
        conn.execute("""
            INSERT INTO audit_logs (timestamp, user_id, action, resource_id, details_json)
            VALUES (?, ?, ?, ?, ?);
        """, (now_iso, user_id, action, resource_id, json.dumps(details or {})))
        if should_close:
            conn.commit()
    except Exception:
        pass  # Never disrupt request flow if audit log fails
    finally:
        if should_close:
            conn.close()
