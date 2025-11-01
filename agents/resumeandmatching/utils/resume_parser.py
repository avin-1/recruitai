from typing import Optional
import fitz  # PyMuPDF


def parse_resume(resume_path: str) -> Optional[str]:
    try:
        doc = fitz.open(resume_path)
        text = "".join([page.get_text() for page in doc])
        doc.close()
        return text
    except Exception:
        return None


