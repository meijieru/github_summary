# Use the official Alpine Linux as a base image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY pyproject.toml ./
RUN pip install uv && uv pip install --system .

# Copy the rest of the application code
COPY . .

# Set the entrypoint for the container
COPY docker-entrypoint.sh .

ENTRYPOINT ["./docker-entrypoint.sh"]
