import logging
from fastapi import APIRouter, status, HTTPException
from src.backend.core.config import API_VERSION
from src.backend.models.all_models import ChatData
from src.backend.services.rag_retriver import query_process_agent

#Define chatbot router
chatbot_router = APIRouter(
    prefix="/query/"+ API_VERSION +"",
    tags=["query"],
    responses={404: {"description": "Not found"}}
)

#Chatbot Endpoint for POST requests
@chatbot_router.post("/query_data", status_code=status.HTTP_200_OK)
async def query_data(request: ChatData):
    try:
        user_query = request.query
        logging.info(f"Recieved Query: {user_query}")

        #process the user query
        answer = await query_process_agent(user_query)
        logging.info(f"Answer: {answer}")

        return answer

    except Exception as e:
        logging.error(f"Error in query data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


