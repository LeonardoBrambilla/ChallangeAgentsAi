"""Script de ingestão vetorial: lê os documentos/FAQs, faz chunking, gera embeddings
via Azure OpenAI e persiste no vector store configurado (Chroma por padrão, ou Azure AI
Search se `VECTOR_BACKEND=azure_search`).

Uso:
    python -m vector_db.ingest
"""
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from logging_config import configure_logging, log_event
from settings import settings
from vector_db.store_factory import get_vector_store

logger = configure_logging(settings.log_level)

DOCUMENTS_DIR = Path(__file__).parent / "documents"


def load_documents() -> list[Document]:
    documents = []
    for path in sorted(DOCUMENTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name}))
    return documents


def main() -> None:
    documents = load_documents()
    log_event(logger, "ingest.loaded", num_documents=len(documents))

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    log_event(logger, "ingest.chunked", num_chunks=len(chunks))

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    log_event(logger, "ingest.done", backend=settings.vector_backend, collection=settings.chroma_collection)


if __name__ == "__main__":
    main()
