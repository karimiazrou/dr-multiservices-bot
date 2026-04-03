FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dr_multiservices_bot.py .

CMD ["python", "dr_multiservices_bot.py"]
