"""Create FAISS index from resume PDF for question answering."""
import os
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

INDEX_DIR = "faiss_index"

if __name__ == "__main__":

    # delete previous index if exists

    if os.path.exists(INDEX_DIR):
        print(f"Deleting existing index directory: {INDEX_DIR}")
        shutil.rmtree(INDEX_DIR)

    # create index
    PDF_PATH = "resume.pdf"
    loader = PyPDFLoader(file_path=PDF_PATH)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(
        chunk_size=1000, chunk_overlap=30, separator="\n"
    )
    docs = text_splitter.split_documents(documents=documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(INDEX_DIR)
    print(f"Index created successfully at {INDEX_DIR}")
