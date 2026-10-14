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
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai.document_processor import (
    extract_text_from_document,
    process_document,
    SUPPORTED_EXTENSIONS,
)
from ai.medical_extractor import extract_medical_info
from ai.summarizer import summarize_medical_info
from ai.patient_agent import process_patient_request
from risk.risk_engine import evaluate_risk
from human_review.review_manager import create_review_request

# Configure privacy-safe logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mediguide_backend")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB upload limit
CHUNK_SIZE = 1024 * 1024  # 1 MB read buffer

app = FastAPI(
    title="MediGuide-AI API",
    description="Patient-centric medical document summarization and extraction API",
    version="1.0.0",
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
    target_language: str = Field(default="en", max_length=10)


def _execute_pipeline_in_worker_thread(temp_file_path: str, filename: str) -> Dict[str, Any]:
    """
    Synchronous CPU-bound pipeline execution running in a worker thread.
    Prevents blocking the main FastAPI asyncio event loop.
    Captures privacy-safe stage timings.
    """
    t_start = time.time()

    # Stage 1: Document OCR extraction
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

    # Stage 2: Biomedical Named Entity Recognition & deterministic metrics
    t1 = time.time()
    extracted_info = extract_medical_info(cleaned_text)
    t_ner = round(time.time() - t1, 3)

    # Stage 3: Medical Summarization with clinical verification
    t2 = time.time()
    summary = summarize_medical_info(extracted_info, source_text=cleaned_text)
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
    }


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept an uploaded medical document (image or PDF), stream to a temporary file,
    and dispatch CPU-heavy inference to a worker thread so the event loop remains responsive.
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

        # Offload synchronous CPU-heavy inference to a worker thread to keep the asyncio event loop free
        result = await asyncio.to_thread(
            _execute_pipeline_in_worker_thread, temp_file_path, file.filename
        )
        return result

    finally:
        # Guarantee removal of temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as err:
                logger.warning("Could not remove temp file: %s", err)


@app.post("/api/process-text")
def process_text_endpoint(payload: TextProcessRequest) -> Dict[str, Any]:
    """Process plain text clinical narrative through patient agent pipeline."""
    result = process_patient_request(
        document_text=payload.text, target_language=payload.target_language
    )
    return result
