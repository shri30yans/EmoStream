from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, from_json, expr, floor, when, to_json, struct, collect_list
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

spark = SparkSession.builder \
    .appName("EmojiStreamProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3") \
    .config("spark.sql.shuffle.partitions", "4")\
    .getOrCreate()

schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("emoji_type", StringType(), True),
    StructField("timestamp", TimestampType(), True)
])

# Micro-batch config
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "emoji_topic") \
    .option("maxOffsetsPerTrigger", 100) \
    .load()

df = df.selectExpr("CAST(value AS STRING) as json_str")

# Parse JSON into structured data
emoji_df = df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

emoji_df_with_watermark = emoji_df.withWatermark("timestamp", "2 seconds")

aggregated_df = emoji_df_with_watermark \
    .groupBy(
        window(col("timestamp"), "2 seconds", "2 seconds"),
        col("emoji_type")
    ) \
    .count() \
    .withColumnRenamed("count", "emoji_count") 

scaled_df = aggregated_df \
    .withColumn("scaled_count", 
        when(col("emoji_count") <= 1000, col("emoji_count"))
        .otherwise(floor(col("emoji_count") / 1000)) 
    )

# After scaling
grouped_df = scaled_df.groupBy("window") \
    .agg(
        collect_list(
            struct("emoji_type", "scaled_count")
        ).alias("emojis")
    )

# JSON conversion
output_df = grouped_df.select(
    to_json(struct("window", "emojis")).alias("value")
)

query = output_df.writeStream \
    .outputMode("append") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "aggregated_emoji_topic") \
    .trigger(continuous='2 second') \
    .option("checkpointLocation", "checkpoint") \
    .start()

# Keep the application running
query.awaitTermination()
