FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents ./agents
COPY graph ./graph
COPY tools ./tools
COPY vector_db ./vector_db
COPY ui ./ui
COPY tests ./tests
COPY eval ./eval
COPY foundry ./foundry
COPY settings.py logging_config.py llm_factory.py rate_limiter.py history_utils.py ./
COPY init.sql init_mssql.sql .

ENV PYTHONPATH=/code

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
