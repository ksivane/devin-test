FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script into the container
COPY devin-pr.py .

# Inject the environment variable. Valid for couple days.
ENV GITHUB_TOKEN=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

# Run the script on container start
CMD ["python", "devin-pr.py"]
