import os
import logging
from langchain_pinecone import PineconeVectorStore
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chains import LLMMathChain
from src.backend.core.config import GOOGLE_API_KEY, LLM_MODEL, EMBEDDING_MODEL, PINECONE_API_KEY, PINECONE_INDEX_NAME


llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0)
embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)

#Pinecone Setup
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

#Tool 1: Financial Data Retriever
def get_financial_data(query: str) -> str:
    print(f"\n---> FinancialDataRetriever Tool called with query: {query}")
    try:
        vector_store = PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings,
        )

        #Enhanced retrieval prompt to get more relevant context
        search_query = f"Financial information about {query}"
        docs = vector_store.similarity_search(search_query, k=5)
        if not docs:
            return "No relevant financial information found for your query."
        
        #prompt template for formatting guidance
        qa_prompt_template = """
        You are a professional financial analyst with expertise in interpreting corporate financial data. 
        
        CONTEXT INFORMATION:
        {context}
        
        USER QUESTION: 
        {question}
        
        INSTRUCTIONS:
        1. Analyze the context carefully to find the exact information requested
        2. When discussing financial quarters, remember that Q1 ends in March, Q2 in June, Q3 in September, and Q4 in December
        3. Present monetary values with appropriate currency symbols and formatting
        4. Include year-over-year or quarter-over-quarter comparisons when that data is available
        5. If precise information isn't available in the context, acknowledge this and provide the closest relevant information
        6. For ratios and percentages, explain what they indicate about the company's performance
        7. If absolutely no relevant information is found, state: "I could not find that specific information in the available financial data."
        
        ANSWER:
        """
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=qa_prompt_template
        )

        #Run chain
        chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
        response = chain.invoke({"input_documents": docs, "question": query})
        result = response.get("output_text", "Could not process the financial data.")
        print(f"---> FinancialDataRetriever Tool output: {result}")
        return result

    except Exception as e:
        logging.error(f"Error in FinancialDataRetriever tool: {e}")
        return f"An error occurred while trying to retrieve financial data: {str(e)}"

#Tool register
financial_data_retriever_tool = Tool(
    name="FinancialDataRetriever",
    func=get_financial_data,
    description="""Use this tool to find specific financial information such as revenue, profit margins, EBITDA, operating income, 
    expenses, debt, cash flow, balance sheet items, or other financial metrics for a company at a specific date or period. 
    The tool works best when you provide the company name, specific financial metric, and time period in your query. 
    Remember that financial quarters end in March (Q1), June (Q2), September (Q3), and December (Q4)."""
)

#Tool 2: Calculator
calculator_chain = LLMMathChain.from_llm(llm=llm, verbose=True)
calculator_tool = Tool(
    name="Calculator",
    func=calculator_chain.run,
    description="""Use this tool for financial calculations including:
    - Basic arithmetic (addition, subtraction, multiplication, division)
    - Percentage calculations (growth rates, profit margins, etc.)
    - Financial ratios (P/E, debt-to-equity, current ratio, etc.)
    - Time value of money calculations (NPV, IRR, compound interest)
    - Weighted averages and other financial metrics
    Provide the complete mathematical expression to evaluate."""
)


#Tools
tools = [financial_data_retriever_tool, calculator_tool]

# Standard ZERO_SHOT_REACT_DESCRIPTION agent without custom prompt
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10,
    early_stopping_method="generate"
)

#system message to enhance the agent behavior
system_message = """You are a professional financial analyst assistant with expertise in corporate finance, financial reporting, and investment analysis.

Your primary goal is to provide accurate, detailed financial insights based on available company data.

Important financial guidelines:
- Financial quarters end in March (Q1), June (Q2), September (Q3), and December (Q4)
- When calculating growth rates, use (New Value - Old Value) / Old Value * 100%
- Distinguish between absolute values and percentages
- Provide context when sharing financial metrics (industry averages, historical trends)
- Be precise with financial terminology and transparent about data limitations

When analyzing financial data:
1. First retrieve the necessary raw financial information
2. Perform any required calculations to derive meaningful insights
3. Interpret the results in business context
4. Present findings clearly with appropriate financial terminology
5. Note any important caveats or limitations in the data

Remember to approach all financial questions methodically and precisely.
Provide answers ONLY for financial problems and greetings. For Other cases say you are not aware."""

#Set the system message for the LLM
llm.client.system = system_message

#Query handler
async def query_process_agent(query: str)-> str:
    logging.info(f"\nFinancial Analyst Assistant")
    logging.info(f"Question: {query}")
    try:
        response = agent_executor.invoke({"input": query})
        final_answer = response.get("output", "The financial analyst could not determine an answer.")
        logging.info(f"\nFinancial Analysis Result: {final_answer}")
        return final_answer
    
    except Exception as e:
        logging.error(f"Error during agent execution: {e}")
        if "Could not parse LLM output:" in str(e):
            #Extract the actual parsing error message
            error_message = str(e).split("Could not parse LLM output:")[1].strip()
            logging.info(f"LLM Parsing Error Detail: {error_message}")
        return f"financial analyst got an error: {str(e)}"
