23 December 2025
- Progress:
    1. Introduced streamlit dashboard to display the data from PostgreSQL. It refreshes every 5 seconds.
    2. Dockerize the system -
        - `init-db/schema.sql` - Create table if not exist when container starts.
- Note that this version uses Spark running from local pc. Which Spark machine is from `pyspark`. Will reuse this in dockerized container.

19 December 2025
- Progress: 
    1. Further debug to find the issue with no-rows produced by spark
        1. Check if Spark is receiving from Kafka via rawstring
            - It received. 
        2. Check the timestamp to be similar by the seconds. It is.
        3. Check social_avg and _price avg.
            - BUG: Failed. Watermark has issue.
            - Solution: Check their immediate values before aggregation:
                - `social_avg.writeStream.queryName("debug_social_agg").outputMode("update").format("console").start()` and the price equivalent.
                - The above debug shows that the aggregations are working internally, and that it is a timing/watermark issue. A `final_df` issue.
    2. **Fixing the massive issue of timing, which caused `join` to fail.**
        1. Preparing `join_key` column for both social and price, which is done by rounding the time to the nearest 10.
            - Solution: This gives Spark a direct address to join. `p.join_key = s.join_key
            - Result: Spark now compares a Price from 13:10 to Social message from 13:10. This allows Has join which is faster than directly comparing based on range of 10s, which satisfies Spark's predicate requirement.  
        2. Breaking watermark issue from aggregating Price and Social separately, then trying to join the result. 
            - Issue: This creates a **Circular Dependency**, where Price Aggregate waits for Social Watermark, and vice versa.
            - Solution: If we join the raw data first, then aggregate in `final_df`.
        - With this logic change, Postgre properly receives from Spark.

18 December 2025
- Progress: 
    1. Debugging the network issue with price_producer.py (Fixed)
        1. Check connectivity
            -  using `nc -vz` shows that either it is region restricted, firewall or dns blocked. 
            - To check if wsl2 has connectivity, simply `ping google.com` or `nc -vz google.com 443`, which showed success. Failure in this is simply because internal firewall (`ufw`) or router is blocking all outgoing connections, at least for the wsl2. If success, the block is specific to Binance.
        2. DNS check
            - `nslookup stream.binance.com` - requires `sudo apt install bind9-dnsutils` 
            - Returned an address that is local to me instead of Binance-owned server, powered by Clourflare `13.x.x.x`. My ISP DNS Hijacked or Transparent Proxy'd me. 
        3. Solution: Change source. `Using coinbase.com` which is not blocked by my ISP.
    2. Debugging issues with Spark job cannot read from Kafka price producer.
        - Issues found: 
            - Mismatch topics for producers and processors.
            - Datetime mismatch. My local time zone is not GMT+0 which is the default settings.


16 December 2025
- Progress:
    1. download_model.py - downloads pre-trained model for AI stack.
    2. Spark-Kafka is reading from social producer ONLY 
        - BUG: price_producer has bug in that it does not connect to stream.binance.com

- Solutions of bugs today:
    1. `ERROR ArrowPythonRunner: This may have been caused by a prior exception: java.lang.UnsupportedOperationException: `
        - PyArrow Not found PySpark and Apache Arrow (which powers `pandas_udf`) rely on low-level memory access features, specificially `sun.misc.Unsafe` and `java.nio.DirectByteBuffer` to transfer data efficiently.
        - To use these features as per `spark-submit` command,
            - Unroll Java 21 to Java 11.
            - Add more conf to `spark-submit` command: 
            - `spark-submit   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.0   --conf "spark.driver.extraJavaOptions=-Dio.netty.tryReflectionSetAccessible=true --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED"   --conf "spark.executor.extraJavaOptions=-Dio.netty.tryReflectionSetAccessible=true --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED"   spark_job/processor.py`
                - `spark-submit` - launch Apache Spark app. Connects to cluster manager.
                - `--packages` - Use the specific Apache Spark-Kafka integration library. Also PostgreSQL JDBC Driver.
                - JVM Conf - Applies specific configurations to Java Virtual Machine (JVM)
                - `-Dio.netty.tryReflectionSetAccessible=true` - Workaround for compatibility issues with the Netty networking library (used extensively by Spark, Kafka, etc.) and the Java module system. It tries to force Netty to use reflection despite Java's restrictions.
                - `--add-opens=java.base/java.nio=ALL-UNNAMED` - Grants deeper access to the `java.nio` package within the `java.base module` for unnamed modules (like those loaded via the classpath). This is often required for libraries that manipulate Java buffers directly (like Netty).
                - `--add-opens=java.base/sun.nio.ch=ALL-UNNAMED`- Similar to the above, this specifically grants access to internal classes in `sun.nio.ch` (which deals with channel-based I/O). This is often necessary for high-performance I/O operations used by Spark and its dependencies.
 
15 December 2025
- Progress:
    1. kafka.vendor.six.moves No module found
        - kafka-python is incompatible with Python 3.12.
        - use kafk-apython-ng which is the maintained fork.

    