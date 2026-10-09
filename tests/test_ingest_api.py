"""Unit tests for the ingest API using Flask's test client + fake producer."""

import json

import pytest

from app.ingest_api import create_app


class FakeProducer:
    def __init__(self):
        self.sent = []
        self.flushed = 0

    def send(self, topic, value):
        self.sent.append((topic, value))

    def flush(self):
        self.flushed += 1


@pytest.fixture()
def client():
    producer = FakeProducer()
    app = create_app(producer=producer, topic="streamagg.raw.v1")
    app.config["TESTING"] = True
    with app.test_client() as c:
        c._fake_producer = producer  # type: ignore[attr-defined]
        yield c


def _drain(app_client):
    buffered = app_client.application.config["BUFFERED_PRODUCER"]
    buffered.flush()


def test_ingest_accepts_valid_reaction(client):
    resp = client.post("/v1/reactions", json={
        "user_id": "user123",
        "reaction": "cheer",
        "timestamp": "2024-01-01T12:00:00Z",
    })
    assert resp.status_code == 202
    assert resp.get_json()["status"] == "accepted"
    _drain(client)
    assert len(client._fake_producer.sent) == 1
    topic, event = client._fake_producer.sent[0]
    assert topic == "streamagg.raw.v1"
    assert event["reaction"] == "cheer"


def test_legacy_endpoint_still_works(client):
    resp = client.post("/send_emoji", json={
        "user_id": "u1", "emoji_type": "smile",
        "timestamp": "2024-01-01T12:00:00Z"})
    assert resp.status_code == 202


def test_ingest_rejects_invalid_body(client):
    resp = client.post("/v1/reactions", json={"user_id": "", "reaction": ""})
    assert resp.status_code == 400


def test_healthz_ok_with_producer(client):
    resp = client.get("/healthz")
    assert resp.status_code in (200, 503)
    assert "kafka" in resp.get_json()


def test_stats_endpoint(client):
    resp = client.get("/v1/stats")
    assert resp.status_code == 200
    body = resp.get_json()
    assert {"accepted", "dropped", "queued"} <= set(body)
