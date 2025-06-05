import os


from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain.prompts import PromptTemplate

INDEX_DIR = "faiss_index"

if __name__ == "__main__":

    # delete previous index if exists
    
    if os.path.exists(INDEX_DIR):
        print(f"Deleting existing index directory: {INDEX_DIR}")
        import shutil
        shutil.rmtree(INDEX_DIR)

    # create index
    pdf_path = "resume.pdf"
    loader = PyPDFLoader(file_path=pdf_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(
        chunk_size=1000, chunk_overlap=30, separator="\n"
    )
    docs = text_splitter.split_documents(documents=documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(INDEX_DIR)
