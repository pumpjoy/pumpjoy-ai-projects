A Real-Time AI Data Pipeline Toy Model.
Uses the following stack:
1. Data Generator - ~ | Simulate real-time transactions.
2. Message Broker - Apache Kafka | Data ingestion, high-throughput, low latency event bus.
3. Stream Processing - Apache Spark (PySpark) | Feature engineering and real-time inferencing.
4. AI/ML Model | Simple classifier focussing on deployment/serving.
5. Monitor/Dashboard - Prometheus & Grafana | Collect metrics (latency, throughput) and visualize pipeline.
6. Containerization - Docker | Bundles the services 