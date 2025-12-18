

Commands:
- Start Spark Job - 
```
spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.0 \
--conf "spark.driver.extraJavaOptions=-Dio.netty.tryReflectionSetAccessible=true --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED" \
--conf "spark.executor.extraJavaOptions=-Dio.netty.tryReflectionSetAccessible=true --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED" \
spark_job/processor.py
```

- Connect to PostgreSQL Database - `docker exec -it 3b_pyspark_project_sentiment-postgres-1 psql -U user -d hype_db`
- Create results table -
```
CREATE TABLE realtime_hype (
    time TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY,
    avg_price DOUBLE PRECISION,
    hype_score DOUBLE PRECISION
);
``` 
- Other PostgreSQL (PSQL) Commands - 
    - Lists all tables -`\dt`
    - Check data from table `realtime_hype`- `SELECT * FROM realtime_hype;`
    - Limit checks - `SELECT * FROM realtime_hype ORDER BY time DESC LIMIT 5;` 
    - Clears data; Removes all rows from a set of table - `TRUNCATE TABLE realtime_hype;` 
    - Quit PSQL - `\q`


--- 

Debug Commands:
- Docker logs - `docker-compose logs -f`
- Docker Kafka send 5 messages by topics - 
```
docker exec -it <container_name> /usr/bin/kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic crypto_price \
    --from-beginning \
    --max-messages 5
```
```
docker exec -it <container_name> /usr/bin/kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic crypto_social \
    --from-beginning \
    --max-messages 5
```

docker exec -it 3b_pyspark_project_sentiment-kafka-1  /usr/bin/kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic crypto_social \
    --from-beginning \
    --max-messages 5 



- Network debugs - 
    - Install Netcat if not already - `sudo apt install netcat-openbsd`
    - Test Binance Port 9443 - `nc -vz stream.binance.com 9443`
        - Test 443 if 9443 cannot.
    - Test Internet Connectivity - `nc -vz google.com 443`
    - Test IP Block - `nslookup stream.binance.com`
    - Check Local Firewall - `sudo ufw status`
    - 
