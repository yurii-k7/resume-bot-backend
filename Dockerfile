FROM python:3.12-slim

# Install pipenv and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential && \
    pip install --upgrade pip pipenv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Pipfile and Pipfile.lock first for better caching
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of the code
COPY src ./src
COPY faiss_index ./faiss_index

# Expose port
EXPOSE 8081

# Run the app
CMD ["pipenv", "run", "python", "src/app.py"]