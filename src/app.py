"""Flask API for Resume Bot backend."""
import json
import logging
import os
import time
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from answer import answer

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

def log_chatbot_interaction(session_id, user_question, answer_text, response_time,
                          success=True):
    """Log detailed chatbot interaction data"""
    interaction_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "question": user_question,
        "answer": answer_text,
        "response_time_ms": response_time,
        "success": success,
        "error": None,
        "user_agent": request.headers.get('User-Agent', ''),
        "ip_address": request.remote_addr,
        "environment": os.getenv('FLASK_ENV', 'development')
    }

    # Log as structured JSON for easy parsing by CloudWatch
    chatbot_logger.info(json.dumps(interaction_data))

    # Also log basic metrics
    logger.info("CHATBOT_INTERACTION - Session: %s, ResponseTime: %sms, Success: %s",
                session_id, response_time, success)

@app.route('/question', methods=['POST'])
def question():
    """Handle question requests from users."""
    start_time = time.time()
    session_id = str(uuid.uuid4())
    question_text = ""
    answer_text = ""

    try:
        logger.info("Received question request - Session: %s", session_id)

        data = request.json
        if not data:
            raise ValueError("No JSON data provided")

        question_text = data.get("question", "")
        if not question_text:
            raise ValueError("No question provided")

        logger.info("Processing question - Session: %s, Question length: %d",
                    session_id, len(question_text))

        # Process the question
        answer_text = answer(question_text)

        response_time = int((time.time() - start_time) * 1000)

        # Log successful interaction
        log_chatbot_interaction(
            session_id=session_id,
            user_question=question_text,
            answer_text=answer_text,
            response_time=response_time,
            success=True
        )

        response = {
            "answer": answer_text,
            "session_id": session_id
        }

        logger.info("Successfully processed question - Session: %s, ResponseTime: %sms",
                    session_id, response_time)
        return response, 200

    except Exception as e:  # pylint: disable=broad-exception-caught
        response_time = int((time.time() - start_time) * 1000)
        error_message = str(e)

        # Log failed interaction
        log_chatbot_interaction(
            session_id=session_id,
            user_question=question_text,
            answer_text="",
            response_time=response_time,
            success=False
        )

        logger.error("Error processing question - Session: %s, Error: %s",
                     session_id, error_message)

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
    """Root endpoint handler."""
    logger.info("Root endpoint accessed")
    return "Resume Bot API - Ready", 200

# Add request logging middleware
@app.before_request
def log_request_info():
    """Log incoming request information."""
    logger.info("Request: %s %s - IP: %s",
                request.method, request.url, request.remote_addr)

@app.after_request
def log_response_info(response):
    """Log outgoing response information."""
    logger.info("Response: %s - %s %s",
                response.status_code, request.method, request.url)
    return response

if __name__ == '__main__':
    logger.info("Starting Resume Bot Flask application")
    # Use environment variable for host, default to localhost for security
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '8081'))
    app.run(host=host, port=port)
