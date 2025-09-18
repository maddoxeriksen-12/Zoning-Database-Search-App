FROM python:3.11-slim

# System deps for Camelot + fonts
RUN apt-get update && apt-get install -y \
    ghostscript python3-tk tesseract-ocr libglib2.0-0 \
    libsm6 libxext6 libxrender1 libgl1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/ /app/worker/
ENV PYTHONUNBUFFERED=1

WORKDIR /app/worker
CMD ["python", "main.py"]
