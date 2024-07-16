import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import ReadTheDocsLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.environ["AZURE_EMBEDDING_OPENAI_DEPLOYMENT"],
    openai_api_key=os.environ["AZURE_EMBEDDING_OPENAI_KEY"],
    azure_endpoint=os.environ["AZURE_EMBEDDING_OPENAI_API_BASE"],
    openai_api_type=os.environ["AZURE_EMBEDDING_OPENAI_API_TYPE"],
    openai_api_version=os.environ["AZURE_EMBEDDING_OPENAI_API_VERSION"],
)

# load the document --> split the document into chunks --> create embeddings --> store in vector database
def ingest_docs():
  print("Ingesting..")
  loader = ReadTheDocsLoader("langchain-docs/api.python.langchain.com/en/latest", encoding="utf-8")
  
  raw_documents = loader.load()
  
  print(f"loaded {len(raw_documents)} documents")
  
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50)
  documents = text_splitter.split_documents(raw_documents)
  
  for doc in documents:
    new_url = doc.metadata["source"]
    new_url = new_url.replace("langchain-docs", "http:/")
    doc.metadata.update({"source": new_url})
  
  print(f"Going to add {len(documents)} to the vector store db (Pincecone)")
  pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
  PineconeVectorStore.from_documents(documents, embeddings, index_name="langchain-docs-index")
  
  print("-----Loading to Vector Store Done----------")
  

if __name__ == "__main__":
  ingest_docs()