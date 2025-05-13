from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from src.backend.core.config import LOG_LEVEL
from src.backend.routes.get_company_route import company_process_router
from src.backend.routes.visualize_data_route import visualize_data_router
from src.backend.routes.chatbot_route import chatbot_router

#Set up logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

#Initialize FastAPI app
app = FastAPI()

#Define allowed CORS origins
origins = ["http://localhost",
           "http://localhost:8502",
           "http://127.0.0.1:8000",
           "http://192.168.1.142:8501"]

#Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Include route modules
app.include_router(company_process_router)
app.include_router(visualize_data_router)
app.include_router(chatbot_router)


#Run app with uvicorn
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)