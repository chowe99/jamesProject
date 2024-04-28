# syntax=docker/dockerfile:1
FROM python:3.11.7-slim as base

# Prevents Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

ARG OPENAI_API_KEY

# Set the environment variable using the value of the build argument
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# Install system dependencies required for compiling certain Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    python3-dev \
    gfortran \
    apt-transport-https \
    ca-certificates \
    gnupg \
    curl \ 
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Download the GPG key and add it to the keyring directly
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud-google-keyring.gpg


COPY GOOGLE_TTS_API.json /app/service-account-file.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-file.json

WORKDIR /app

# Create a non-privileged user
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home "/nonexistent" \
    --shell "/sbin/nologin" --no-create-home --uid "${UID}" appuser

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Create the static directory in the correct location and change permissions
RUN chown -R appuser:appuser /app
RUN mkdir -p /app/app/static && chown -R appuser:appuser /app/app/static && chmod -R 755 /app/app/static




# Switch to the non-privileged user
USER appuser

# Expose the port that the application listens on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "run:app"]

