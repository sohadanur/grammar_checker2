from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import logging
from database import get_db_connection
from models import CorrectionRequest, CorrectionResponse
import mysql.connector

# Load environment variables
load_dotenv()

#Configure Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

 # Configure Gemini API Key
genai.configure(api_key="AIzaSyDBOOe6YewFRdWAnSNevYc1BAPT2A_ZojE")  # Add your API key here

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

def count_words(text: str) -> int:
    """Count words in the text."""
    return len(re.findall(r'\b\w+\b', text))

def get_db_connection():
    """Establish a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to MySQL: {err}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.post("/check-text", response_model=CorrectionResponse)
async def check_text(request: CorrectionRequest):
    """
    Checks grammar, spelling, and punctuation in the given student response.
    """
    logging.info("Received request for text correction")
    
    word_count = count_words(request.student_question)

    # Validate word count (between 5 and 550 words)
    if word_count < 5 or word_count > 550:
        logging.error("Text must be between 5 and 550 words.")
        raise HTTPException(status_code=400, detail="Text must be between 5 and 550 words.")

    try:
        # Load Gemini model
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Please correct the following text for grammar, spelling, and punctuation errors: \n\n{request.student_question}"
        response = model.generate_content(prompt)

        # Validate API response
        if not response.text:
            logging.error("No valid response from API")
            raise HTTPException(status_code=500, detail="No valid response from API")
        
        corrected_text = response.text.strip()

        # Store in MySQL
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO corrections (exam_id, student_id, student_question, student_answer)
            VALUES (%s, %s, %s, %s)
        """, (request.exam_id, request.student_id, request.student_question, corrected_text))
        connection.commit()
        cursor.close()
        connection.close()

        logging.info("Text correction successful")
        return {
            "original": request.student_question,
            "student_answer": corrected_text
        }

    except Exception as e:
        logging.error(f"Error during text correction: {str(e)}")
        if "429" in str(e):
            raise HTTPException(status_code=429, detail="API quota exceeded. Try again later or reduce request frequency.")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-corrections")
async def get_corrections():
    """
    Fetches all stored corrections from MySQL.
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT exam_id, student_id, student_question, student_answer, created_at FROM corrections ORDER BY created_at DESC")
    corrections = cursor.fetchall()
    cursor.close()
    connection.close()
    return {"corrections": corrections}
