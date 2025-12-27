from pathlib import Path
from hazm import Normalizer, word_tokenize
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import torch

_normalizer = Normalizer()

def _preprocess(text: str) -> str:
    try:
        text = text.lower()
        text = _normalizer.normalize(text)
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        return ' '.join(word_tokenize(text))
    except Exception:
        return text

def build_faiss_index(md_path: str, out_dir: str, embed_model: str = "Msobhi/Persian_Sentence_Embedding_v3"):
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    loader = TextLoader(str(md_path), encoding='utf-8')
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", ".", "؛", ";", " ", ",", "-"],
        keep_separator=True,
        length_function=lambda x: len(x.split())
    )
    splits = splitter.split_documents(docs)
    texts = [_preprocess(d.page_content) for d in splits]

    embeddings = HuggingFaceEmbeddings(
        model_name=embed_model,
        encode_kwargs={
        "batch_size": 16,
        "normalize_embeddings": True,
        }
    )

    vs = FAISS.from_texts(
        texts,
        embedding=embeddings,
        metadatas=[{"source": f"chunk_{i}"} for i in range(len(texts))]
    )
    vs.save_local(str(out_dir))
    return str(out_dir)
