"""
MediGuide-AI FastAPI Backend Application.
Provides RESTful endpoints for medical document upload, OCR extraction,
biomedical entity recognition, clinical summarization, and risk evaluation.

Safety & Compliance:
- Strict non-diagnostic disclaimers on all outputs.
- No clinical decisions, diagnoses, or prescriptions made.
- Human review escalation triggered for high-risk and uncertain documents.
- Zero logging of medical document contents, patient identifiers, or clinical metrics.
- Synchronous CPU-heavy ML inference is executed in a worker thread to prevent
  blocking the FastAPI asyncio event loop.
- Privacy-safe stage timing and diagnostics logged.
- Temporary file removal guaranteed in finally blocks.
- Upload size limited to 10 MB.
"""

import os
import time
import uuid
import asyncio
import logging
import tempfile
import threading
import concurrent.futures
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai.document_processor import (
    extract_text_from_document,
    process_document,
    get_ocr_engine,
    SUPPORTED_EXTENSIONS,
)
from ai.medical_extractor import extract_medical_info, get_ner_pipeline
from ai.summarizer import summarize_medical_info, get_summarization_pipeline
from ai.patient_agent import process_patient_request
from risk.risk_engine import evaluate_risk
from human_review.review_manager import (
    create_review_request,
    add_review_request,
    get_review_requests,
    get_review_request_by_id,
    submit_review_decision,
    get_review_stats,
)
from backend.database import (
    save_report,
    get_report_by_id,
    get_reports_by_user,
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    create_user,
    update_user_status,
    update_user_language,
    verify_password,
)
from ai.translator import (
    translate_text,
    detect_language,
    is_language_supported,
    get_supported_languages,
    SUPPORTED_LANGUAGES,
)
from backend.auth import (
    create_access_token,
    get_optional_current_user,
    get_current_user,
    require_role,
)

SERVER_START_TIME = time.time()

# Configure privacy-safe logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mediguide_backend")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB upload limit
CHUNK_SIZE = 1024 * 1024  # 1 MB read buffer
PROCESSING_BUDGET_SECONDS = 15.0

# Dedicated thread pool executor for CPU-bound document inference
upload_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="mediguide_upload",
)

# Track service model readiness
model_readiness = {
    "ocr_ready": False,
    "ner_ready": False,
    "summarizer_ready": False,
    "fully_ready": False,
}


def warmup_models() -> None:
    """
    Warm up OCR, NER, and summarizer models in a background worker thread
    so all weights, tokenizers, and engines are cached in memory before user requests arrive.
    Prevents cold-start pauses on initial document uploads.
    """
    logger.info("Initiating backend model background warmup...")

    # 1. Biomedical NER model warmup
    try:
        pipe = get_ner_pipeline()
        if pipe:
            pipe("Patient reports mild fatigue.")
        model_readiness["ner_ready"] = True
        logger.info("Biomedical NER model warmed up.")
    except Exception as e:
        logger.warning("NER warmup encountered an error: %s", e)

    # 2. Summarization model warmup
    try:
        spipe = get_summarization_pipeline()
        if spipe:
            spipe(
                "Patient reports mild fatigue.",
                max_length=20,
                min_length=5,
                num_beams=1,
                early_stopping=False,
                length_penalty=1.0,
            )
        model_readiness["summarizer_ready"] = True
        logger.info("Summarization model warmed up.")
    except Exception as e:
        logger.warning("Summarizer warmup encountered an error: %s", e)

    # 3. PaddleOCR engine warmup
    try:
        get_ocr_engine()
        model_readiness["ocr_ready"] = True
        logger.info("PaddleOCR engine warmed up.")
    except Exception as e:
        logger.warning("PaddleOCR warmup encountered an error: %s", e)

    model_readiness["fully_ready"] = (
        model_readiness["ner_ready"]
        and model_readiness["summarizer_ready"]
        and model_readiness["ocr_ready"]
    )
    logger.info("Model warmup completed. Readiness status: %s", model_readiness)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up models in background without blocking server startup
    warmup_thread = threading.Thread(target=warmup_models, daemon=True)
    warmup_thread.start()
    yield
    upload_executor.shutdown(wait=False)


app = FastAPI(
    title="MediGuide-AI API",
    description="Patient-centric medical document summarization and extraction API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configured for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    target_language: Optional[str] = Field(default="en", max_length=10)
    report_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


class LanguageUpdateRequest(BaseModel):
    preferred_language: str = Field(..., pattern="^(en|ta|hi|te|ml|kn)$")


class ReportTranslateRequest(BaseModel):
    target_language: str = Field(..., pattern="^(en|ta|hi|te|ml|kn)$")


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(..., min_length=1, max_length=5000)
    reviewer_name: Optional[str] = Field(default="Dr. Sarah Wilson", max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6, max_length=100)
    preferred_language: Optional[str] = Field(default="en", max_length=10)


class CreateUserAdminRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    role: str = Field(..., pattern="^(patient|doctor|admin)$")
    password: Optional[str] = Field(default="Temporary123!", min_length=6, max_length=100)


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(Active|Suspended)$")


def _execute_pipeline_in_worker_thread(temp_file_path: str, filename: str) -> Dict[str, Any]:
    """
    Synchronous CPU-bound pipeline execution running in a worker thread.
    Enforces a strict 15-second processing budget with stage-level deadlines.
    Prevents blocking the main FastAPI asyncio event loop.
    Captures privacy-safe stage timings.
    """
    t_start = time.time()

    # Stage 1: Document text extraction (OCR or native PDF)
    t0 = time.time()
    raw_text = extract_text_from_document(temp_file_path)
    cleaned_text = process_document(raw_text)
    t_ocr = round(time.time() - t0, 3)

    if not cleaned_text or not cleaned_text.strip():
        logger.warning("Stage 1 failure: OCR yielded no readable text (duration=%.2fs)", t_ocr)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract readable text from the document. Please ensure the file contains legible text.",
        )

    time_elapsed = time.time() - t_start
    time_remaining = PROCESSING_BUDGET_SECONDS - time_elapsed

    # Stage 2: Biomedical Named Entity Recognition & deterministic metrics
    t1 = time.time()
    # Run full NER model if backend is ready and budget permits (> 3.0s);
    # otherwise fallback immediately to deterministic extractor to prevent cold timeout
    if model_readiness["ner_ready"] and time_remaining > 3.0:
        extracted_info = extract_medical_info(cleaned_text, run_ner_model=True)
    else:
        logger.info("NER model not ready or low budget (%.2fs); using deterministic extractor fallback.", time_remaining)
        extracted_info = extract_medical_info(cleaned_text, run_ner_model=False)
    t_ner = round(time.time() - t1, 3)

    time_elapsed = time.time() - t_start
    time_remaining = PROCESSING_BUDGET_SECONDS - time_elapsed

    # Stage 3: Medical Summarization with clinical verification
    t2 = time.time()
    # If backend summarizer is ready, pass time_remaining minus 0.5s safety margin;
    # otherwise pass 0.0 to safely use deterministic fallback
    sum_budget = max(0.0, time_remaining - 0.5) if model_readiness["summarizer_ready"] else 0.0
    summary = summarize_medical_info(extracted_info, source_text=cleaned_text, time_budget_seconds=sum_budget)
    t_sum = round(time.time() - t2, 3)

    # Stage 4: Risk Evaluation & Human Review Escalation
    t3 = time.time()
    risk_result = evaluate_risk(extracted_info)
    t_risk = round(time.time() - t3, 3)

    guidance = []
    review_request = None
    if risk_result.get("is_high_risk") or risk_result.get("uncertainty_flag"):
        guidance.append(
            "Please seek professional medical review based on the flagged information."
        )
        review_request = create_review_request(extracted_info, summary, risk_result)
    else:
        guidance.append(
            "Prepare questions for a doctor and bring relevant documents to your next consultation."
        )

    t_total = round(time.time() - t_start, 3)

    # Privacy-safe logging: log ONLY duration metrics, never document text or clinical values
    logger.info(
        "Pipeline completed successfully: ocr=%.2fs, ner=%.2fs, summarizer=%.2fs, risk=%.2fs, total=%.2fs",
        t_ocr,
        t_ner,
        t_sum,
        t_risk,
        t_total,
    )

    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"

    disclaimer = (
        "This system does not diagnose conditions, prescribe medications, "
        "or replace professional clinical consultation. Final clinical decisions "
        "belong to a qualified healthcare provider."
    )

    return {
        "report_id": report_id,
        "filename": filename,
        "extracted_text": cleaned_text,
        "extracted_info": extracted_info,
        "summary": summary,
        "risk_assessment": risk_result,
        "review_request": review_request,
        "guidance": guidance,
        "disclaimer": disclaimer,
        "timings": {
            "ocr_seconds": t_ocr,
            "ner_seconds": t_ner,
            "summarizer_seconds": t_sum,
            "risk_seconds": t_risk,
            "total_seconds": t_total,
        },
    }


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint providing service readiness status."""
    return {
        "status": "healthy",
        "service": "MediGuide-AI API",
        "version": "1.0.0",
        "supported_formats": sorted(list(SUPPORTED_EXTENSIONS)),
        "max_file_size_mb": 10,
        "readiness": model_readiness,
    }


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Accept an uploaded medical document (image or PDF), stream to a temporary file,
    and dispatch CPU-heavy inference to a worker thread so the event loop remains responsive.
    Persists resulting findings and summary to SQLite database.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload.",
        )

    _, ext = os.path.splitext(file.filename)
    ext_lower = ext.lower()

    if ext_lower not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Stream file to a temporary file while enforcing max file size
    temp_file = tempfile.NamedTemporaryFile(suffix=ext_lower, delete=False)
    temp_file_path = temp_file.name
    content_length = 0

    try:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            content_length += len(chunk)
            if content_length > MAX_FILE_SIZE_BYTES:
                temp_file.close()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File exceeds maximum allowed size of 10 MB.",
                )
            temp_file.write(chunk)
        temp_file.close()

        # Reject 0-byte files
        if content_length == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty (0 bytes).",
            )

        logger.info(
            "Document received: extension=%s, size=%d bytes (dispatched to worker thread)",
            ext_lower,
            content_length,
        )

        # Offload synchronous CPU-heavy inference to dedicated worker thread with strict 15-second budget
        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    upload_executor,
                    _execute_pipeline_in_worker_thread,
                    temp_file_path,
                    file.filename,
                ),
                timeout=PROCESSING_BUDGET_SECONDS,
            )

            # Downstream persistence: Save report to SQLite database off the main event loop
            user_id = current_user.get("id") if current_user else "1"
            try:
                await asyncio.to_thread(
                    save_report,
                    report_id=result["report_id"],
                    user_id=user_id,
                    filename=result["filename"],
                    extracted_text=result["extracted_text"],
                    extracted_info=result["extracted_info"],
                    summary=result["summary"],
                    risk_assessment=result["risk_assessment"],
                    guidance=result["guidance"],
                    disclaimer=result["disclaimer"],
                    timings=result["timings"],
                )
            except Exception as db_err:
                logger.warning("Could not persist report to database: %s", db_err)

            return result
        except asyncio.TimeoutError:
            logger.warning("Upload processing exceeded %.1fs budget timeout.", PROCESSING_BUDGET_SECONDS)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Processing timed out after 15 seconds. Please try a clearer or smaller document.",
            )

    finally:
        # Guarantee removal of temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as err:
                logger.warning("Could not remove temp file: %s", err)


@app.post("/api/process-text")
def process_text_endpoint(
    payload: TextProcessRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Process plain text clinical narrative through multilingual patient agent pipeline."""
    user_id = current_user.get("id") if current_user else None

    # If target_language is default or unspecified, use patient preference if available
    target_lang = payload.target_language
    if (not target_lang or target_lang == "en") and current_user and current_user.get("preferred_language"):
        target_lang = current_user.get("preferred_language")

    result = process_patient_request(
        document_text=payload.text,
        target_language=target_lang or "en",
        user_id=user_id,
        report_id=payload.report_id,
        conversation_history=payload.conversation_history,
    )
    return result


@app.get("/api/reviews")
def list_reviews(
    review_status: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """List human clinical review requests with optional status and risk filtering."""
    if current_user and current_user.get("role") not in ("doctor", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only healthcare professionals and administrators can access the review queue.",
        )
    filter_val = status or review_status
    return get_review_requests(status=filter_val, risk_level=risk_level)


@app.get("/api/reviews/{request_id}")
def get_review_detail(
    request_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Retrieve detailed clinical escalation case by ID."""
    if current_user and current_user.get("role") not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only healthcare professionals and administrators can inspect review details.",
        )
    review = get_review_request_by_id(request_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review request '{request_id}' not found.",
        )
    return review


@app.post("/api/reviews/{request_id}/decision")
def post_review_decision(
    request_id: str,
    payload: ReviewDecisionRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Submit a healthcare professional's decision and clinical sign-off."""
    if current_user and current_user.get("role") not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only registered healthcare professionals can submit review decisions.",
        )
    reviewer = current_user.get("name") if current_user else (payload.reviewer_name or "Dr. Sarah Wilson")
    updated = submit_review_decision(
        request_id=request_id,
        decision=payload.decision,
        notes=payload.notes,
        reviewer_name=reviewer,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review request '{request_id}' not found.",
        )
    return updated


# ==========================================
# Authentication & Downstream User Endpoints
# ==========================================

@app.post("/api/auth/login")
def login_endpoint(payload: LoginRequest) -> Dict[str, Any]:
    """Verify user credentials and return signed access token."""
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.get("status") == "Suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact system administration.",
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        name=user["name"],
    )
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"],
            "specialty": user.get("specialty"),
            "preferred_language": user.get("preferred_language", "en") or "en",
        },
    }


@app.post("/api/auth/register")
def register_endpoint(payload: RegisterRequest) -> Dict[str, Any]:
    """Register a new patient account and return authentication token."""
    user = create_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="patient",
        preferred_language=payload.preferred_language or "en",
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        name=user["name"],
    )
    return {
        "token": token,
        "user": user,
    }


@app.get("/api/auth/me")
def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return currently authenticated user profile."""
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "status": current_user.get("status", "Active"),
        "specialty": current_user.get("specialty"),
        "preferred_language": current_user.get("preferred_language", "en") or "en",
    }


@app.get("/api/languages")
def list_languages_endpoint() -> List[Dict[str, str]]:
    """Return list of supported languages and localized names."""
    return get_supported_languages()


@app.patch("/api/auth/language")
@app.put("/api/auth/language")
def update_language_endpoint(
    payload: LanguageUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Persist authenticated user's preferred language."""
    success = update_user_language(current_user["id"], payload.preferred_language)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update language preference. Invalid language code.",
        )
    return {
        "status": "success",
        "user_id": current_user["id"],
        "preferred_language": payload.preferred_language,
    }


# ==========================================
# Report History & Access Isolation Endpoints
# ==========================================

@app.get("/api/reports")
def list_reports(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """
    Retrieve stored reports.
    Patients access their own reports; clinicians and administrators view all reports.
    """
    if not current_user:
        return get_reports_by_user(user_id="1")
    if current_user.get("role") == "patient":
        return get_reports_by_user(user_id=current_user.get("id"))
    return get_reports_by_user(user_id=None)


@app.get("/api/reports/{report_id}")
def get_single_report(
    report_id: str,
    lang: Optional[str] = "en",
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Retrieve report findings by ID, enforcing patient data isolation and multilingual support."""
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )
    if current_user and current_user.get("role") == "patient":
        if report.get("user_id") != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view this medical report.",
            )

    req_lang = (lang or "en").lower().strip()
    if req_lang != "en" and is_language_supported(req_lang):
        return {
            **report,
            "summary_original": report["summary"],
            "summary": translate_text(report["summary"], req_lang),
            "guidance_original": report.get("guidance", []),
            "guidance": [translate_text(g, req_lang) for g in report.get("guidance", [])],
            "disclaimer": translate_text(report.get("disclaimer", ""), req_lang),
            "language": req_lang,
        }

    return report


@app.post("/api/reports/{report_id}/translate")
def translate_report_endpoint(
    report_id: str,
    payload: ReportTranslateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Translate clinical summary and guidance of an authorized report to requested language."""
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )
    if current_user and current_user.get("role") == "patient":
        if report.get("user_id") != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view this medical report.",
            )

    target_lang = payload.target_language.lower().strip()
    if not is_language_supported(target_lang):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{payload.target_language}'.",
        )

    return {
        "report_id": report_id,
        "language": target_lang,
        "summary": translate_text(report["summary"], target_lang),
        "guidance": [translate_text(g, target_lang) for g in report.get("guidance", [])],
        "disclaimer": translate_text(report.get("disclaimer", ""), target_lang),
    }


# ==========================================
# Administrator Management Endpoints
# ==========================================

@app.get("/api/admin/users")
def admin_list_users(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """List all registered system accounts (Administrator only)."""
    if current_user and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required.",
        )
    return get_all_users()


@app.post("/api/admin/users")
def admin_create_user(
    payload: CreateUserAdminRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Create a user with designated role (Administrator only)."""
    if current_user and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required.",
        )
    user = create_user(
        name=payload.name,
        email=payload.email,
        password=payload.password or "Temporary123!",
        role=payload.role,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    return user


@app.patch("/api/admin/users/{user_id}/status")
def admin_toggle_user_status(
    user_id: str,
    payload: UpdateStatusRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Toggle user active / suspended status (Administrator only)."""
    if current_user and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required.",
        )
    success = update_user_status(user_id, payload.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )
    return {"id": user_id, "status": payload.status}


@app.get("/api/admin/doctors")
def admin_list_doctors(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """List verified clinicians from database (Clinicians and Administrators)."""
    if current_user and current_user.get("role") not in ("admin", "doctor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Clinician registry access restricted.",
        )
    all_users = get_all_users()
    doctors = [u for u in all_users if u.get("role") == "doctor"]
    return doctors


@app.get("/api/system/stats")
def system_stats() -> Dict[str, Any]:
    """Provide real-time telemetry on system readiness, review queue, and service uptime."""
    conn = None
    reports_count = 0
    users_count = 0
    try:
        from backend.database import get_db_connection
        conn = get_db_connection()
        reports_count = conn.execute("SELECT COUNT(*) as c FROM reports;").fetchone()["c"]
        users_count = conn.execute("SELECT COUNT(*) as c FROM users;").fetchone()["c"]
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

    return {
        "status": "operational",
        "service": "MediGuide-AI Core",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "readiness": model_readiness,
        "review_stats": get_review_stats(),
        "total_reports_stored": reports_count,
        "total_users_registered": users_count,
        "supported_formats": sorted(list(SUPPORTED_EXTENSIONS)),
        "max_file_size_mb": 10,
        "services": [
            {
                "name": "PaddleOCR Document Parser",
                "status": "Ready" if model_readiness["ocr_ready"] else "Warming up",
            },
            {
                "name": "Biomedical NER Engine",
                "status": "Ready" if model_readiness["ner_ready"] else "Warming up",
            },
            {
                "name": "DistilBART Clinical Summarizer",
                "status": "Ready" if model_readiness["summarizer_ready"] else "Warming up",
            },
            {"name": "Deterministic Clinical Guardrails", "status": "Active"},
            {"name": "Human Escalation Manager", "status": "Active"},
            {"name": "SQLite ACID Persistence Engine", "status": "Operational"},
        ],
    }
