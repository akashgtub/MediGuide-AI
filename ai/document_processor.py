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
