# Dockerfile
# Start from the official Spark image you are using
FROM jupyter/pyspark-notebook:spark-3.5.0

USER root

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Ensure the log directory exists and is writable by the non-root user
RUN mkdir -p /usr/local/spark/logs && \
    chown -R jovyan:users /usr/local/spark/logs

# Switch back to the default non-root user
USER jovyan 