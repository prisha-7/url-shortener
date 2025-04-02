# Use an official Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy source code to the container
COPY app.py requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
