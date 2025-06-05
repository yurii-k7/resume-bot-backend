from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv
load_dotenv()

INDEX_DIR = "faiss_index"

def answer(question):
    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

    prompt_template = """
        You are a helpful assistant. You will be given a resume and a question.
        Your task is to answer the question based on the information in the documents.
        Your task is convice the user that person is a good fit for the job.
        If the question is not related to the resume, say "I don't know".
        You should answer the question in a concise and informative manner.
        If the question is related to the resume, provide a detailed answer based on the information in the documents.
        If the question is related to the resume, you should provide a detailed answer based on the information in the documents.
        Answer in positive and optimistic tone.
        If the question cannot be answered based on the information in the documents, say "I don't know".
        Here are the documents:
        {context}
        Question: {input}
        Answer:
    """

    retrieval_qa_chat_prompt = PromptTemplate(
        input_variables=["context", "input"],
        template=prompt_template,
    )


    combine_docs_chain = create_stuff_documents_chain(
        OpenAI(), retrieval_qa_chat_prompt
    )
    retrieval_chain = create_retrieval_chain(
        vectorstore.as_retriever(), combine_docs_chain
    )

    res = retrieval_chain.invoke({"input": question})
    return res["answer"]

if __name__ == "__main__":
    # Example usage
    question = "What is the candidate's experience with AI?"
    answer_text = answer(question)
    print(answer_text)