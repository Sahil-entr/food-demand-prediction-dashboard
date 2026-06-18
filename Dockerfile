# Use an official lightweight Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt /code/

# Install system dependencies (build-essential for compiling C dependencies if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY . /code/

# Expose port 7860 (Hugging Face Spaces standard port)
EXPOSE 7860

# Run the Flask app using Gunicorn on port 7860 with a single worker
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:7860", "app:app"]
