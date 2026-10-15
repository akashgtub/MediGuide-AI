import os
import logging
from typing import List, Any

# Disable network connectivity check to model hosters to prevent timeouts
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
# Prevent OpenMP runtime conflict when both Paddle and PyTorch are loaded on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Supported file extensions for document OCR
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".bmp", ".tiff"}

ocr_engine = None

def get_ocr_engine():
    """
    Lazily initialize and return the PaddleOCR engine singleton.
    Configured for CPU execution and compatible with PaddleOCR 3.x and 2.x.
    """
    global ocr_engine
    if ocr_engine is not None:
        return ocr_engine

    try:
        from paddleocr import PaddleOCR
        # PaddleOCR 3.x configuration:
        # device='cpu' forces CPU execution.
        # enable_mkldnn=False avoids the OneDNN PIR executor runtime attribute issue on CPU.
        # use_doc_orientation_classify=False & use_doc_unwarping=False optimize inference speed.
        # use_textline_orientation=True correctly detects text orientation.
        try:
            ocr_engine = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                lang="en",
                device="cpu",
                enable_mkldnn=False,
            )
        except Exception as init_err:
            logging.warning(
                f"Modern PaddleOCR initialization failed ({init_err}). Attempting fallback."
            )
            try:
                ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False)
            except Exception:
                ocr_engine = PaddleOCR(lang="en")
    except ImportError:
        ocr_engine = None
        logging.warning("PaddleOCR not installed or failed to import.")
    except Exception as e:
        ocr_engine = None
        logging.error(f"Failed to initialize PaddleOCR: {e}")

    return ocr_engine


def process_document(text: str) -> str:
    """
    Accept document/text input.
    Clean and normalize extracted text.
    Prepare text for downstream processing.
    """
    if not text:
        return ""
    # Clean up whitespace and line breaks
    cleaned_text = " ".join(text.split())
    return cleaned_text


def _extract_text_lines(result: Any) -> List[str]:
    """
    Safely extract recognized text lines from PaddleOCR result structures across versions.
    PaddleOCR 3.x returns a list of OCRResult dict-like objects containing 'rec_texts'.
    PaddleOCR 2.x returns nested lists of [[polygon_points], (text, confidence)].
    """
    text_lines: List[str] = []
    if not result:
        return text_lines

    for page in result:
        if page is None:
            continue
        # PaddleOCR 3.x structure (OCRResult or dict containing 'rec_texts')
        if isinstance(page, dict) or hasattr(page, "get"):
            rec_texts = page.get("rec_texts", [])
            if rec_texts:
                for line in rec_texts:
                    if line and isinstance(line, str):
                        text_lines.append(line.strip())
        # PaddleOCR 2.x structure (list of [[points], (text, score)])
        elif isinstance(page, (list, tuple)):
            for line in page:
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    content = line[1]
                    if isinstance(content, (list, tuple)) and len(content) >= 1:
                        text_lines.append(str(content[0]).strip())
                    elif isinstance(content, str):
                        text_lines.append(content.strip())
                elif isinstance(line, str):
                    text_lines.append(line.strip())
        elif isinstance(page, str):
            text_lines.append(page.strip())

    return text_lines


def extract_text_from_pdf_native(file_path: str) -> str:
    """
    Directly extract digital text streams from PDF pages using PyMuPDF (fitz) or pypdf.
    Extremely fast (< 50ms) and avoids heavy OCR computation on documents with digital text.
    Returns extracted text if found, or empty string if document has no readable text (e.g. scanned).
    """
    if not file_path or not os.path.exists(file_path):
        return ""

    extracted_pages: List[str] = []
    # 1. Attempt PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(file_path)
        for page in doc:
            t = page.get_text()
            if t and t.strip():
                extracted_pages.append(t.strip())
        doc.close()
    except Exception as e:
        logging.debug(f"fitz PDF text extraction failed or unavailable: {e}")

    # 2. Fall back to pypdf if fitz was unavailable or found no text
    if not extracted_pages:
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    extracted_pages.append(t.strip())
        except Exception as e:
            logging.debug(f"pypdf extraction failed: {e}")

    if extracted_pages:
        return "\n".join(extracted_pages)
    return ""


def _ocr_pdf_pages(file_path: str, engine: Any) -> str:
    """
    Render scanned/image PDF pages to temporary images and process via PaddleOCR.
    Cleans up all temporary files immediately.
    """
    lines: List[str] = []
    try:
        import fitz
        import tempfile
        doc = fitz.open(file_path)
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_name = tmp.name
            try:
                pix.save(tmp_name)
                if hasattr(engine, "predict"):
                    res = engine.predict(tmp_name)
                else:
                    res = engine.ocr(tmp_name, cls=True)
                lines.extend(_extract_text_lines(res))
            finally:
                if os.path.exists(tmp_name):
                    try:
                        os.remove(tmp_name)
                    except OSError:
                        pass
        doc.close()
    except Exception as e:
        logging.warning(f"Failed to rasterize and OCR PDF pages: {e}")
    return " ".join(lines)


def extract_text_from_document(file_path: str) -> str:
    """
    Extract recognized text from an image or PDF document.
    Prioritizes fast native digital PDF extraction; falls back to PaddleOCR
    for images and scanned documents.
    
    Safety:
    This function ONLY extracts text from documents.
    It does NOT diagnose, prescribe, interpret, or recommend medical treatments.
    """
    if not file_path or not isinstance(file_path, str):
        return ""

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        logging.warning(f"File not found or is not a valid file: {file_path}")
        return ""

    # Check for empty file (0 bytes)
    try:
        if os.path.getsize(file_path) == 0:
            logging.warning(f"File is empty (0 bytes): {file_path}")
            return ""
    except OSError as e:
        logging.error(f"Error accessing file {file_path}: {e}")
        return ""

    # Validate file extension
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    if ext_lower not in SUPPORTED_EXTENSIONS:
        logging.warning(f"Unsupported file format: {ext} for file: {file_path}")
        return ""

    # Fast path for PDFs with digital text streams
    if ext_lower == ".pdf":
        native_text = extract_text_from_pdf_native(file_path)
        logging.info("PDF native text check: '%s' yielded %d characters", file_path, len(native_text) if native_text else 0)
        if native_text and len(native_text.strip()) >= 15:
            return process_document(native_text)
        logging.warning("PDF native extraction yielded insufficient text; falling back to PaddleOCR for '%s'", file_path)

    # Scanned PDF or Image: requires OCR engine
    engine = get_ocr_engine()
    if engine is None:
        logging.error("OCR engine is not available.")
        return ""

    try:
        if ext_lower == ".pdf":
            extracted_text = _ocr_pdf_pages(file_path, engine)
        else:
            if hasattr(engine, "predict"):
                result = engine.predict(file_path)
            else:
                result = engine.ocr(file_path, cls=True)
            extracted_lines = _extract_text_lines(result)
            extracted_text = " ".join(extracted_lines)

        return process_document(extracted_text)
    except Exception as e:
        logging.error(f"Failed to process document {file_path}: {e}")
        return ""
