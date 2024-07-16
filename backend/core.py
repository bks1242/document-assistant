from dotenv import load_dotenv
import os
from typing import Any, Dict, List
from langchain.chains.retrieval import create_retrieval_chain

load_dotenv()

from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_pinecone import PineconeVectorStore
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

from consts import INDEX_NAME

# INDEX_NAME = "langchain-docs-index"
INDEX_NAME = "sample-embeddings-index"


def run_llm(query: str, chat_history: List[Dict[str, Any]] = []):
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.environ["AZURE_EMBEDDING_OPENAI_DEPLOYMENT"],
        openai_api_key=os.environ["AZURE_EMBEDDING_OPENAI_KEY"],
        azure_endpoint=os.environ["AZURE_EMBEDDING_OPENAI_API_BASE"],
        openai_api_type=os.environ["AZURE_EMBEDDING_OPENAI_API_TYPE"],
        openai_api_version=os.environ["AZURE_EMBEDDING_OPENAI_API_VERSION"],
    )

    docsearch = PineconeVectorStore(embedding=embeddings, index_name=INDEX_NAME)
    chat = AzureChatOpenAI(
        openai_api_key=os.environ["AZURE_OPENAI_KEY"],
        azure_endpoint=os.envi["AZURE_OPENAI_ENDPOINT"],
        openai_api_type="azure",
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        openai_api_version="2024-05-01-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt)

    history_aware_retriever = create_history_aware_retriever(
        llm=chat, retriever=docsearch.as_retriever(), prompt=rephrase_prompt
    )
    qa = create_retrieval_chain(
        retriever=history_aware_retriever, combine_docs_chain=stuff_documents_chain
    )

    result = qa.invoke(input={"input": query, "chat_history": chat_history})
    new_result = {
        "query": result["input"],
        "result": result["answer"],
        "source_documents": result["context"],
    }
    return new_result


if __name__ == "__main__":
    res = run_llm(query="What is pincone in machine learning?")
    print(res["result"])
