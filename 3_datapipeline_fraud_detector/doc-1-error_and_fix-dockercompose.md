# Document: Docker-Compose | Errors & Fixes 
- This document takes notes on errors encountered whilst setting up docker-compose.yaml

---
# Kafka
## Error: `kafka.errors.NoBrokersAvailable`
### Tl;Dr:
- Source: Followed tutorial which uses `confluentinc/cp-kafka` image that can automatically set listener configurations, where the listener is set to `PLAINTEXT`. As this project uses `apache/kafka` image, Kafka Broker configuration used `localhost` for its listeners, meaning the broker was only listening internally within the container and could not be reached by the host machine.
- Solution: Implemented a **Dual Listener** setup (`INTERNAL://broker:29092` and `EXTERNAL://localhost:9092`) and opened port `9092` to the host.
### Long: 
1. Separating Listener `Internal` and `External`
    - `Internal://broker:29092` (Docker Network)
        - Communicate between Docker containers, listen address `broker:29092` which listens to its own hostname on the Docker network.
    - `External://localhost:9092` (Host Network)
        - Communicate between Kafka broker and clients running outside of Docker network such as the python script.
        - Advertising address `localhost:9092`, similar to web address, forwarding `localhost` (host machine) traffic to the container via port `["9092:9092"]` mapping.
2. Inter-Broker Requirement
    - The Kafka used in this project is `apache/kafka` instead of `confluentinc/cp-kafka` which has sophisticated entry point scripts which automatically derive and set multiple listener configuration (such as internal and external) based on a few basic variables (such as `KAFKA_ADVERTISED_LISTENERS`).
    -  The Kafka broker requires an explicit instruction on which defined listener (`INTERNAL` or `EXTERNAL`) it should use for inter-broker communication (like replication and metadata exchange).
        - Even with only one broker, it needs this to communicate with its own controller role.
    - By setting it to `INTERNAL`, the broker knows to use the listener that references **the internal Docker hostname (`broker`) for its internal cluster functions.
3. If using Kafka setups that has automatic derive and set listener configuration;
Single listener using `PLAINTEXT://0.0.0.0:9092`
```
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```
- The broker binds to all interfaces (`0.0.0.0`) inside the container and advertises the hosts's `localhost` address. 
- This works if the **client knows the address**.
- This does not separate the listener names, may cause issues when introduce other DOcker services that need to talk the the broker using the internal Docker hostname (`broker`).
- **Kafka principle** - The advertised listener must be reachable by the client.
    - If advertise `localhost:9092`, clients on host can connect.
    - If advertise `broker:9092`, clients inside the Docker network can connect.

## Error: `java.lang.IllegalArgumentException: No security protocol defined for listener INTERNAL`
- Source: Directly related to the above error; Missing security protocol mapping for the new listeners defined in the step above.
- Solution: Fixed `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP`: Explicitly mapped all listeners: `CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT`.

## Error: `java.lang.IllegalArgumentException: inter.broker.listener.name must be a listener name`
- Source: Directly related to the above error; The required setting for inter-br ker communication was missing.
- Added `KAFKA_INTER_BROKER_LISTENER_NAME`: Set to `INTERNAL` to tell the single broker to use the internal Docker service network for cluster communication.

---
# Spark
- Most errors are derived from specific or unstable Docker image tags, and subsequently incorrect dependency versions.
- `bitnami/spark:latest` is vendor-controlled, paid and restricted; Choosing `latest` tag requires premium subscription. Find alternatives for this toy project.
- Official `apache/spark` image is free, but required specific tags. 
    - As of writing this document (December 2025), The [latest stable](https://hub.docker.com/r/apache/spark/tags?page=4) or major release version of `apache/spark` is 3.5.7, and 4.1.0 is in preview stage.
- Ensure that the Spark image version matches the Kafka when creating a Spark Session.
    - `.config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7")`

## Error: `java.io.FileNotFoundException: /nonexistent/.ivy2/cache/...`
- Source: Spark's dependency manager (Ivy) failed because the default cache path for the non-root user (`/nonexistent/`) was not writable or did not exist.
- Solution: **Redirected Ivy Cache**: Added the configuration argument to the docker exec command:
`--conf "spark.driver.extraJavaOptions=-Divy.cache.dir=/tmp -Divy.home=/tmp"`
- Solution: Add the directory in the `docker-compose.yaml` 
    - volumes:
        - ./app:/app

## Run 
- Run Kafka's producer (in this project is app/transaction_producer.py) which simulates receiving data.
- Run the consumer in terminal, 
```
docker exec -it spark-master /opt/spark/bin/spark-submit \
    --conf "spark.driver.extraJavaOptions=-Divy.cache.dir=/tmp -Divy.home=/tmp" \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7 \
    /app/spark_stream_processor.py
```

```
docker exec -it spark-master /opt/spark/bin/spark-submit \
    --conf "spark.driver.extraJavaOptions=-Divy.cache.dir=/tmp -Divy.home=/tmp" \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7 \
    --archives /opt/venv.tar.gz#venv \
    --conf spark.executorEnv.PYSPARK_PYTHON="./venv/bin/python" \
    /app/spark_stream_processor.py
```