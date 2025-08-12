import json
import logging
import time
import uuid
from datetime import datetime
import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from answer import answer

# Configure structured logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')

def get_secret(secret_arn):
    """Retrieve secret from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_arn}: {e}")
        raise e

def setup_environment():
    """Set up environment variables from AWS Secrets Manager"""
    secret_mappings = {
        'OPENAI_API_KEY_SECRET_ARN': 'OPENAI_API_KEY',
        'PINECONE_API_KEY_SECRET_ARN': 'PINECONE_API_KEY', 
        'LANGSMITH_API_KEY_SECRET_ARN': 'LANGSMITH_API_KEY'
    }
    
    for secret_arn_env, env_var in secret_mappings.items():
        secret_arn = os.environ.get(secret_arn_env)
        if secret_arn and env_var not in os.environ:
            try:
                secret_value = get_secret(secret_arn)
                os.environ[env_var] = secret_value
                logger.info(f"Successfully loaded {env_var} from secrets manager")
            except Exception as e:
                logger.error(f"Failed to load {env_var} from secrets manager: {e}")

# Set up environment on import
setup_environment()

# Custom logger for chatbot interactions
chatbot_logger = logging.getLogger('chatbot_interactions')
chatbot_logger.setLevel(logging.INFO)

def log_chatbot_interaction(session_id, question, answer_text, response_time, success=True, error=None, event=None):
    """Log detailed chatbot interaction data"""
    interaction_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "question": question,
        "answer": answer_text,
        "response_time_ms": response_time,
        "success": success,
        "error": error,
        "user_agent": event.get('headers', {}).get('User-Agent', '') if event else '',
        "ip_address": event.get('requestContext', {}).get('identity', {}).get('sourceIp', '') if event else '',
        "environment": os.getenv('FLASK_ENV', 'production')
    }
    
    # Log as structured JSON for easy parsing by CloudWatch
    chatbot_logger.info(json.dumps(interaction_data))
    
    # Also log basic metrics
    logger.info(f"CHATBOT_INTERACTION - Session: {session_id}, ResponseTime: {response_time}ms, Success: {success}")

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    start_time = time.time()
    session_id = str(uuid.uuid4())
    question_text = ""
    answer_text = ""
    
    try:
        logger.info(f"Lambda invoked - Session: {session_id}, Event: {json.dumps(event)}")
        
        # Handle different event structures (API Gateway, ALB, direct invocation)
        if 'httpMethod' in event:
            # API Gateway event
            method = event['httpMethod']
            path = event.get('path', '/')
            body = event.get('body', '{}')
            headers = event.get('headers', {})
        elif 'requestContext' in event and 'http' in event['requestContext']:
            # API Gateway v2 event
            method = event['requestContext']['http']['method']
            path = event['requestContext']['http']['path']
            body = event.get('body', '{}')
            headers = event.get('headers', {})
        else:
            # Direct invocation or other event types
            method = 'POST'
            path = '/question'
            body = json.dumps(event) if isinstance(event, dict) else str(event)
            headers = {}
        
        logger.info(f"Processing {method} {path} - Session: {session_id}")
        
        # Health check endpoint
        if path == '/health' or path == '/' and method == 'GET':
            response_time = int((time.time() - start_time) * 1000)
            logger.info(f"Health check - Session: {session_id}, ResponseTime: {response_time}ms")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "environment": os.getenv('FLASK_ENV', 'production')
                })
            }
        
        # Root endpoint
        if path == '/' and method == 'GET':
            response_time = int((time.time() - start_time) * 1000)
            logger.info(f"Root endpoint - Session: {session_id}, ResponseTime: {response_time}ms")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/plain',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': "Resume Bot API - Ready"
            }
        
        # Handle OPTIONS for CORS
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': ''
            }
        
        # Question endpoint
        if method == 'POST' and (path == '/question' or path == '/'):
            # Parse the request body
            try:
                if isinstance(body, str):
                    data = json.loads(body) if body else {}
                else:
                    data = body
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in request body: {e}")
            
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
                success=True,
                event=event
            )
            
            response_body = {
                "answer": answer_text,
                "session_id": session_id
            }
            
            logger.info(f"Successfully processed question - Session: {session_id}, ResponseTime: {response_time}ms")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps(response_body)
            }
        
        # Unknown endpoint
        logger.warning(f"Unknown endpoint - Session: {session_id}, Method: {method}, Path: {path}")
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                "error": "Endpoint not found",
                "session_id": session_id
            })
        }
        
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
            error=error_message,
            event=event
        )
        
        logger.error(f"Error processing request - Session: {session_id}, Error: {error_message}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                "error": "Failed to process request",
                "session_id": session_id,
                "message": error_message
            })
        }