# producers/processors.py
# Uses Pandas UDF
import sys
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, pandas_udf
from pyspark.sql.types import StructType, StructField, StringType, LongType

# --- AI CONFIGURATION ---
from transformers import pipeline

sentiment_pipeline = None

def get_pipeline():
    """
    Singleton pattern to ensure the model is loaded only once per executor,
    not for every batch of data.
    """
    global sentiment_pipeline
    if sentiment_pipeline is None:
        # Load pre-trained model
        sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return sentiment_pipeline

# --- SPARK AI UDF ---
@pandas_udf(StringType())
def analyze_sentiment(text_series: pd.Series) -> pd.Series:
    """
    Receives a batch of tweets (pandas Series), feeds them to the AI,
    and returns a batch of labels (POSITIVE/NEGATIVE).
    """
    pipe = get_pipeline()
    
    # Transformers pipeline handles lists of strings efficiently
    # Truncation=True handles tweets longer than the model's limit
    results = pipe(text_series.tolist(), truncation=True, max_length=512)
    
    # Extract just the label (e.g., 'POSITIVE') from the result
    return pd.Series([r['label'] for r in results])

# --- MAIN JOB ---
def main():
    # 1. Initialize Spark Session
    # Include the Kafka jar package required to read streams
    spark = SparkSession.builder \
        .appName("CryptoHypeMeter") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # 2. Define Schema for Incoming Data
    # Must match the JSON sent by social_producer.py
    schema = StructType([
        StructField("username", StringType()),
        StructField("text", StringType()),
        StructField("timestamp", LongType())
    ])

    # 3. Read from Kafka
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "crypto_social") \
        .option("startingOffsets", "latest") \
        .load()

    # 4. Parse JSON Data
    # Kafka sends bytes; cast to string -> parse JSON -> extract fields
    tweets_df = kafka_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*")

    # 5. Apply AI Transformation
    # Adds a new column 'sentiment' to our stream
    processed_df = tweets_df.withColumn("sentiment", analyze_sentiment(col("text")))

    # 6. Output to Console (Debugging)
    # Print the table to terminal every few seconds
    query = processed_df.writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", "false") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()