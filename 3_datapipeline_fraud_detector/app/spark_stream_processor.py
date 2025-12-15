from pyspark.sql import SparkSession
# FIX 1: Import the functions module using the standard alias 'F'
import pyspark.sql.functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, TimestampType
)

# --- CONFIGURATION ---
KAFKA_CONNECTOR_VERSION = "3.5.0"
KAFKA_BROKER = 'broker:29092' 
INPUT_TOPIC_NAME = 'test_topic'
OUTPUT_TOPIC_NAME = 'fraud_alerts'
CHECKPOINT_LOCATION = "/tmp/checkpoint/fraud_app"

# Schema definition (remains the same)
input_schema = StructType([
    StructField("user_id", IntegerType(), True),
    StructField("transaction_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("timestamp", StringType(), True) 
])

# --- 1. SPARK SESSION INITIALIZATION ---
spark = SparkSession \
    .builder \
    .appName("RealTimeFraudPipeline") \
    .config("spark.jars.packages", f"org.apache.spark:spark-sql-kafka-0-10_2.12:{KAFKA_CONNECTOR_VERSION}") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_LOCATION) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# --- 2. READ FROM KAFKA ---
kafka_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", INPUT_TOPIC_NAME) \
    .option("startingOffsets", "latest") \
    .load()

# --- 3. PARSE JSON AND WATERMARK ---
parsed_stream = kafka_stream.selectExpr("CAST(value AS STRING) as json_payload") \
    .select(F.from_json(F.col("json_payload"), input_schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", F.col("timestamp").cast(TimestampType())) \
    .withWatermark("event_time", "10 minutes")

# --- 4. FEATURE ENGINEERING (Windowed Aggregation) ---
# Calculate the number of transactions per user in a 5-minute sliding window
user_activity = parsed_stream \
    .groupBy(
        F.window(F.col("event_time"), "10 minutes", "5 minutes"),
        F.col("user_id")
    ) \
    .agg(
        F.count("transaction_id").alias("txn_count_5min"),
        F.avg("amount").alias("avg_amount_10min")
    ) \
    .withWatermark("window", "10 minutes") \
    .select(F.col("user_id"), F.col("txn_count_5min"), F.col("avg_amount_10min"), F.col("window"))

# --- 5. STATEFUL JOIN ---
# Join current transaction with the latest computed features (stateful)
final_features_df = parsed_stream.alias("txn") \
    .join(
        user_activity.alias("agg"),
        # 1. User ID Match
        (F.col("txn.user_id") == F.col("agg.user_id")) &
        # 2. Time-Based Range Condition (Crucial for Bounded State)
        # Match current transaction (txn.event_time) to the window end time (agg.window.end)
        # The transaction must fall within the aggregate's 10-minute window.
        (F.col("txn.event_time") >= F.col("agg.window.start")) &
        (F.col("txn.event_time") <= F.col("agg.window.end")),
        "inner"
    ) \
    .select(
        F.col("txn.*"),
        # The aggregated columns are still available
        F.col("agg.txn_count_5min"),
        F.col("agg.avg_amount_10min")
    )

# --- 6. RULES ENGINE DECISION (FINAL LOGIC) ---
HIGH_AMOUNT_THRESHOLD = 500.0   
HIGH_COUNT_THRESHOLD = 5 

final_alerts_df = final_features_df.withColumn(
    "is_fraud_alert", 
    F.when(
        (F.col("amount") > HIGH_AMOUNT_THRESHOLD) |
        (F.col("txn_count_5min").cast(IntegerType()) > HIGH_COUNT_THRESHOLD), 
        True
    ).otherwise(False)
).withColumn(
    # Provide a 'score' based on velocity for reporting/completeness
    "fraud_score", 
    F.col("txn_count_5min") / F.lit(10) 
)


# --- 7. WRITE TO KAFKA SINK ---
# Select and structure the final output
output_stream = final_alerts_df.select(
    F.to_json(
        F.struct(
            F.col("transaction_id"),
            F.col("user_id"),
            F.col("amount"),
            F.col("is_fraud_alert"),
            F.col("fraud_score")
        )
    ).alias("value")
)

# output_stream = parsed_stream.select(
#     F.to_json(
#         F.struct(
#             F.col("user_id"),
#             F.col("transaction_id")
#         )
#     ).alias("value")
# )

# Start the streaming query
query = output_stream \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("topic", OUTPUT_TOPIC_NAME) \
    .outputMode("append") \
    .start()

print("Starting Spark Structured Streaming job...")
query.awaitTermination()