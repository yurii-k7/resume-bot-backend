FROM python:3.9-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

COPY src/ ./src/

CMD ["pipenv", "run", "python", "src/app.py"]