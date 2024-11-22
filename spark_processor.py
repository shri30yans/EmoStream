from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, count, first, from_json, when, lit, to_json, struct, collect_list
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

print("Starting Spark application")

spark = SparkSession.builder \
    .appName("RealTimeEmojiAggregator") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3") \
    .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
    .getOrCreate()


schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("emoji_type", StringType(), True),
    StructField("timestamp", StringType(), True)
])

emoji_stream = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", 'localhost:9092') \
    .option("subscribe", 'client_emoji') \
    .load()

formated_emoji_stream = emoji_stream.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

formated_emoji_stream = formated_emoji_stream.withColumn("event_time", col("timestamp").cast(TimestampType()))

aggregated_emoji_stream = formated_emoji_stream.groupBy(
    window(col("event_time"), "2 seconds"), 
    col("emoji_type")
).agg(
    count("user_id").alias("raw_count")
).withColumn(
    "count",
    when(col("raw_count") > 1000, (col("raw_count") / 1000).cast("integer"))
    .when(col("raw_count").between(1, 1000), 1)
    .otherwise(col("raw_count"))
).groupBy(
    "window"
).agg(
    to_json(
        collect_list(
            struct(
                col("emoji_type"),
                col("count")
            )
        )
    ).alias("emojis")
).select(
    col("window.start").alias("window_start"),
    col("window.end").alias("window_end"),
    col("emojis")
)

final_output = aggregated_emoji_stream.selectExpr("to_json(struct(*)) as value")

kafka_query = final_output \
    .writeStream \
    .outputMode("update") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", 'localhost:9092') \
    .option("topic", 'emoji_topic_aggregated') \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .trigger(processingTime="2 seconds") \
    .start()

kafka_query.awaitTermination()

