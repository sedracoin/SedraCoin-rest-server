FROM python:3.10.12

WORKDIR /app

COPY Pipfile* ./

RUN pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

COPY . .

CMD ["pipenv", "run", "gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "127.0.0.1:8000", "main:app"]

