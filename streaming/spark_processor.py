"""Spark Structured Streaming job: RAW_EVENTS_TOPIC -> AGG_EVENTS_TOPIC.

Reads generic reaction events, windows them into WINDOW_SECONDS micro-batches,
counts per reaction type, downsamples (see streaming/aggregation.py), and
writes one JSON document per window to the aggregate topic.

Run:
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3 \\
        streaming/spark_processor.py [--window-seconds 2 --per-unit 1000 ...]
"""

from __future__ import annotations

import argparse
import logging

import config

log = logging.getLogger("streamagg.spark")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StreamAgg Kafka->Spark aggregator")
    parser.add_argument("--bootstrap-servers", default=config.KAFKA_BOOTSTRAP_SERVERS)
    parser.add_argument("--input-topic", default=config.RAW_EVENTS_TOPIC)
    parser.add_argument("--output-topic", default=config.AGG_EVENTS_TOPIC)
    parser.add_argument("--window-seconds", type=int, default=config.WINDOW_SECONDS)
    parser.add_argument("--per-unit", type=int, default=config.DOWNSAMPLE_PER_UNIT)
    parser.add_argument("--checkpoint", default=config.SPARK_CHECKPOINT_DIR)
    return parser.parse_args(argv)


def run() -> None:
    args = parse_args()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import (
        col, count, collect_list, from_json, struct, to_json, when,
        window as spark_window,
    )
    from pyspark.sql.types import StringType, StructField, StructType, TimestampType

    logging.basicConfig(level=logging.INFO)
    log.info(
        "starting: %s[%s] -> window %ds -> %s (checkpoint %s)",
        args.bootstrap_servers, args.input_topic,
        args.window_seconds, args.output_topic, args.checkpoint,
    )

    spark = (
        SparkSession.builder.appName(config.SPARK_APP_NAME)
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
        )
        .config(
            "spark.sql.streaming.statefulOperator.checkCorrectness.enabled",
            "false",
        )
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Accept both the new "reaction" field and the legacy "emoji_type".
    schema = StructType([
        StructField("user_id", StringType(), True),
        StructField("reaction", StringType(), True),
        StructField("emoji_type", StringType(), True),
        StructField("timestamp", StringType(), True),
    ])

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", args.bootstrap_servers)
        .option("subscribe", args.input_topic)
        .load()
    )
    events = raw.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Coalesce new + legacy field names, drop malformed rows early.
    events = events.withColumn(
        "reaction_norm",
        when(col("reaction").isNotNull(), col("reaction"))
        .otherwise(col("emoji_type")),
    ).filter(col("reaction_norm").isNotNull())

    events = events.withColumn(
        "event_time", col("timestamp").cast(TimestampType())
    ).filter(col("event_time").isNotNull())

    window_spec = spark_window(col("event_time"), f"{args.window_seconds} seconds")

    per_window = events.groupBy(window_spec, col("reaction_norm").alias("reaction")).agg(
        count("user_id").alias("raw_count")
    )
    per_window = per_window.withColumn(
        "count",
        when(col("raw_count") > args.per_unit,
             (col("raw_count") / args.per_unit).cast("int"))
        .when(col("raw_count") >= 1, 1)
        .otherwise(0),
    )
    payload = (
        per_window.groupBy("window")
        .agg(
            to_json(
                collect_list(struct(col("reaction"), col("count"), col("raw_count")))
            ).alias("reactions")
        )
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("reactions"),
        )
    )

    out = payload.selectExpr("to_json(struct(*)) as value")
    query = (
        out.writeStream.outputMode("update").format("kafka")
        .option("kafka.bootstrap.servers", args.bootstrap_servers)
        .option("topic", args.output_topic)
        .option("checkpointLocation", args.checkpoint)
        .trigger(processingTime=f"{args.window_seconds} seconds")
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    run()
