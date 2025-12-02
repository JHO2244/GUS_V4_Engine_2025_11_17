import hashlib
from datetime import datetime

class PASSeal:
    def __init__(self, version: str, scope: str, issuer: str, timestamp: str, payload_hash: str):
        self.version = version
        self.scope = scope
        self.issuer = issuer
        self.timestamp = timestamp
        self.payload_hash = payload_hash

def compute_hash(payload: dict) -> str:
    raw = str(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def generate_seal_proto(scope: str, issuer: str = "JHO") -> PASSeal:
    timestamp = datetime.utcnow().isoformat()
    payload = {
        "scope": scope,
        "issuer": issuer,
        "timestamp": timestamp,
    }
    payload_hash = compute_hash(payload)
    return PASSeal(
        version="PAS.v1.0-proto",
        scope=scope,
        issuer=issuer,
        timestamp=timestamp,
        payload_hash=payload_hash
    )
