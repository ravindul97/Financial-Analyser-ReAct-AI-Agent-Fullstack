import logging
import os
from dotenv import load_dotenv

load_dotenv()

#API version
API_VERSION = 'v1'
LOG_LEVEL = logging.INFO

#Folder-configurations
DIPPED_PLC_URL="https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=DIPD.N0000"
RICHARD_PLC_URL="https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=REXP.N0000"
COMPANY_CONFIGS = {
    "REXP": {
        "input_dir": "data/unprocess_data/REXP",
        "output_dir": "data/extracted_data/REXP",
        "keyword_regex": r"consolidated\s+income\s+statements?",
        "output_csv": "data/processed_csv/rexp_processed_financial_data.csv"
    },
    "DIPD": {
        "input_dir": "data/unprocess_data/DIPD",
        "output_dir": "data/extracted_data/DIPD",
        "keyword_regex": r"STATEMENT OF PROFIT OR LOSS",
        "output_csv": "data/processed_csv/dipd_processed_financial_data.csv"
    }
}
FILES_METADATA = {
    "dipd_processed_financial_data.csv": {"company": "Dipped Products PLC", "symbol": "DIPD"},
    "rexp_processed_financial_data.csv": {"company": "Richard Pieris Exports PLC", "symbol": "REXP"}
}
PROCESSED_CSV_DATA_PATH = "data/processed_csv/"

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.0-flash')


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "YOUR_API_KEY_HERE")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "YOUR_API_KEY_HERE")