FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port (Hugging Face Docker Space runs on 7860 by default)
EXPOSE 7860
ENV PORT=7860

# Launch server
CMD ["python", "app.py"]
