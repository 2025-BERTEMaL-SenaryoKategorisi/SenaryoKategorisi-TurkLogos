from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import os
import glob

load_dotenv()

# Option 1: Specify individual text files
file_paths = [
    "data/campaignscampaigns.txt",
]

# Option 2: Load all .txt files from a directory
# file_paths = glob.glob("data/*.txt")

# Load documents from text files
docs = []
for file_path in file_paths:
    if os.path.exists(file_path):
        loader = TextLoader(file_path, encoding='utf-8')
        docs.extend(loader.load())
    else:
        print(f"Warning: File {file_path} not found")

# Flatten the documents list if needed
docs_list = docs

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,  # Use simple length function
)
doc_splits = text_splitter.split_documents(docs_list)

# Create embeddings instance (using a lightweight embedding model)
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",  # or "all-minilm" or other embedding models
    base_url="http://localhost:11434"  # default Ollama URL
)

# Create vector store
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=embeddings,
    persist_directory="./.chroma",
)

# Create retriever
retriever = Chroma(
    collection_name="rag-chroma",
    persist_directory="./.chroma",
    embedding_function=embeddings,
).as_retriever()

print(f"Successfully ingested {len(doc_splits)} document chunks from {len(docs_list)} files")