.PHONY: up down api spark main cluster bridge load demo test lint

up:
	docker compose up -d

down:
	docker compose down

api:
	python -m app.ingest_api

spark:
	spark-submit streaming/spark_processor.py

main:
	python -m fanout.main_publisher

cluster:
	python -m fanout.cluster_publisher --cluster-id $${CLUSTER:-default}

bridge:
	python -m fanout.websocket_bridge

load:
	python tools/load_generator.py --rps $${RPS:-100} --duration $${DURATION:-30}

demo:
	streamlit run client/demo_frontend.py

test:
	python -m pytest tests/ -q

lint:
	python -m compileall -q app streaming fanout tools client config.py
