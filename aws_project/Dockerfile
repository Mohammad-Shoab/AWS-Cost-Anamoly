FROM python:3.9-slim-buster

# Set the working directory
WORKDIR /aws-cost-anomaly-detection

# Copy only the requirements file first for better caching
COPY requirements.txt /aws-cost-anomaly-detection/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create log directory and set permissions
RUN mkdir -p /var/log && \
    touch /var/log/stdin.log /var/log/stdout.log /var/log/stderr.log && \
    chmod -R 755 /var/log

# Copy the rest of your application code
COPY . /aws-cost-anomaly-detection

# Specify the command to run your application
CMD ["python3", "app.py"]
