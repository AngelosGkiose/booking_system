import hashlib
import json


def generate_request_hash(event_seat_id):
    payload = {"event_seat_id": event_seat_id}
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
