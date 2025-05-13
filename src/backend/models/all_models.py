from pydantic import BaseModel

#Company name model
class CompanyData(BaseModel):
    name: str

#Data visualization model
class VisualizeData(BaseModel):
    name: str

#model for chatbot
class ChatData(BaseModel):
    query: str
