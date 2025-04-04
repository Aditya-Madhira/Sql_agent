# main.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Check if Ollama is running before importing agent
def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            logger.info("Ollama service is running")
            return True
        else:
            logger.error(f"Ollama returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("Ollama service is not running. Please start Ollama first.")
        return False


# Try to connect to Ollama
max_retries = 3
for i in range(max_retries):
    if check_ollama():
        break
    if i < max_retries - 1:
        logger.info(f"Waiting for Ollama to start... (attempt {i + 1}/{max_retries})")
        time.sleep(5)
    else:
        logger.warning("Proceeding without confirmed Ollama connection")

# Now import agent after checking for Ollama
try:
    from database import initialize_database

    # Explicitly initialize database before setting up agent
    initialize_database()

    # Check if database file exists
    DB_FILE = "employee_database.db"
    if not os.path.exists(DB_FILE):
        logger.error(f"Database file {DB_FILE} not found after initialization")
    else:
        logger.info(f"Database file {DB_FILE} exists")

    # Import agent after database is initialized
    from agent import process_agent_query

    logger.info("Successfully imported agent")
except Exception as e:
    logger.error(f"Error during initialization: {e}")
    raise

app = FastAPI(title="Employee Query API with AI Agent Integration")

# Add CORS middleware to allow cross-origin requests from the Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/query")
def get_query(
    query: str = Query(..., description="The query to process."),
    conversation_id: Optional[str] = Query(None, description="Optional conversation ID for memory continuity.")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")

    # Process the query using the agent from agent.py
    try:
        result = process_agent_query(query, conversation_id)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)


# Add a health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)