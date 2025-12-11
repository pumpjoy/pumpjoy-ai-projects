# spark_steam_processor.py
# Takes stream from Kafka topic and calculates:
#   1. transaction count last 5 minutes.
#   2. average amount last 10 minutes.
# Load AI-IsolationForest Model for anomaly detection | Real-time fraud score.
# Publish result of original transaction, features, & fraud score to new Kafka topic


from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# Schema of the incoming JSON data from the Kafka producer
transaction_schema = StructType([
    StructField("id", IntegerType()),
    StructField("timestamp", DoubleType()),
    StructField("message", StringType()),
    StructField("status", StringType())
])

# Initialize Spark Session
# Configure Kafka package (JAR) for connectivity
spark = SparkSession \
    .builder \
    .appName("RealTimeFraudPipeline") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7") \
    .getOrCreate()

# Suppress log noise
spark.sparkContext.setLogLevel("ERROR")

#########################
# Kafka configuration
KAFKA_BROKER = 'broker:29092'  # Using internal service name and port
TOPIC_NAME = 'test_topic'

# Define Streaming Source (Kafka)
kafka_stream_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", TOPIC_NAME) \
    .option("startingOffsets", "earliest") \
    .load()
#########################

# Stream Transformation and Feature Engineering
# Parse JSON string value column and apply the schema
processed_df = kafka_stream_df \
    .selectExpr("CAST(value AS STRING) as json_value") \
    .select(from_json(col("json_value"), transaction_schema).alias("data")) \
    .select("data.*", current_timestamp().alias("processing_time")) \
    .withColumn("feature_example", col("id") * 100) # <-- Placeholder for a feature calculation

print("Starting Spark Structured Streaming job...")

# Define the Streaming Sink (Output)
# For first test, simply write the output to the console.
query = processed_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start()

# Keep query running until terminated 
query.awaitTermination()