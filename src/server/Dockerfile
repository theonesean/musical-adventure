FROM python:3.12.4-slim-bullseye

RUN mkdir /app
COPY . ./app
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install poetry
RUN poetry config virtualenvs.in-project true --local \ 
    && poetry install --no-dev --no-interaction --no-ansi

ENV PROJECT_ID=""

EXPOSE 8080

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]