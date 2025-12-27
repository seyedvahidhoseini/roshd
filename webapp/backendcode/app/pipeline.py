import shutil
import uuid
from pathlib import Path
from .converters import pdf_to_markdown
from .indexing import build_faiss_index

class DocPipeline:
    def __init__(self, docs_dir: str, embed_model: str):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.embed_model = embed_model

    def create_workspace(self, doc_id: str | None = None) -> str:
        doc_id = doc_id or str(uuid.uuid4())
        ws = self.docs_dir / doc_id
        ws.mkdir(parents=True, exist_ok=True)
        return doc_id

    def run_all(self, src_pdf_path: str, doc_id: str | None = None) -> dict:
        """ایجاد (یا استفاده از) doc_id → کپی PDF → ساخت md → ساخت ایندکس"""
        doc_id = self.create_workspace(doc_id)
        ws = self.docs_dir / doc_id
        pdf_path = ws / "source.pdf"
        shutil.copy2(src_pdf_path, pdf_path)

        md_path = ws / "skill.md"
        pdf_to_markdown(str(pdf_path), str(md_path))

        index_dir = ws / "my_faiss_index"
        build_faiss_index(str(md_path), str(index_dir), embed_model=self.embed_model)

        return {
            "doc_id": doc_id,
            "pdf_path": str(pdf_path),
            "md_path": str(md_path),
            "index_dir": str(index_dir),
        }
