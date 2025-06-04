# Python HTTP Server

This project sets up a simple HTTP server using Python with a POST endpoint `/question` that echoes back the data received in the request.

## Project Structure

```
python-http-server
├── src
│   └── app.py
├── Pipfile
├── Pipfile.lock
├── Dockerfile
└── README.md
```

## Requirements

- Python 3.8 or higher
- Pipenv for managing dependencies

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd python-http-server
   ```

2. **Install dependencies:**

   Make sure you have Pipenv installed. If not, you can install it using pip:

   ```bash
   pip install pipenv
   ```

   Then, run:

   ```bash
   pipenv install
   ```

3. **Run the server:**

   You can run the server using Pipenv:

   ```bash
   pipenv run python src/app.py
   ```

   The server will start on `http://localhost:8081`.

## Docker Instructions

To build and run the Docker container, use the following commands:

1. **Build the Docker image:**

   ```bash
   docker build -t python-http-server .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -p 8081:8081 python-http-server
   ```

The server will be accessible at `http://localhost:8081`.

## Usage

To test the `/question` endpoint, you can use `curl` or any API testing tool like Postman. Here’s an example using `curl`:

```bash
curl -X POST http://localhost:8081/question -d '{"question": "What is your name?"}' -H "Content-Type: application/json"
```

The server will respond with the same data you sent in the request.