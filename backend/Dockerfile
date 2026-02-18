# Use official Python image (Linux-based)
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy dependency files first
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy rest of your app code
COPY . .

# Expose app port (change if needed)
EXPOSE 8000

# Start your app (change if needed)
CMD ["python", "main.py"]
