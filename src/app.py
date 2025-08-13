from flask import Flask, request, jsonify
from flask_cors import CORS
from answer import answer
import json
import logging
import time
import uuid
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom logger for chatbot interactions
chatbot_logger = logging.getLogger('chatbot_interactions')
chatbot_logger.setLevel(logging.INFO)

def log_chatbot_interaction(session_id, question, answer_text, response_time, success=True, error=None):
    """Log detailed chatbot interaction data"""
    interaction_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "question": question,
        "answer": answer_text,
        "response_time_ms": response_time,
        "success": success,
        "error": error,
        "user_agent": request.headers.get('User-Agent', ''),
        "ip_address": request.remote_addr,
        "environment": os.getenv('FLASK_ENV', 'development')
    }
    
    # Log as structured JSON for easy parsing by CloudWatch
    chatbot_logger.info(json.dumps(interaction_data))
    
    # Also log basic metrics
    logger.info(f"CHATBOT_INTERACTION - Session: {session_id}, ResponseTime: {response_time}ms, Success: {success}")

@app.route('/question', methods=['POST'])
def question():
    start_time = time.time()
    session_id = str(uuid.uuid4())
    question_text = ""
    answer_text = ""
    
    try:
        logger.info(f"Received question request - Session: {session_id}")
        
        data = request.json
        if not data:
            raise ValueError("No JSON data provided")
            
        question_text = data.get("question", "")
        if not question_text:
            raise ValueError("No question provided")
            
        logger.info(f"Processing question - Session: {session_id}, Question length: {len(question_text)}")
        
        # Process the question
        answer_text = answer(question_text)
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Log successful interaction
        log_chatbot_interaction(
            session_id=session_id,
            question=question_text,
            answer_text=answer_text,
            response_time=response_time,
            success=True
        )
        
        response = {
            "answer": answer_text,
            "session_id": session_id
        }
        
        logger.info(f"Successfully processed question - Session: {session_id}, ResponseTime: {response_time}ms")
        return response, 200
        
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        error_message = str(e)
        
        # Log failed interaction
        log_chatbot_interaction(
            session_id=session_id,
            question=question_text,
            answer_text="",
            response_time=response_time,
            success=False,
            error=error_message
        )
        
        logger.error(f"Error processing question - Session: {session_id}, Error: {error_message}")
        
        return jsonify({
            "error": "Failed to process question",
            "session_id": session_id
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv('FLASK_ENV', 'development')
    }, 200

@app.route('/')
def root():
    logger.info("Root endpoint accessed")
    return "Resume Bot API - Ready", 200

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} - {request.method} {request.url}")
    return response

if __name__ == '__main__':
    logger.info("Starting Resume Bot Flask application")
    # Use environment variable for host, default to localhost for security
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '8081'))
    app.run(host=host, port=port)