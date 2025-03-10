
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
# EXPOSE 80

# Define environment variable
ENV SERVICE_ACCOUNT_FILE="/app/service-account.json"

# Run aio.py when the container launches
CMD ["python", "/app/aio.py"]
