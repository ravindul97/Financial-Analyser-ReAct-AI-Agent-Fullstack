import os
import pandas as pd
import logging
from langchain_pinecone import PineconeVectorStore, Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone, ServerlessSpec
from src.backend.services.llm_model import embeddings
from src.backend.core.config import PINECONE_API_KEY, FILES_METADATA, PROCESSED_CSV_DATA_PATH, PINECONE_INDEX_NAME

#load and convert csv files
async def load_and_prepare_documents():
    try:
        """Loads CSVs, converts rows to text, and adds metadata."""
        all_docs = []
        for filename, metadata in FILES_METADATA.items():
            logging.info(f"file name: {filename}")
            file_path = os.path.join(PROCESSED_CSV_DATA_PATH, filename)
            #Skip missing files
            if not os.path.exists(file_path):
                logging.info(f"Warning: File {file_path} not found. Skipping.")
                continue

            try:
                #see data
                df = pd.read_csv(file_path)
                logging.info(f"df {filename}: {df.head()}")
                logging.info(f"Loaded {filename} with {len(df)} rows.")
            except Exception as e:
                logging.info(f"Error loading {filename}: {e}")
                continue

            for index, row in df.iterrows():
                #Prepend company information to the page_content
                company_info = f"Company: {metadata['company']} ({metadata['symbol']}). Data Point: {row.get('Data Point Name', 'N/A')}."
                
                #Remove 'Data Point Name' from content_parts if it's already handled.
                row_data_string = ", ".join([f"{col}: {val}" for col, val in row.drop('Data Point Name', errors='ignore').dropna().items()])
                page_content = f"{company_info} Values: {row_data_string}"
                
                #Add metadata
                doc_metadata = metadata.copy() 
                doc_metadata["source_file"] = filename
                doc_metadata["row_index"] = index 
                
                # Add data point name to metadata
                if 'Data Point Name' in row:
                    doc_metadata['data_point_name'] = str(row['Data Point Name'])
                if 'Year' in row:
                    doc_metadata['year'] = str(row['Year'])

                all_docs.append(Document(page_content=page_content, metadata=doc_metadata))
        
        logging.info(f"Total documents created before splitting: {len(all_docs)}")
        if all_docs:
            logging.info(f"Sample document content before splitting: {all_docs[0].page_content}")
            logging.info(f"Sample document metadata before splitting: {all_docs[0].metadata}")
        return all_docs
    except Exception as e:
        logging.error(f"Error in loading and prepairing docs: {e}")
        return
    

#Split documents into chunks
async def split_documents(documents):
    try:
        """Splits documents into smaller chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=0,
            length_function=len,
        )
        split_docs = text_splitter.split_documents(documents)
        logging.info(f"Total documents after splitting: {len(split_docs)}")
        return split_docs
    except Exception as e:
        logging.error(f"Error in chunking docs: {e}")
        return

#Main pipeline for loading, processing, and storing document
async def rag_pipeline():
    logging.info("strat rag pipeline")
    pc = Pinecone(
        api_key=PINECONE_API_KEY
    )
    try:
        #check the pinecone index
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=768,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
    except Exception as e:
        logging.error(f"Error creating Pinecone index: {e}")
        return
    

    #Load and Prepare Documents
    logging.info("Loading and preparing documents...")
    raw_documents = await load_and_prepare_documents()
    if not raw_documents:
        logging.info("No documents loaded. Exiting.")
        return

    #Split Documents
    logging.info("Splitting documents...")
    chunked_documents = await split_documents(raw_documents)
    if not chunked_documents:
        logging.info("No documents to process after splitting. Exiting.")
        return
    
    logging.info(f"Sample chunk 0 metadata: {chunked_documents[0].metadata if chunked_documents else 'N/A'}")
    logging.info(f"Sample chunk 0 content: {chunked_documents[0].page_content[:100] if chunked_documents else 'N/A'}...")

    index_name = PINECONE_INDEX_NAME

    try:
        #Embed and store into Pinecone index
        PineconeVectorStore.from_documents(
            documents=chunked_documents,
            embedding=embeddings,
            index_name=index_name,
        )

        logging.info("Embeddings stored successfully in Pinecone.")

        return 'succesfully stored'

    except Exception as e:
        logging.error(f"Error storing embeddings in Pinecone: {e}")
