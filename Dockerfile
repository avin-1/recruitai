# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Install gunicorn for production serving
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Define environment variable
ENV PORT=10000

# Run wsgi.py when the container launches
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
