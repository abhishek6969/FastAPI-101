# ====================================================================
# DOCKERFILE - Development Environment
# ====================================================================
# Purpose: Build a containerized FastAPI development application
# Base Image: Python 3.13 (lightweight, latest stable)
# Use Case: Local development, testing, docker-compose environments
# Note: For production deployment, use Dockerfile.prd instead
# ====================================================================

# Use official Python 3.13 runtime as base image
FROM python:3.13

# Set working directory inside container where app files will be copied
WORKDIR /usr/src/app

# Copy requirements.txt first to leverage Docker layer caching
# If requirements don't change, this layer is cached and rebuild is faster
COPY requirements.txt ./

# Install Python dependencies from requirements.txt
# --no-cache-dir flag reduces image size by not storing pip cache in the image
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# Done after pip install to optimize layer caching
COPY . .

# Set the default command to run when container starts
# Starts Uvicorn server on all network interfaces (0.0.0.0) on port 8000
# --reload flag enables auto-restart on code changes (dev feature)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]



