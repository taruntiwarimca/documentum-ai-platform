"""Real local operations standing in for OTDS 23.4.

No real OTDS instance is reachable in this environment. TLS validation
generates and inspects a real X.509 self-signed certificate (via the
`cryptography` package) rather than returning a canned result. Identity
source and authentication are checked against a real local JSON user store
with genuine PBKDF2 password hashing, not a hardcoded True.

configure_identity_source and register_user go beyond the six tools
documented for `otds` in documentum-ai-platform-poc/config/mcp-tools.yaml
(precheck, health, validate_tls, validate_identity_source,
test_authentication, audit) — they exist only so those six have real state
to check against; see the README for this scope note.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from agent_common.component_store import ComponentStore
from agent_common.password import hash_password, verify_password


class OtdsAgent:
    def __init__(self, data_dir: str | Path, environment: str) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._store = ComponentStore(self._data_dir, environment, "otds")
        env_dir = self._data_dir / environment
        self._cert_path = env_dir / "otds_server.crt"
        self._key_path = env_dir / "otds_server.key"

    def precheck(self) -> dict[str, Any]:
        (self._data_dir / self._environment).mkdir(parents=True, exist_ok=True)
        return {"ok": True}

    def validate_tls(self, common_name: str = "otds01") -> dict[str, Any]:
        if not self._cert_path.exists():
            self._generate_self_signed_cert(common_name)
        cert = x509.load_pem_x509_certificate(self._cert_path.read_bytes())
        now = datetime.now(timezone.utc)
        valid = cert.not_valid_before_utc <= now <= cert.not_valid_after_utc
        record = {
            "valid": valid,
            "subject": cert.subject.rfc4514_string(),
            "not_valid_after": cert.not_valid_after_utc.isoformat(),
            "cert_path": str(self._cert_path),
        }
        self._store.update(tls=record)
        return record

    def _generate_self_signed_cert(self, common_name: str) -> None:
        self._cert_path.parent.mkdir(parents=True, exist_ok=True)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        self._cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        self._key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )

    def configure_identity_source(self, name: str, source_type: str) -> dict[str, Any]:
        record = {"name": name, "type": source_type}
        self._store.set_resource("identity_sources", name, record)
        return record

    def validate_identity_source(self, name: str) -> dict[str, Any]:
        configured = self._store.get_resource("identity_sources", name)
        if configured is None:
            return {"ok": False, "reason": f"identity source {name!r} is not configured"}
        return {"ok": True, "identity_source": name, "type": configured.get("type")}

    def register_user(self, username: str, password: str) -> dict[str, Any]:
        record = hash_password(password)
        self._store.set_resource("users", username, record)
        return {"username": username, "registered": True}

    def test_authentication(self, username: str, password: str) -> dict[str, Any]:
        record = self._store.get_resource("users", username)
        if record is None:
            return {"authenticated": False, "reason": "unknown user"}
        ok = verify_password(password, record["salt"], record["password_hash"])
        return {"authenticated": ok, "reason": None if ok else "invalid credentials"}

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        tls = data.get("tls")
        return {
            "healthy": bool(tls and tls.get("valid")),
            "tls_valid": bool(tls and tls.get("valid")),
            "identity_sources": list(data.get("resources", {}).get("identity_sources", {})),
        }
