# Dockerfile
# Start from the official Spark image you are using
FROM apache/spark:3.5.7-scala2.12-java11-python3-ubuntu

USER root

# Clean slate: Ensure we use the correct Python executable for pip
RUN apt-get update && \
    apt-get install -y python3-pip

RUN pip install pandas numpy scikit-learn

# Ensure requirements.txt is copied
# COPY requirements.txt /tmp/requirements.txt

# Install all packages using the '--no-cache-dir' to avoid the warning, 
# and directly into the system's default site-packages path, where PySpark looks.
# Note: We rely on the system's default path now, not a custom one.
# RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Clean up apt lists to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

USER spark