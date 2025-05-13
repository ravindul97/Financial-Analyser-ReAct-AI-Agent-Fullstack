import logging
from fastapi import APIRouter, status, HTTPException
from src.backend.core.config import API_VERSION, DIPPED_PLC_URL, RICHARD_PLC_URL
from src.backend.models.all_models import CompanyData
from src.backend.services.web_scrape import web_scrape

#Define company data scraping router
company_process_router = APIRouter(
    prefix="/company/"+ API_VERSION +"",
    tags=["company_name"],
    responses={404: {"description": "Not found"}}
)

#Company data scraping Endpoint
@company_process_router.post("/get_company_name", response_model=CompanyData, status_code=status.HTTP_200_OK)
async def company_process(request: CompanyData):
    try:
        company_name = request.name
        logging.info(f"Recieved company name: {company_name}")

        #for Dipped Products PLC Selected
        if 'dipped' in company_name.lower():
            logging.info(f"Dipped Products PLC Selected")
            result = await web_scrape(DIPPED_PLC_URL)
            logging.info(f"result: {result}")

            return CompanyData(name='Scrape Completed: Dipped Products PLC')
        
        #for Richard Pieris Exports PLC  Selected
        elif 'richard' in company_name.lower():
            logging.info(f"Richard Pieris Exports PLC  Selected")
            result = await web_scrape(RICHARD_PLC_URL)
            logging.info(f"result: {result}")
            
            return CompanyData(name='Scrape Completed: Richard Pieris Exports PLC')
        
        #for other companies
        else:
            logging.info(f"Company is not in List")
            return CompanyData(name='Invalid Company name')

    except Exception as e:
        logging.error(f"Error in get company name endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


