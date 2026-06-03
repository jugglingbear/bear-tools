# pylint: disable=C0116

import ipaddress
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtensionOID, NameOID

from bear_tools import security_utils

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def self_signed() -> tuple[bytes, bytes]:
    """A reusable self-signed cert/key covering a representative mix of SAN types."""
    return security_utils.generate_self_signed_cert(
        sans=["192.168.1.50", "localhost", "example.test"],
        common_name="Unit Test Cert",
    )


@pytest.fixture(scope="module")
def cert_pem(self_signed: tuple[bytes, bytes]) -> str:
    return self_signed[0].decode()


def _make_non_ca_cert(sans: list[str] | None = None) -> str:
    """Build a self-signed cert WITHOUT the CA basic-constraint (for negative tests)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "non-ca")])
    now = datetime.now(tz=timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=10))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )
    if sans:
        builder = builder.add_extension(security_utils._build_subject_alt_names(sans), critical=False)
    cert = builder.sign(private_key=key, algorithm=hashes.SHA256())
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def _make_cert_no_san() -> str:
    """Build a self-signed CA cert that has no SubjectAlternativeName extension at all."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "no-san")])
    now = datetime.now(tz=timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=10))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode()


# ---------------------------------------------------------------------------
# generate_self_signed_cert
# ---------------------------------------------------------------------------


def test_generate_self_signed_cert_returns_pems(self_signed: tuple[bytes, bytes]) -> None:
    cert_pem, key_pem = self_signed
    assert cert_pem.startswith(b"-----BEGIN CERTIFICATE-----")
    assert b"PRIVATE KEY" in key_pem


def test_generate_self_signed_cert_is_ca(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    bc = cert.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS).value
    assert isinstance(bc, x509.BasicConstraints)
    assert bc.ca is True


def test_generate_self_signed_cert_common_name(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "Unit Test Cert"


def test_generate_self_signed_cert_default_common_name() -> None:
    cert_pem, _ = security_utils.generate_self_signed_cert(sans=["10.0.0.1"])
    cert = security_utils.load_cert(cert_pem.decode())
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "Self-Signed Certificate"


def test_generate_self_signed_cert_validity_window(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    lifetime = cert.not_valid_after_utc - cert.not_valid_before_utc
    assert abs(lifetime.days - 825) <= 1


def test_generate_self_signed_cert_separates_ip_and_dns(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
    assert isinstance(san, x509.SubjectAlternativeName)
    ips = [str(ip) for ip in san.get_values_for_type(x509.IPAddress)]
    dns = list(san.get_values_for_type(x509.DNSName))
    assert ips == ["192.168.1.50"]
    assert set(dns) == {"localhost", "example.test"}


def test_generate_self_signed_cert_is_self_validating(cert_pem: str) -> None:
    assert security_utils.is_self_signed_certificate_valid(cert_pem) is True


def test_generate_self_signed_cert_writes_files(tmp_path: Path) -> None:
    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    cert_pem, key_pem = security_utils.generate_self_signed_cert(
        sans=["127.0.0.1"], cert_path=cert_file, key_path=key_file
    )
    assert cert_file.read_bytes() == cert_pem
    assert key_file.read_bytes() == key_pem
    # Private key must be owner-read/write only (0600)
    assert (key_file.stat().st_mode & 0o777) == 0o600


def test_generate_self_signed_cert_honors_key_size() -> None:
    cert_pem, _ = security_utils.generate_self_signed_cert(sans=["127.0.0.1"], key_size=3072)
    cert = security_utils.load_cert(cert_pem.decode())
    public_key = cert.public_key()
    assert isinstance(public_key, rsa.RSAPublicKey)
    assert public_key.key_size == 3072


# ---------------------------------------------------------------------------
# _build_subject_alt_names
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["192.168.0.1", "10.0.0.255", "::1", "2001:db8::1"])
def test_build_subject_alt_names_ip(value: str) -> None:
    san = security_utils._build_subject_alt_names([value])
    ips = san.get_values_for_type(x509.IPAddress)
    assert ips == [ipaddress.ip_address(value)]
    assert san.get_values_for_type(x509.DNSName) == []


@pytest.mark.parametrize("value", ["example.com", "host.local", "*.wildcard.com"])
def test_build_subject_alt_names_dns(value: str) -> None:
    san = security_utils._build_subject_alt_names([value])
    assert san.get_values_for_type(x509.DNSName) == [value]
    assert san.get_values_for_type(x509.IPAddress) == []


# ---------------------------------------------------------------------------
# load_cert
# ---------------------------------------------------------------------------


def test_load_cert_from_string(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    assert isinstance(cert, x509.Certificate)


def test_load_cert_from_path(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    cert = security_utils.load_cert(path)
    assert isinstance(cert, x509.Certificate)


def test_load_cert_invalid_data_raises() -> None:
    with pytest.raises(RuntimeError):
        security_utils.load_cert("not a certificate")


def test_load_cert_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        security_utils.load_cert(tmp_path / "does_not_exist.pem")


# ---------------------------------------------------------------------------
# is_self_signed_certificate_valid
# ---------------------------------------------------------------------------


def test_is_self_signed_certificate_valid_true(cert_pem: str) -> None:
    assert security_utils.is_self_signed_certificate_valid(cert_pem) is True


def test_is_self_signed_certificate_valid_path(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    assert security_utils.is_self_signed_certificate_valid(path) is True


def test_is_self_signed_certificate_valid_expired(cert_pem: str) -> None:
    future = datetime.now(tz=timezone.utc) + timedelta(days=10_000)
    assert security_utils.is_self_signed_certificate_valid(cert_pem, current_time=future) is False


def test_is_self_signed_certificate_valid_not_yet_valid(cert_pem: str) -> None:
    past = datetime.now(tz=timezone.utc) - timedelta(days=10_000)
    assert security_utils.is_self_signed_certificate_valid(cert_pem, current_time=past) is False


def test_is_self_signed_certificate_valid_non_ca() -> None:
    assert security_utils.is_self_signed_certificate_valid(_make_non_ca_cert()) is False


def test_is_self_signed_certificate_valid_garbage() -> None:
    assert security_utils.is_self_signed_certificate_valid("garbage") is False


# ---------------------------------------------------------------------------
# get_certificate_sans
# ---------------------------------------------------------------------------


def test_get_certificate_sans(cert_pem: str) -> None:
    sans = security_utils.get_certificate_sans(cert_pem)
    assert set(sans) == {"192.168.1.50", "localhost", "example.test"}


def test_get_certificate_sans_empty_when_absent() -> None:
    assert security_utils.get_certificate_sans(_make_cert_no_san()) == []


# ---------------------------------------------------------------------------
# cert_matches_host
# ---------------------------------------------------------------------------


def test_cert_matches_host_ip_exact(cert_pem: str) -> None:
    assert security_utils.cert_matches_host(cert_pem, "192.168.1.50") is True


def test_cert_matches_host_ip_mismatch(cert_pem: str) -> None:
    assert security_utils.cert_matches_host(cert_pem, "192.168.1.51") is False


def test_cert_matches_host_dns_exact(cert_pem: str) -> None:
    assert security_utils.cert_matches_host(cert_pem, "example.test") is True


def test_cert_matches_host_dns_case_insensitive(cert_pem: str) -> None:
    assert security_utils.cert_matches_host(cert_pem, "EXAMPLE.TEST") is True


def test_cert_matches_host_dns_mismatch(cert_pem: str) -> None:
    assert security_utils.cert_matches_host(cert_pem, "other.test") is False


def test_cert_matches_host_ip_not_matched_as_dns(cert_pem: str) -> None:
    # "localhost" is a DNS SAN, but an IP target must never match a DNS entry
    assert security_utils.cert_matches_host(cert_pem, "127.0.0.1") is False


@pytest.mark.parametrize(
    "host,expected",
    [
        ("api.svc.local", True),       # single left label matches wildcard
        ("API.SVC.LOCAL", True),       # case-insensitive
        ("svc.local", False),          # base domain does not match *.svc.local
        ("a.b.svc.local", False),      # wildcard matches only one label
    ],
)
def test_cert_matches_host_wildcard(host: str, expected: bool) -> None:
    cert_pem, _ = security_utils.generate_self_signed_cert(sans=["*.svc.local"])
    assert security_utils.cert_matches_host(cert_pem.decode(), host) is expected


# ---------------------------------------------------------------------------
# cert_fingerprint
# ---------------------------------------------------------------------------


def test_cert_fingerprint_sha256(cert_pem: str) -> None:
    fp = security_utils.cert_fingerprint(cert_pem)
    parts = fp.split(":")
    assert len(parts) == 32  # SHA-256 = 32 bytes
    assert all(len(p) == 2 for p in parts)
    assert fp == fp.upper()


def test_cert_fingerprint_sha512(cert_pem: str) -> None:
    assert len(security_utils.cert_fingerprint(cert_pem, algorithm="sha512").split(":")) == 64


def test_cert_fingerprint_sha1(cert_pem: str) -> None:
    assert len(security_utils.cert_fingerprint(cert_pem, algorithm="sha1").split(":")) == 20


def test_cert_fingerprint_custom_separator(cert_pem: str) -> None:
    fp = security_utils.cert_fingerprint(cert_pem, separator="")
    assert ":" not in fp
    assert len(fp) == 64  # 32 bytes * 2 hex chars


def test_cert_fingerprint_is_stable(cert_pem: str) -> None:
    assert security_utils.cert_fingerprint(cert_pem) == security_utils.cert_fingerprint(cert_pem)


def test_cert_fingerprint_case_insensitive_algorithm(cert_pem: str) -> None:
    assert security_utils.cert_fingerprint(cert_pem, algorithm="SHA256") == security_utils.cert_fingerprint(cert_pem)


def test_cert_fingerprint_bad_algorithm(cert_pem: str) -> None:
    with pytest.raises(ValueError, match="Unsupported fingerprint algorithm"):
        security_utils.cert_fingerprint(cert_pem, algorithm="md5")


# ---------------------------------------------------------------------------
# Expiry helpers
# ---------------------------------------------------------------------------


def test_get_cert_expiry_is_utc_aware(cert_pem: str) -> None:
    expiry = security_utils.get_cert_expiry(cert_pem)
    assert expiry.tzinfo is not None
    assert expiry > datetime.now(tz=timezone.utc)


def test_days_until_expiry_positive(cert_pem: str) -> None:
    days = security_utils.days_until_expiry(cert_pem)
    assert 820 <= days <= 825


def test_days_until_expiry_negative_when_expired(cert_pem: str) -> None:
    future = datetime.now(tz=timezone.utc) + timedelta(days=10_000)
    assert security_utils.days_until_expiry(cert_pem, current_time=future) < 0


def test_is_cert_expired_false(cert_pem: str) -> None:
    assert security_utils.is_cert_expired(cert_pem) is False


def test_is_cert_expired_true(cert_pem: str) -> None:
    future = datetime.now(tz=timezone.utc) + timedelta(days=10_000)
    assert security_utils.is_cert_expired(cert_pem, current_time=future) is True


# ---------------------------------------------------------------------------
# mask_password
# ---------------------------------------------------------------------------


def test_mask_password_full_mask() -> None:
    assert security_utils.mask_password("secret") == "******"


def test_mask_password_partial() -> None:
    assert security_utils.mask_password("secret", unmasked_length=2) == "****et"


def test_mask_password_unmasked_longer_than_password() -> None:
    assert security_utils.mask_password("ab", unmasked_length=10) == "ab"


def test_mask_password_custom_symbol() -> None:
    assert security_utils.mask_password("secret", unmasked_length=2, symbol="#") == "####et"


def test_mask_password_empty() -> None:
    assert security_utils.mask_password("") == ""


# ---------------------------------------------------------------------------
# is_openssl_installed
# ---------------------------------------------------------------------------


def test_is_openssl_installed_true() -> None:
    with patch("subprocess.check_call", return_value=0) as mock_call:
        assert security_utils.is_openssl_installed() is True
        mock_call.assert_called_once()


def test_is_openssl_installed_false() -> None:
    with patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "hash openssl")):
        assert security_utils.is_openssl_installed() is False


# ---------------------------------------------------------------------------
# _is_linux / _linux_ca_anchor
# ---------------------------------------------------------------------------


def test_is_linux_true() -> None:
    with patch.object(security_utils.sys, "platform", "linux"):
        assert security_utils._is_linux() is True


def test_is_linux_false() -> None:
    with patch.object(security_utils.sys, "platform", "darwin"):
        assert security_utils._is_linux() is False


def test_linux_ca_anchor_debian() -> None:
    with (
        patch.object(security_utils.Path, "is_dir", lambda self: str(self).startswith("/usr/local")),
        patch.object(security_utils.shutil, "which", lambda cmd: "/usr/sbin/update-ca-certificates"),
    ):
        anchor = security_utils._linux_ca_anchor()
    assert anchor is not None
    anchor_dir, add_cmd, del_cmd = anchor
    assert anchor_dir == Path("/usr/local/share/ca-certificates")
    assert add_cmd == "sudo update-ca-certificates"
    assert del_cmd == "sudo update-ca-certificates --fresh"


def test_linux_ca_anchor_rhel() -> None:
    def _which(cmd: str) -> str | None:
        return "/usr/bin/update-ca-trust" if cmd == "update-ca-trust" else None

    with (
        patch.object(security_utils.Path, "is_dir", lambda self: str(self).startswith("/etc/pki")),
        patch.object(security_utils.shutil, "which", _which),
    ):
        anchor = security_utils._linux_ca_anchor()
    assert anchor is not None
    anchor_dir, add_cmd, del_cmd = anchor
    assert anchor_dir == Path("/etc/pki/ca-trust/source/anchors")
    assert add_cmd == "sudo update-ca-trust extract"
    assert del_cmd == "sudo update-ca-trust extract"


def test_linux_ca_anchor_none() -> None:
    with (
        patch.object(security_utils.Path, "is_dir", lambda self: False),
        patch.object(security_utils.shutil, "which", lambda cmd: None),
    ):
        assert security_utils._linux_ca_anchor() is None


# ---------------------------------------------------------------------------
# find_cert (platform-mocked)
# ---------------------------------------------------------------------------


def test_find_cert_macos_found() -> None:
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", return_value=0),
    ):
        assert security_utils.find_cert("My Cert") is True


def test_find_cert_macos_not_found() -> None:
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "security")),
    ):
        assert security_utils.find_cert("My Cert") is False


def test_find_cert_linux_match(tmp_path: Path, cert_pem: str) -> None:
    crt = tmp_path / "unit.crt"
    crt.write_text(cert_pem)
    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=(tmp_path, "add", "del")),
    ):
        assert security_utils.find_cert("Unit Test Cert") is True
        assert security_utils.find_cert("Nonexistent") is False


def test_find_cert_linux_no_truststore() -> None:
    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=None),
    ):
        assert security_utils.find_cert("x") is False


def test_find_cert_unsupported_platform() -> None:
    with patch.object(security_utils.sys, "platform", "win32"):
        assert security_utils.find_cert("x") is False


# ---------------------------------------------------------------------------
# trust_cert (platform-mocked)
# ---------------------------------------------------------------------------


def test_trust_cert_missing_file(tmp_path: Path) -> None:
    assert security_utils.trust_cert(str(tmp_path / "nope.pem")) is False


def test_trust_cert_macos(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", return_value=0) as mock_call,
    ):
        assert security_utils.trust_cert(str(path)) is True
        mock_call.assert_called_once()


def test_trust_cert_linux(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    calls: list[str] = []

    def _record(command: str, **_: object) -> int:
        calls.append(command)
        return 0

    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=(tmp_path, "sudo refresh", "del")),
        patch("subprocess.check_call", side_effect=_record),
    ):
        assert security_utils.trust_cert(str(path)) is True
    assert any("cp" in c for c in calls)
    assert "sudo refresh" in calls


def test_trust_cert_linux_no_truststore(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=None),
    ):
        assert security_utils.trust_cert(str(path)) is False


def test_trust_cert_unsupported_platform(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    with patch.object(security_utils.sys, "platform", "win32"):
        assert security_utils.trust_cert(str(path)) is False


# ---------------------------------------------------------------------------
# delete_cert (platform-mocked)
# ---------------------------------------------------------------------------


def test_delete_cert_macos_success() -> None:
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", return_value=0),
    ):
        assert security_utils.delete_cert("My Cert") is True


def test_delete_cert_macos_failure() -> None:
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "security")),
    ):
        assert security_utils.delete_cert("My Cert") is False


def test_delete_cert_macos_failure_ignored() -> None:
    with (
        patch.object(security_utils.sys, "platform", "darwin"),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "security")),
    ):
        # ignore_errors swallows the macOS failure and still reports success
        assert security_utils.delete_cert("My Cert", ignore_errors=True) is True


def test_delete_cert_linux_removes_match(tmp_path: Path, cert_pem: str) -> None:
    crt = tmp_path / "unit.crt"
    crt.write_text(cert_pem)
    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=(tmp_path, "add", "sudo refresh")),
        patch("subprocess.check_call", return_value=0) as mock_call,
    ):
        assert security_utils.delete_cert("Unit Test Cert") is True
        # One rm for the matching cert + one refresh command
        assert mock_call.call_count == 2


def test_delete_cert_linux_no_match(tmp_path: Path, cert_pem: str) -> None:
    crt = tmp_path / "unit.crt"
    crt.write_text(cert_pem)
    with (
        patch.object(security_utils.sys, "platform", "linux"),
        patch.object(security_utils, "_linux_ca_anchor", return_value=(tmp_path, "add", "del")),
    ):
        assert security_utils.delete_cert("Nonexistent") is False


def test_delete_cert_unsupported_platform() -> None:
    with patch.object(security_utils.sys, "platform", "win32"):
        assert security_utils.delete_cert("x") is False


# ---------------------------------------------------------------------------
# _cert_common_name / _safe_load_common_name
# ---------------------------------------------------------------------------


def test_cert_common_name(cert_pem: str) -> None:
    cert = security_utils.load_cert(cert_pem)
    assert security_utils._cert_common_name(cert) == "Unit Test Cert"


def test_cert_common_name_none() -> None:
    cert = MagicMock()
    cert.subject.get_attributes_for_oid.return_value = []
    assert security_utils._cert_common_name(cert) is None


def test_safe_load_common_name_ok(tmp_path: Path, cert_pem: str) -> None:
    path = tmp_path / "c.pem"
    path.write_text(cert_pem)
    assert security_utils._safe_load_common_name(path) == "Unit Test Cert"


def test_safe_load_common_name_bad_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pem"
    bad.write_text("not a cert")
    assert security_utils._safe_load_common_name(bad) is None
