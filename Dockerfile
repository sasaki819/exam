# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install system dependencies if any (e.g., for psycopg2, though slim often has them)
# For psycopg2, build-essential and libpq-dev might be needed if not using a binary.
# However, psycopg2-binary is used in requirements.txt, which usually avoids this.
# RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose port
EXPOSE 8000

# Command to run app
# For a production-like setup without reload:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
