from pathlib import Path
import fitz  # PyMuPDF

def pdf_to_markdown(pdf_path: str, md_path: str) -> str:
    pdf_p = Path(pdf_path)
    md_p = Path(md_path)

    doc = fitz.open(str(pdf_p))
    parts = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            parts.append(f"## صفحه {i}\n{text}\n")
    doc.close()

    md_p.parent.mkdir(parents=True, exist_ok=True)
    md_p.write_text("\n".join(parts), encoding="utf-8")
    return str(md_p)
