# Use the official Alpine Linux as a base image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY pyproject.toml ./

# Copy the rest of the application code
COPY . .
  
# Install the project (after copying source so build can find package)
RUN pip install --no-cache-dir uv && uv pip install --system .

# Expose service port
EXPOSE 8000

# Set the entrypoint for the container
COPY docker-entrypoint.sh .

ENTRYPOINT ["./docker-entrypoint.sh"]
