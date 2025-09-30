# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your FastAPI application runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "spoon_ai.agents.run_agent_server"]