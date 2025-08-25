FROM python:3.9-slim

WORKDIR /app

COPY python_libraries.txt .
RUN pip install --no-cache-dir -r python_libraries.txt

COPY . .

EXPOSE 5015

CMD ["python", "main.py"]
