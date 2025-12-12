# BUG: No Module (numpy._core) found. Could not find solution even after changing path.
# TODO: Switch to use jupyter/pyspark instead 

# spark_steam_processor.py
# Takes stream from Kafka topic and calculates:
#   1. transaction count last 5 minutes.
#   2. average amount last 10 minutes.
# Load AI-IsolationForest Model for anomaly detection | Real-time fraud score.
# Publish result of original transaction, features, & fraud score to new Kafka topic

import pandas as pd
import pickle
import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, 
    from_json, 
    to_json,
    window, 
    count, 
    avg, 
    current_timestamp, 
    pandas_udf,
    struct
)
from pyspark.sql.types import (
    StructType, 
    StructField, 
    StringType, 
    IntegerType, 
    DoubleType, 
    TimestampType
)

KAFKA_CONNECTOR_VERSION = "3.5.7"
KAFKA_BROKER = 'broker:29092' 
INPUT_TOPIC_NAME = 'test_topic'
CHECKPOINT_LOCATION = "/tmp/checkpoint/fraud_app"

MODEL_PATH = "/app/isolation_forest_model.pkl" 
FEATURE_COLUMNS = ["amount", "txn_count_5min", "avg_amount_10min"] 

OUTPUT_TOPIC_NAME = 'fraud_alerts'

# Schema of the incoming JSON data from the Kafka producer
transaction_schema = StructType([
    StructField("id", IntegerType()),
    StructField("user_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("timestamp", DoubleType()),
    StructField("message", StringType()),
    StructField("status", StringType())
])

# --- Initiate Spark Session ---
# Configure Kafka package (JAR) for connectivity
spark = SparkSession \
    .builder \
    .appName("RealTimeFraudPipeline") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_LOCATION) \
    .getOrCreate()

# Only log Error messages
spark.sparkContext.setLogLevel("ERROR")
print(f"Starting Spark Structured Streaming job with Kafka package v{KAFKA_CONNECTOR_VERSION}...")
print(f"Reading from broker: {KAFKA_BROKER}, topic: {INPUT_TOPIC_NAME}")

# --- Define Streaming Source (Kafka) ---
kafka_stream_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", INPUT_TOPIC_NAME) \
    .option("startingOffsets", "earliest") \
    .load()

# --- Base transformations (parse and clean) ---
# Create base df with Spark Timestamp column
base_df = kafka_stream_df \
    .selectExpr("CAST(value AS STRING) as json_value") \
    .select(from_json(col("json_value"), transaction_schema).alias("data")) \
    .select("data.*", current_timestamp().alias("processing_time")) \
    .withColumn("event_time", col("timestamp").cast(TimestampType()))
print("Starting Spark Structured Streaming job...")

# --- Stateful Feature Engineering ---
# Calculate the number of transactions per user (last 5 mins) and average amount (10 mins).

# Apply watermark. Define a 1-minute tolerance for late data
watermarked_df = base_df.withWatermark("event_time", "1 minute")

# Calculate feature of transaction Count in the last 5 minutes
# Group by user_id and a sliding window that ends every 1 minute
count_features_df = watermarked_df \
    .groupBy(
        window(col("event_time"), "5 minutes", "1 minute").alias("count_window"), 
        col("user_id")
    ) \
    .agg(
        count(col("id")).alias("txn_count_5min")
    ) \
    .select(
        col("count_window.end").alias("txn_count_window_end"),
        col("user_id"), # <-- NO ALIASING HERE
        col("txn_count_5min")
    )

# Calculate feature of average amount in the last 10 minutes
# Group by user_id and a sliding window that ends every 5 minute
avg_features_df = watermarked_df \
    .groupBy(
        window(col("event_time"), "10 minutes", "2 minutes").alias("avg_window"), 
        col("user_id")
    ) \
    .agg(
        avg(col("amount")).alias("avg_amount_10min")
    ) \
    .select(
        col("avg_window.end").alias("avg_amount_window_end"),
        col("user_id"),
        col("avg_amount_10min")
    )

# --- Join features back to original stream ---
# Prepares the data for model scoring by ensuring every original record 
# gets the latest feature value from its respective window.

# Join Original Stream with Count Feature (5 min)
count_joined_df = base_df.alias("original") \
    .join(
        count_features_df.alias("count_features"),
        on=[
            F.col("original.user_id") == F.col("count_features.user_id")
        ],
        how="left_outer"
    ) \
    .select(
        "original.*",
        F.col("count_features.txn_count_5min")
    )

# Join the Result (Count) with the Average Feature (10 min)
final_features_df = count_joined_df.alias("current") \
    .join(
        avg_features_df.alias("avg_features"),
        on=[
            F.col("current.user_id") == F.col("avg_features.user_id")
        ],
        how="left_outer"
    ) \
    .select(
        "current.*", # Contains original columns + txn_count_5min
        F.col("avg_features.avg_amount_10min") # Add the new average feature
    )

# Rename to 'scored_df' for Model Inference
scored_df = final_features_df

# --- Define Pandas UDF ---
# Load the pre-trained Isolation Forest model
try:
    with open(MODEL_PATH, 'rb') as f:
        ISOLATION_FOREST_MODEL = pickle.load(f)
except FileNotFoundError:
    print(f"ERROR: Model file not found at {MODEL_PATH}. Prediction will fail.")
    ISOLATION_FOREST_MODEL = None


# Define the Pandas UDF for real-time scoring
# Input is a Pandas Series/DataFrame, output is a Pandas Series (Score)
# The return type is DoubleType because the Isolation Forest decision_function returns a float score.
@pandas_udf(DoubleType())
def predict_fraud_score(iterator: pd.Series) -> pd.Series:
    """
    Applies the Isolation Forest model to batches of streaming data.
    
    Args:
        iterator (DataFrame): Pandaas Series/DataFrame 
    Return:
        DoubleType (DataFrame): Float score
    """
    if ISOLATION_FOREST_MODEL is None:
        return pd.Series([0.0] * len(iterator)) # Return safe score if model is missing

    data_batch = pd.DataFrame(iterator.tolist(), columns=FEATURE_COLUMNS)
    
    # 1. Apply the model's decision function (Anomaly score is the inverse of the distance)
    # The score tells us how "normal" a transaction is. Lower score = more anomalous.
    raw_scores = ISOLATION_FOREST_MODEL.decision_function(data_batch)

    # 2. Return the score as a Pandas Series
    # Higher score = more fraudulent (for clarity)
    return pd.Series(raw_scores * -1)

# --- Apply Model Inference ---
# Select the feature columns needed by the model and structure them for the UDF
model_input_df = scored_df.select(
    "*", # Keep all original columns and features
    struct(
        col("amount"),
        col("txn_count_5min"),
        col("avg_amount_10min")
    ).alias("model_features") # Package features into a single struct column
)

# Apply the Pandas UDF to generate the final fraud score
final_predictions_df = model_input_df.withColumn(
    "fraud_score", 
    predict_fraud_score(col("model_features"))
)

# Add a simple binary flag based on the score threshold (set artificial threshold of 0.05)
final_alerts_df = final_predictions_df.withColumn(
    "is_fraud_alert", 
    F.when(col("fraud_score") > 0.05, True).otherwise(False)
)


# --- Define Streaming Sink (Console Output) ---
# Select the final output columns and structure them
# Send a clean JSON payload containing the final decision
kafka_output_df = final_alerts_df.select(
    # Kafka requires 'key' and 'value' columns
    col("user_id").alias("key"), # Use user_id as the Kafka key
    to_json(
        struct(
            col("event_time").cast(StringType()).alias("alert_time"),
            col("user_id"),
            col("amount"),
            col("txn_count_5min"),
            col("avg_amount_10min"),
            col("fraud_score"),
            col("is_fraud_alert")
        )
    ).alias("value") # The complete payload as a JSON string
)

# 2. Write the stream to the new Kafka topic
print(f"\nWriting final alerts to Kafka topic: {OUTPUT_TOPIC_NAME}")
query = kafka_output_df \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("topic", OUTPUT_TOPIC_NAME) \
    .option("checkpointLocation", f"{CHECKPOINT_LOCATION}/kafka_sink") \
    .outputMode("append") \
    .start()

query.awaitTermination()