# Use the official Python image as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY app /app

# Install the required packages
RUN pip install --no-cache-dir -r /app/requirements.txt

# Specify the command to run the application
CMD ["python", "/app/main.py"]

