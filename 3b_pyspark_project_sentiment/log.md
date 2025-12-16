
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

    