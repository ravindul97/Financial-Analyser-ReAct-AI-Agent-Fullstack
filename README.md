# Quarterly Financial Analyser with LangChain, FastAPI and Streamlit

This project provides a comprehensive solution for extracting and analyzing financial data from quarterly reports of companies listed on the Colombo Stock Exchange (CSE). It includes web scraping capabilities, data visualization through an interactive dashboard, and an AI-Agentic query system.

------------------------------------------------------------------------

### Features

- **Web Scraping**: Scrape financial reports for a specified company.
- **Dataset Creation**: Creates structured datasets of key financial metrics for P&L statements
- **Dashboard**: Visualizes financial trends and enables comparative analysis
- **Chatbot**: Ask questions about the financial data.

### RAG Components

- **LLM**: gemini-2.0-flash.
- **Text Embedding Model**: models/embedding-001
- **Vector Database**: Pinecone
- **Framework**: LangChain

------------------------------------------------------------------------

### System Requirements

- Python 3.10+
- Pip package manager 
- Internet connection for accessing data
- Chrome web browser
- 1GB of free disk space
- Gemini API Key, Pinecone API Key

------------------------------------------------------------------------

### Setup Instructions

#### 1. Clone the Repository

    git clone https://github.com/ravindul97/financial-analyser-ai-agent.git
    cd financial-analyser-ai-agent

#### 2. Create and activate a virtual environment:
##### Windows:
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

##### macOS/Linux:
    python -m venv .venv
    source .venv/bin/activate

#### 3. Install the required dependencies:
    pip install -r requirements.txt

#### 4. Using Environment Variables
##### create a .env file in the root directory with below keys or modify the src/backend/core/config.py file. (API Keys are in Final Report-Appendix 2)
    GOOGLE_API_KEY=your_google_api_key_here
    PINECONE_API_KEY=your_pinecone_api_key_here
    PINECONE_INDEX_NAME=your_pinecone_index_name_here


------------------------------------------------------------------------

### Running the Application
The application consists of two main components: 
The backend API and the frontend interface. Both need to be running simultaneously.

#### Step 1: Start the Backend Server

1. Open a terminal and navigate to the project root directory.

2. Activate the virtual environment (if not activated):
##### Windows:
    .\.venv\Scripts\Activate.ps1

##### macOS/Linux:
    source .venv/bin/activate

3. Start the FastAPI backend server:
##### Run:
    python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload

4. The backend API will be available at http://127.0.0.1:8000


#### Step 2: Launch the Frontend Dashboard

1. Open a new terminal window (keep the backend server running)

2. Navigate to the project root directory

3. Activate the virtual environment:
##### Windows:
    .\.venv\Scripts\Activate.ps1

##### macOS/Linux:
    source .venv/bin/activate

4. Start the Streamlit frontend application:
##### Run:
    python -m streamlit run src/frontend/app.py

5. The dashboard will open automatically in your default web browser at http://localhost:8501

------------------------------------------------------------------------

### Using the Application

1. Scrape Financial Data:
    - Enter the company name in the Streamlit interface (one by one)
    - Click the scrape button to extract financial reports
    - Wait for the "Scrape completed" confirmation message

2. Visualize Data:
    - Click the "Visualize" button to generate graphs
    - After processing (may take a few minutes), the dashboard will display

3. Analyze and Query:
    - Explore the interactive charts and tables
    
4. Agentic Chatbot:
    - Use the chatbot interface to ask questions about the financial data

------------------------------------------------------------------------

### Uninstall/Remove Environments
##### windows
    deactivate  

------------------------------------------------------------------------

### Documentation
Access the Swagger UI documentation: http://127.0.0.1:8000/docs

