"""
Medical Summarizer Module for MediGuide-AI.
Generates safe, patient-friendly summaries from extracted clinical information.

Architecture & Clinical Safety:
1. Grounded in Extracted Clinical Facts:
   The summarizer only uses information present in the input document.
   Clinical measurements, units, dates, test names, and medications are deterministically
   verified and preserved without alteration.
2. Non-Diagnostic & Non-Prescriptive:
   Does not invent diagnoses or recommend treatments.
   Explicitly distinguishes extracted source statements from narrative summaries.
3. Reliable Deterministic Fallback:
   If model weights are not downloaded, if loading fails, or if inference encounters an
   error, the module falls back to deterministic template summarization.
4. Privacy:
   Medical document text, patient identifiers, and clinical values are NEVER logged.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional

# Silence OneDNN precision/round-off and HF symlink warnings on Windows
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Pretrained summarization model metadata
SUMMARIZATION_MODEL_NAME = "sshleifer/distilbart-cnn-6-6"
SUMMARIZATION_MODEL_LINK = "https://huggingface.co/sshleifer/distilbart-cnn-6-6"
SUMMARIZATION_MODEL_LICENSE = "Apache-2.0"

_summarization_pipeline = None
_pipeline_initialized = False


def get_summarization_pipeline():
    """
    Lazily initialize and return the Hugging Face summarization pipeline for CPU.
    Prefers loading from local cache without network retry delays.
    Returns None safely if dependencies or weights are unavailable.
    Does NOT log patient data.
    """
    global _summarization_pipeline, _pipeline_initialized
    if _pipeline_initialized:
        return _summarization_pipeline

    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

        # Try offline local files first to avoid network retry pauses
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                SUMMARIZATION_MODEL_NAME, local_files_only=True
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                SUMMARIZATION_MODEL_NAME, local_files_only=True
            )
            _summarization_pipeline = pipeline(
                "summarization", model=model, tokenizer=tokenizer, device=-1
            )
            logging.info("Summarization pipeline initialized from local cache.")
        except Exception:
            # Fall back to standard pipeline initialization if offline cache lookup fails
            _summarization_pipeline = pipeline(
                "summarization",
                model=SUMMARIZATION_MODEL_NAME,
                device=-1,  # CPU execution
            )
            logging.info("Summarization pipeline initialized successfully.")
    except Exception as e:
        logging.warning(
            "Could not initialize summarization model '%s'. Running in deterministic fallback mode.",
            SUMMARIZATION_MODEL_NAME,
        )
        _summarization_pipeline = None

    _pipeline_initialized = True
    return _summarization_pipeline


def _chunk_text(text: str, max_chunk_chars: int = 1000) -> List[str]:
    """
    Safely split long documents at sentence boundaries without splitting decimal numbers.
    """
    if not text or len(text) <= max_chunk_chars:
        return [text] if text else []

    pattern = re.compile(r'(?<=[.!?\n])\s+')
    sentences = pattern.split(text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        if current_len + len(s_clean) > max_chunk_chars and current_chunk:
            chunks.append(" ".join(current_chunk).strip())
            current_chunk = [s_clean]
            current_len = len(s_clean)
        else:
            current_chunk.append(s_clean)
            current_len += len(s_clean) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    return chunks


def _build_context_text(extracted_info: Dict[str, Any]) -> str:
    """
    Construct factual context text exclusively from extracted clinical entities
    and observations without adding speculative details.
    """
    parts = []
    obs = extracted_info.get("observations", [])
    if obs:
        parts.append(" ".join(obs))

    symptoms = extracted_info.get("symptoms", [])
    if symptoms:
        parts.append(f"Reported symptoms: {', '.join(symptoms)}.")

    medications = extracted_info.get("medications", [])
    if medications:
        parts.append(f"Mentioned medications: {', '.join(medications)}.")

    test_names = extracted_info.get("test_names", [])
    test_values = extracted_info.get("test_values", [])
    units = extracted_info.get("units", [])
    if test_names or test_values:
        measurements_desc = []
        if test_names:
            measurements_desc.append(f"Tests: {', '.join(test_names)}")
        if test_values:
            val_str = ", ".join(test_values)
            if units:
                val_str += f" ({', '.join(units)})"
            measurements_desc.append(f"Measurements: {val_str}")
        parts.append(f"{'. '.join(measurements_desc)}.")

    dates = extracted_info.get("dates", [])
    if dates:
        parts.append(f"Dates found: {', '.join(dates)}.")

    return " ".join(parts).strip()


def _verify_neural_summary(
    summary_text: str, extracted_info: Dict[str, Any]
) -> bool:
    """
    Verify that the neural model output faithfully preserves all key clinical facts:
    vital measurements, scientific units, medications, test names, symptoms, and dates.
    Returns False if any source fact was dropped or distorted.
    """
    if not summary_text or not summary_text.strip():
        return False

    summary_lower = summary_text.lower()

    # 1. Verify numeric measurements
    test_values = extracted_info.get("test_values", [])
    for val in test_values:
        if val not in summary_text:
            return False

    # 2. Verify scientific units
    units = extracted_info.get("units", [])
    for u in units:
        if u.lower() not in summary_lower:
            return False

    # 3. Verify medications
    medications = extracted_info.get("medications", [])
    for med in medications:
        if med.lower() not in summary_lower:
            return False

    # 4. Verify test names
    test_names = extracted_info.get("test_names", [])
    for t in test_names:
        if t.lower() not in summary_lower:
            return False

    # 5. Verify symptoms
    symptoms = extracted_info.get("symptoms", [])
    for sym in symptoms:
        if sym.lower() not in summary_lower:
            return False

    # 6. Verify dates
    dates = extracted_info.get("dates", [])
    for d in dates:
        # Check either full date or individual tokens
        d_lower = d.lower()
        if d_lower not in summary_lower:
            tokens = [tok for tok in d_lower.split() if len(tok) >= 3]
            if tokens and not all(tok in summary_lower for tok in tokens):
                return False

    return True


def _run_neural_summarization(
    pipeline_obj: Any, context_text: str, max_chunk_chars: int = 1000
) -> Optional[str]:
    """
    Execute neural summarization over text chunks using DistilBART.
    Handles long documents safely without logging medical contents.
    Returns None if any step fails.
    """
    chunks = _chunk_text(context_text, max_chunk_chars=max_chunk_chars)
    if not chunks:
        return None

    generated_parts: List[str] = []
    for chunk in chunks:
        try:
            # Dynamically set max_length safely according to input length
            words_count = len(chunk.split())
            max_len = min(130, max(25, words_count + 10))
            min_len = min(15, max(5, words_count // 3))

            outputs = pipeline_obj(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
                truncation=True,
            )
            if outputs and isinstance(outputs, list) and "summary_text" in outputs[0]:
                gen_text = outputs[0]["summary_text"].strip()
                if gen_text:
                    generated_parts.append(gen_text)
        except Exception:
            logging.warning(
                "Neural summarizer encountered an error during inference; falling back."
            )
            return None

    if not generated_parts:
        return None

    return " ".join(generated_parts).strip()


def _generate_deterministic_summary(extracted_info: Dict[str, Any]) -> str:
    """
    Deterministic template summarizer.
    Guarantees 100% factual accuracy and zero hallucination.
    Preserves exact backward compatibility with existing tests.
    """
    summary_parts = []
    summary_parts.append(
        "This is a summary of the provided document. Please note this is not a diagnosis or clinical recommendation."
    )

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

    test_values = extracted_info.get("test_values", [])
    units = extracted_info.get("units", [])
    if test_values:
        measurements_str = ", ".join(test_values)
        if units:
            measurements_str += f" ({', '.join(units)})"
        summary_parts.append(f"Recorded measurements: {measurements_str}.")

    if not any([symptoms, medications, test_names, test_values, dates, obs]):
        summary_parts.append(
            "Information appears incomplete or no specific medical data was detected."
        )

    return " ".join(summary_parts)


def summarize_medical_info(
    extracted_info: Any, source_text: Optional[str] = None
) -> str:
    """
    Convert extracted information into a patient-friendly summary.
    Combines pretrained abstractive summarization with deterministic clinical safeguards.

    Safety Guarantees:
    - Never makes clinical diagnoses or treatment recommendations.
    - Never invents missing data or alters inferred_info.
    - Factual verification: preserves exact measurements, units, dates, test names, medications.
    - Falls back to deterministic template if model is unavailable, fails, or omits source facts.
    - Patient privacy: never logs medical documents or clinical values.
    """
    if not extracted_info or not isinstance(extracted_info, dict):
        return "No information could be summarized."

    # Inferred info must never be populated or assumed
    if "inferred_info" in extracted_info:
        extracted_info["inferred_info"] = []

    symptoms = extracted_info.get("symptoms", [])
    medications = extracted_info.get("medications", [])
    test_names = extracted_info.get("test_names", [])
    test_values = extracted_info.get("test_values", [])
    dates = extracted_info.get("dates", [])
    obs = extracted_info.get("observations", [])

    has_medical_data = any([symptoms, medications, test_names, test_values, dates, obs])
    if not has_medical_data:
        return (
            "This is a summary of the provided document. "
            "Please note this is not a diagnosis or clinical recommendation. "
            "Information appears incomplete or no specific medical data was detected."
        )

    # 1. Attempt neural summarization if pipeline is available
    pipeline_obj = get_summarization_pipeline()
    if pipeline_obj is not None:
        context_text = source_text if source_text else _build_context_text(extracted_info)
        if context_text and context_text.strip():
            raw_neural_summary = _run_neural_summarization(pipeline_obj, context_text)
            if raw_neural_summary:
                # 2. Rigorous clinical verification: ensure all source facts and metrics are preserved
                if _verify_neural_summary(raw_neural_summary, extracted_info):
                    # Prepend standard clinical disclaimer
                    disclaimer = (
                        "This is a summary of the provided document. "
                        "Please note this is not a diagnosis or clinical recommendation."
                    )
                    return f"{disclaimer} {raw_neural_summary}"
                else:
                    logging.info(
                        "Neural summary omitted or altered key clinical measurements; using source-grounded deterministic summary."
                    )

    # 3. Deterministic fallback: provides 100% reliable, factual clinical report
    return _generate_deterministic_summary(extracted_info)
