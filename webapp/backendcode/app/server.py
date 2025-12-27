import os
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import tempfile

from app.pipeline import DocPipeline
from app.rag import RAGManager
from app.db import SessionLocal, init_db, Freelancer

load_dotenv()

BASE_DIR = Path(os.getenv("BASE_DIR", "app/storage"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "app/storage/uploads"))
DOCS_DIR = Path(os.getenv("DOCS_DIR", "app/storage/docs"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "Msobhi/Persian_Sentence_Embedding_v3")

BASE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

init_db()

app = Flask(__name__)
CORS(app)

pipeline = DocPipeline(docs_dir=str(DOCS_DIR), embed_model=EMBED_MODEL)
rag_manager = RAGManager(docs_dir=str(DOCS_DIR), embed_model=EMBED_MODEL)

# ---------- Schemas ----------
class ChatBody(BaseModel):
    query: str
    doc_id: str | None = None
    freelancer_id: str | None = None

# ---------- Utils ----------
def to_dict(f: Freelancer):
    return {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "pdf_path": f.pdf_path,
        "md_path": f.md_path,
        "index_dir": f.index_dir,
        "created_at": f.created_at.isoformat()
    }

# ---------- Health ----------
@app.get("/health")
def health():
    return jsonify(status="ok")

# ---------- Legacy list of workspaces ----------
@app.get("/docs")
def list_docs():
    items = []
    for d in DOCS_DIR.iterdir():
        if d.is_dir():
            items.append({
                "doc_id": d.name,
                "pdf": (d / "source.pdf").exists(),
                "md": (d / "skill.md").exists(),
                "index": (d / "my_faiss_index").exists(),
            })
    return jsonify(items=items)

# ---------- New: create freelancer (upload + metadata + DB) ----------
@app.post("/freelancers")
def create_freelancer():
    """
    multipart/form-data:
      - name (string, required)
      - description (string, optional)
      - file (pdf, required)
    خروجی: مشخصات فریلنسر + مسیرها
    """
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    f = request.files.get("file")

    if not name:
        return jsonify(error="name is required"), 400
    if not f or not f.filename.lower().endswith(".pdf"):
        return jsonify(error="file (.pdf) is required"), 400

    # پردازش PDF → MD → Index با یک GUID (همان id فریلنسر)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        f.save(tmp.name)
        # doc_id همان id فریلنسر می‌شود
        from uuid import uuid4
        freelancer_id = str(uuid4())
        result = pipeline.run_all(tmp.name, doc_id=freelancer_id)

    # ذخیره فایل خام در uploads (اختیاری)
    try:
        dst = UPLOAD_DIR / f"{freelancer_id}.pdf"
        Path(tmp.name).replace(dst)
    except Exception:
        pass

    # ذخیره در DB
    db = SessionLocal()
    try:
        fr = Freelancer(
            id=freelancer_id,
            name=name,
            description=description,
            pdf_path=result["pdf_path"],
            md_path=result["md_path"],
            index_dir=result["index_dir"],
        )
        db.add(fr)
        db.commit()
        db.refresh(fr)
        return jsonify(message="ok", freelancer=to_dict(fr)), 201
    finally:
        db.close()

# ---------- New: list freelancers ----------
@app.get("/freelancers")
def list_freelancers():
    db = SessionLocal()
    try:
        rows = db.query(Freelancer).order_by(Freelancer.created_at.desc()).all()
        return jsonify(items=[to_dict(r) for r in rows])
    finally:
        db.close()

# ---------- Chat: accept doc_id OR freelancer_id ----------
@app.post("/chat")
def chat():
    """
    بدنه:
      { "query": "...", "freelancer_id": "..." }  یا  { "query": "...", "doc_id": "..." }
    """
    try:
        body = ChatBody(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(error=e.errors()), 400

    # map freelancer_id -> doc_id
    doc_id = body.doc_id
    if not doc_id and body.freelancer_id:
        db = SessionLocal()
        try:
            fr = db.query(Freelancer).filter(Freelancer.id == body.freelancer_id).first()
            if not fr:
                return jsonify(error="freelancer not found"), 404
            doc_id = fr.id
        finally:
            db.close()

    if not doc_id:
        return jsonify(error="doc_id or freelancer_id is required"), 400

    try:
        answer = rag_manager.ask(doc_id, body.query)
        return jsonify(answer=answer)
    except FileNotFoundError:
        return jsonify(error="index not found for this id. create freelancer first."), 404
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
