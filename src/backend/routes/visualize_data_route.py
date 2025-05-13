import logging
import asyncio
from fastapi import APIRouter, status, HTTPException
from src.backend.core.config import API_VERSION
from src.backend.models.all_models import VisualizeData
from src.backend.services.extract_data import data_extractor
from src.backend.services.dataset_creation import create_dataset
from src.backend.services.rag_vector_save import rag_pipeline

#data visualize router
visualize_data_router = APIRouter(
    prefix="/visualize/"+ API_VERSION +"",
    tags=["visualize"],
    responses={404: {"description": "Not found"}}
)

#Data visualization endpoint
@visualize_data_router.post("/visualize_data", status_code=status.HTTP_200_OK)
async def visualize_data(request: VisualizeData):
    try:
        #Pdf data extraction
        logging.info(f"Data Extraction started")
        extract_result = await data_extractor()
        logging.info(f"extract_result: {extract_result}")

        #Dataset creation
        logging.info(f"Dataset Creation started")
        dataset_preperation_result = await create_dataset()
        logging.info(f"dataset_preperation_result: {dataset_preperation_result}")

        #Save the data in vector db
        asyncio.create_task(
            handle_rag_ingestor(
            )
        )

        return VisualizeData(name='done')
        
    except Exception as e:
        logging.error(f"Error in visualize data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#Data save in VectorDB
async def handle_rag_ingestor():
    try:
        logging.info('Rag Ingestion Started')
        result = await rag_pipeline()
        logging.info(f"result: {result}")

    except Exception as e:
        logging.error(f"Error in handle rag ingestor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
