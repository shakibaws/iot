# Use the official Python image as a base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r python_libraries.txt

# Expose the port the app runs on
EXPOSE 5001

# Run the application
CMD ["python", "bot_notifier.py"]
