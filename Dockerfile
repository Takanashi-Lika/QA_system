FROM python:3.10.10-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag/ ./rag/
COPY model/ ./model/
COPY retriever/ ./retriever/
COPY api/ ./api/
COPY rag_resource/ ./rag_resource/
COPY .env ./

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
