from pathlib import Path
from functools import lru_cache
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationTokenBufferMemory,
    CombinedMemory,
)
import torch

SYSTEM_PROMPT = (
    "تو یک دستیار خوب برای مذاکره کردن هستی. "
    "از context و اطلاعات موجود برای پاسخ دادن استفاده کن. "
    "با توجه به توانایی های فرد به سوالات پاسخ بده و سعی کن فرد را مجاب کنی که توانایی انجام دادن آن کار را داری. "
    "اگر فرد تمایل داشت پروژه را به تو بدهد با ملایمت و ادب جواب بده، در غیر این صورت با ادب خداحافظی کن. "
    "لطفاً تنها اطلاعات مرتبط با سوال را از context استخراج کن. "
    "اگر جواب سوالی را نمی‌دانی، بگو: «پاسخ دقیقی برای این سوال ندارم» یا درخواست اطلاعات بیشتر کن. "
    "اگر توانایی خواسته شده در مهارت‌های فرد نبود بگو من این توانایی را ندارم. "
    "مانند انسان و فارسی عامیانه صحبت کن نه رسمی. "
    "خیلی کوتاه جواب بده.\n\n{context}"
)

def _embeddings(model_name: str):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={  # device باید اینجاست
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        encode_kwargs={
            "batch_size": 16,
            "normalize_embeddings": True,
        },
    )

def _build_chain(faiss_dir: str, embed_model: str):
    emb = _embeddings(embed_model)
    vs = FAISS.load_local(faiss_dir, embeddings=emb, allow_dangerous_deserialization=True)
    retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    llm = ChatOllama(model="llama3.1:latest", temperature=0.1, top_p=0.9, top_k=40, num_ctx=4096, num_thread=8, streaming=False)
    s_llm = ChatOllama(model="llama3.1:latest", temperature=0.0)

    short = ConversationBufferWindowMemory(k=6, return_messages=True, memory_key="short_term_history")
    token = ConversationTokenBufferMemory(llm=s_llm, max_token_limit=1500, return_messages=True, memory_key="token_history")
    summ  = ConversationSummaryBufferMemory(llm=s_llm, max_token_limit=2000, return_messages=False, memory_key="summary_history")
    memory = CombinedMemory(memories=[short, token, summ])

    search_prompt = ChatPromptTemplate.from_messages([
        ("system", "با توجه به تاریخچهٔ گفتگو و سؤال جدید، یک عبارت جستجوی کوتاه و دقیق بساز."),
        (MessagesPlaceholder(variable_name="short_term_history")),
        ("human", "{input}"),
    ])
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        (MessagesPlaceholder(variable_name="short_term_history")),
        ("human", "{input}"),
    ])

    history_aware = create_history_aware_retriever(llm=llm, retriever=retriever, prompt=search_prompt)
    qa_chain = create_stuff_documents_chain(llm, answer_prompt)
    rag_chain = create_retrieval_chain(history_aware, qa_chain)
    return rag_chain, memory

class RAGManager:
    """
    یک کش ساده برای چندین doc_id
    """
    def __init__(self, docs_dir: str, embed_model: str):
        self.docs_dir = Path(docs_dir)
        self.embed_model = embed_model
        self._cache = {}

    def _paths(self, doc_id: str):
        base = self.docs_dir / doc_id
        return {
            "ws": base,
            "pdf": base / "source.pdf",
            "md": base / "skill.md",
            "index": base / "my_faiss_index",
        }

    def get(self, doc_id: str):
        if doc_id in self._cache:
            return self._cache[doc_id]
        paths = self._paths(doc_id)
        if not paths["index"].exists():
            raise FileNotFoundError("FAISS index not found for this doc_id.")
        chain, memory = _build_chain(str(paths["index"]), self.embed_model)
        self._cache[doc_id] = (chain, memory)
        return self._cache[doc_id]

    def ask(self, doc_id: str, query: str) -> str:
        chain, memory = self.get(doc_id)
        mem_vars = memory.load_memory_variables({"input": query})
        inputs = {"input": query, **mem_vars}
        result = chain.invoke(inputs)
        answer = result.get("answer") or result.get("output_text") or str(result)
        memory.save_context({"input": query}, {"answer": answer})
        return answer
