"""Resume-based question answering using LangChain and FAISS."""
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI, OpenAIEmbeddings
load_dotenv()

INDEX_DIR = "faiss_index"

def answer(user_question):
    """Answer a question based on the resume information in the vector store.
    
    Args:
        user_question (str): The question to answer
        
    Returns:
        str: The answer based on the resume context
    """
    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.load_local(
        INDEX_DIR, embeddings, allow_dangerous_deserialization=True
    )

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

    res = retrieval_chain.invoke({"input": user_question})
    return res["answer"]

if __name__ == "__main__":
    # Example usage
    EXAMPLE_QUESTION = "What is the candidate's experience with AI?"
    answer_text = answer(EXAMPLE_QUESTION)
    print(answer_text)
