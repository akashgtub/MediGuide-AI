import os
import logging

try:
    from paddleocr import PaddleOCR
    # Initialize PaddleOCR globally so we don't reload it every time
    # use_angle_cls=True helps with rotated text
    # use_gpu=False ensures it runs on CPU as requested
    ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)
except ImportError:
    ocr_engine = None
    logging.warning("PaddleOCR not installed or failed to initialize.")

def process_document(text: str) -> str:
    """
    Accept document/text input.
    Clean and normalize extracted text.
    Prepare text for downstream processing.
    """
    if not text:
        return ""
    # simple clean up for now
    cleaned_text = " ".join(text.split())
    return cleaned_text

def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from an image or PDF document using PaddleOCR.
    Handles PNG, JPG, PDF safely without diagnosing.
    """
    if not os.path.exists(file_path):
        return ""

    if ocr_engine is None:
        logging.error("OCR engine is not available.")
        return ""

    try:
        # OCR returns a list of results, one for each page
        result = ocr_engine.ocr(file_path, cls=True)
        if not result:
            return ""

        extracted_text_parts = []
        for page in result:
            if page is None:
                continue
            for line in page:
                # line is structured as: [[points], (text, confidence)]
                text_content = line[1][0]
                extracted_text_parts.append(text_content)
        
        extracted_text = " ".join(extracted_text_parts)
        return process_document(extracted_text)
    except Exception as e:
        logging.error(f"Failed to process document {file_path}: {e}")
        return ""
