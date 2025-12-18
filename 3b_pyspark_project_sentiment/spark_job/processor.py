# producers/processors.py
# Uses Pandas UDF
import time
import sys
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import ( 
    col, pandas_udf,
    window, avg 
)
from pyspark.sql.types import (
    StructType, StructField, 
    StringType, LongType, DoubleType, TimestampType
    )
from pyspark.sql import functions as F

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
@pandas_udf(DoubleType())
def analyze_sentiment_score(text_series: pd.Series) -> pd.Series:
    """Returns 1.0 for POSITIVE and 0.0 for NEGATIVE to allow averaging"""
    pipe = get_pipeline()
    
    # Transformers pipeline handles lists of strings efficiently
    # Truncation=True handles tweets longer than the model's limit
    results = pipe(text_series.tolist(), truncation=True, max_length=512)
    
    # Extract just the label (e.g., 'POSITIVE') from the result
    return pd.Series([1.0 if r['label'] == 'POSITIVE' else 0.0 for r in results])

# Read Kafka topic. Ensured similar to price_producer.py
 
def read_kafka_topic(spark, topic, schema):
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .load() \
        .selectExpr("CAST(value AS STRING) as json_payload") \
        .select(F.from_json("json_payload", schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", F.current_timestamp())

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
    social_schema = StructType([
        StructField("username", StringType(), True), # Add this
        StructField("text", StringType(), True),
        StructField("timestamp", LongType(), True)
    ])

    price_schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("timestamp", LongType(), True)
    ])

    # 3. Read both streams 
    social_raw = read_kafka_topic(spark, "crypto_social", social_schema)
    price_raw = read_kafka_topic(spark, "crypto_price", price_schema)
    
    # 4. Process and Watermarking
    # Allow 1 minute for late data to arrive on either side
    social_processed = social_raw \
        .withColumn("sentiment_score", analyze_sentiment_score(col("text"))) \
        .withWatermark("timestamp", "20 seconds")

    price_processed = price_raw \
        .withWatermark("timestamp", "20 seconds")

    # 5. Windowed Aggregation 
    # Group by 1 minute blocks 
    social_avg = social_processed.groupBy(window("timestamp", "10 seconds")) \
        .agg(avg("sentiment_score").alias("hype_score"))

    price_avg = price_processed.groupBy(window("timestamp", "10 seconds")) \
        .agg(avg("price").alias("avg_price"))

    # 6. Join the df together
    # Join the two 1-minute buckets together
    final_df = price_avg.join(social_avg, "window", "left") \
    .select(
        col("window.start").alias("time"),
        col("avg_price"),
        # F.coalesce picks the first non-null value. 
        # If hype_score is null, it returns 0.0.
        F.coalesce(col("hype_score"), F.lit(0.0)).alias("hype_score")
    )
    
    # 7. Output to Postgres
    # Using 'update' mode so we see results as windows close
    query = final_df.writeStream \
        .outputMode("append") \
        .foreachBatch(lambda df, epoch_id: df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://localhost:5432/hype_db") \
            .option("dbtable", "realtime_hype") \
            .option("user", "user") \
            .option("password", "password") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()) \
        .start()
    
    # Also print to console for immediate feedback
    console_query = final_df.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()

    
    # debug_price = spark.readStream \
    #     .format("kafka") \
    #     .option("kafka.bootstrap.servers", "localhost:9092") \
    #     .option("subscribe", "crypto_price") \
    #     .option("startingOffsets", "earliest") \
    #     .load() \
    #     .selectExpr("CAST(value AS STRING) as raw_json")

    # # Assign it to a variable so we can await it
    # debug_query = debug_price.writeStream \
    #     .format("console") \
    #     .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()