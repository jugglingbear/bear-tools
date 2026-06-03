"""
Security utilities for working with X.509/TLS certificates and the system trust store.

Provides helpers to generate self-signed certificates, inspect them (SANs, fingerprint, expiry),
match a certificate against a hostname/IP (RFC 9525), validate self-signed CA certificates, and
add/find/remove certificates in the OS trust store on macOS and Linux. Also includes a small
password-masking helper.
"""

import ipaddress
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from cryptography.x509 import BasicConstraints
from cryptography.x509.oid import ExtensionOID, NameOID

from bear_tools import lumberjack

logger = lumberjack.Logger()

# macOS keeps its truststore in the "Keychain Access" app and provides the `security` CLI to manage it.
_MACOS_TRUSTSTORE = '/Users/$USER/Library/Keychains/login.keychain'


def _is_linux() -> bool:
    """Return True if running on Linux."""
    return sys.platform.startswith('linux')


def _linux_ca_anchor() -> tuple[Path, str, str] | None:
    """
    Resolve this Linux distro's system CA anchor directory and refresh commands.

    Supports the two dominant conventions:
      - Debian/Ubuntu: ``/usr/local/share/ca-certificates`` + ``update-ca-certificates``
      - RHEL/Fedora:   ``/etc/pki/ca-trust/source/anchors`` + ``update-ca-trust extract``

    :return: Tuple of (anchor_dir, add_refresh_cmd, delete_refresh_cmd), or None if no supported
      trust store is detected. Refresh commands are prefixed with ``sudo`` (system store needs root).
    """

    debian_dir = Path('/usr/local/share/ca-certificates')
    if debian_dir.is_dir() and shutil.which('update-ca-certificates'):
        return debian_dir, 'sudo update-ca-certificates', 'sudo update-ca-certificates --fresh'

    rhel_dir = Path('/etc/pki/ca-trust/source/anchors')
    if rhel_dir.is_dir() and shutil.which('update-ca-trust'):
        return rhel_dir, 'sudo update-ca-trust extract', 'sudo update-ca-trust extract'

    return None


def _cert_common_name(cert: x509.Certificate) -> str | None:
    """Return a certificate's Subject Common Name, or None if it has none."""
    attributes = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(attributes[0].value) if attributes else None


def _safe_load_common_name(path: Path) -> str | None:
    """Load a cert file and return its Common Name, swallowing read errors (returns None)."""
    try:
        return _cert_common_name(load_cert(path))
    except RuntimeError:
        return None


def _iter_anchor_certs(anchor_dir: Path) -> list[Path]:
    """List candidate certificate files (``*.crt`` and ``*.pem``) in a Linux anchor directory."""
    return sorted(anchor_dir.glob('*.crt')) + sorted(anchor_dir.glob('*.pem'))


def find_cert(cert_name: str) -> bool:
    """
    Search for a certificate in the truststore

    :param cert_name: Common Name of the certificate
    :return: True if the certificate was found in the truststore; False otherwise
    """

    # macOS
    if sys.platform == 'darwin':
        bash_command: str = f'security find-certificate -c "{cert_name}" "{_MACOS_TRUSTSTORE}"'
        try:
            subprocess.check_call(bash_command, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return False
        return True

    # Linux: scan the distro's CA anchor directory for a cert whose Common Name matches
    if _is_linux():
        anchor = _linux_ca_anchor()
        if anchor is None:
            logger.error('No supported Linux trust store found (need update-ca-certificates or update-ca-trust)')
            return False
        anchor_dir, _, _ = anchor
        return any(_safe_load_common_name(crt) == cert_name for crt in _iter_anchor_certs(anchor_dir))

    logger.error(f'Platform not supported: "{sys.platform}"')
    return False


def delete_cert(cert_name: str, ignore_errors: bool = False) -> bool:
    """
    Delete and un-trust a cert from the truststore

    :param cert_name: Name of cert to un-trust and delete from truststore
    :param ignore_errors: If True, do not log or otherwise indicate errors that occur when trying to delete cert
    :return: True if the operation was successful; False otherwise
    """

    # macOS
    if sys.platform == 'darwin':
        bash_command: str = f'security delete-certificate -t -c "{cert_name}" "{_MACOS_TRUSTSTORE}"'
        try:
            subprocess.check_call(bash_command, shell=True)
        except subprocess.CalledProcessError as error:
            if not ignore_errors:
                logger.error(f'Failed to send command to OS: "{bash_command}". Error: "{error}"')
                return False

    # Linux: remove any anchor cert(s) whose Common Name matches, then refresh the system store
    elif _is_linux():
        anchor = _linux_ca_anchor()
        if anchor is None:
            if not ignore_errors:
                logger.error('No supported Linux trust store found (need update-ca-certificates or update-ca-trust)')
            return False
        anchor_dir, _, refresh_delete = anchor
        matches = [crt for crt in _iter_anchor_certs(anchor_dir) if _safe_load_common_name(crt) == cert_name]
        if not matches:
            if not ignore_errors:
                logger.error(f'Certificate not found in trust store: "{cert_name}"')
            return False
        for crt in matches:
            try:
                subprocess.check_call(f"sudo rm -f '{crt}'", shell=True)
            except subprocess.CalledProcessError as error:
                if not ignore_errors:
                    logger.error(f'Failed to remove cert "{crt}". Error: "{error}"')
                return False
        try:
            subprocess.check_call(refresh_delete, shell=True)
        except subprocess.CalledProcessError as error:
            if not ignore_errors:
                logger.error(f'Failed to refresh trust store via "{refresh_delete}". Error: "{error}"')
            return False

    else:
        logger.error(f'Platform not supported: "{sys.platform}"')
        return False

    logger.info(f'Certificate untrusted and removed from truststore: "{cert_name}"')
    return True


def load_cert(source: Path | str) -> x509.Certificate:
    """
    Load an SSL/TLS certificate from a file or raw PEM data.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :return: The parsed certificate
    :raises RuntimeError: If the certificate cannot be read or parsed
    """

    try:
        cert_data: bytes
        if isinstance(source, Path):
            with open(source, "rb") as f:
                cert_data = f.read()
        elif isinstance(source, str):
            cert_data = source.encode()
        cert: x509.Certificate = x509.load_pem_x509_certificate(cert_data, backend=default_backend())
        return cert
    except (InvalidSignature, ValueError, FileNotFoundError, x509.ExtensionNotFound) as error:
        raise RuntimeError('There was a problem with reading the cert. Error: "{error}"') from error


def is_openssl_installed() -> bool:
    """
    Determine if the system has openssl installed

    :return: True if the ``openssl`` executable is available on PATH; False otherwise
    """

    try:
        subprocess.check_call('hash openssl', shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


def mask_password(password: str, unmasked_length: int = 0, symbol: str = '*') -> str:
    """
    Mask a password by substituting all but the last unmasked_length characters with symbol

    :param password: A password in plain text to mask
    :param unmasked_length: How many characters at the end of the password to not mask
    :param symbol: The symbol to use for substitution
    :return: The masked password
    """

    if len(password) < unmasked_length:
        unmasked_length = len(password)

    masked_length = len(password) - unmasked_length
    return symbol * masked_length + password[masked_length:]


def trust_cert(cert_path: str) -> bool:
    """
    Add a certificate to the user's truststore

    :param cert_path: Path to a certificate that user wants to trust
    :return: True if operation was successful; False otherwise
    """

    if not os.path.exists(cert_path):
        logger.error(f'File not found: {cert_path}')
        return False

    # macOS
    if sys.platform == 'darwin':
        bash_command: str = f'security import {cert_path} -k {_MACOS_TRUSTSTORE}'
        try:
            subprocess.check_call(bash_command, shell=True)
        except subprocess.CalledProcessError as error:
            logger.error(f'Failed to send command to OS: "{bash_command}". Error: "{error}"')
            return False

    # Linux: copy the cert into the distro's anchor directory and rebuild the system bundle
    elif _is_linux():
        anchor = _linux_ca_anchor()
        if anchor is None:
            logger.error('No supported Linux trust store found (need update-ca-certificates or update-ca-trust)')
            return False
        anchor_dir, refresh_add, _ = anchor
        # update-ca-certificates only ingests files with a .crt extension
        destination: Path = anchor_dir / f'{Path(cert_path).stem}.crt'
        for command in (f"sudo cp '{cert_path}' '{destination}'", refresh_add):
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError as error:
                logger.error(f'Failed to send command to OS: "{command}". Error: "{error}"')
                return False

    else:
        logger.error(f'Platform not supported: "{sys.platform}"')
        return False

    logger.info(f'Certificate added to truststore: {cert_path}')
    return True


def is_self_signed_certificate_valid(cert_src: Path | str, current_time: datetime | None = None) -> bool:
    """
    Verifies that a certificate is a valid, self-signed CA certificate.

    Equivalent to: openssl verify -CAfile cert_path cert_path

    :param cert_src: The source of a self-signed certificate. Can be a Path or raw data
    :param current_time: If set, use this as the current time rather than the system's actual current time
    :return: True if the certificate is valid; False otherwise
    """

    try:
        cert_data: bytes
        if isinstance(cert_src, Path):
            with open(cert_src, "rb") as f:
                cert_data = f.read()
        elif isinstance(cert_src, str):
            cert_data = cert_src.encode()

        cert: x509.Certificate = x509.load_pem_x509_certificate(cert_data, backend=default_backend())
        public_key: PublicKeyTypes = cert.public_key()

        hash_algorithm = cert.signature_hash_algorithm
        if hash_algorithm is None:
            return False

        # 1. Verify signature
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                signature=cert.signature,
                data=cert.tbs_certificate_bytes,
                padding=padding.PKCS1v15(),
                algorithm=hash_algorithm
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                signature=cert.signature,
                data=cert.tbs_certificate_bytes,
                signature_algorithm=ec.ECDSA(hash_algorithm)
            )
        elif isinstance(public_key, dsa.DSAPublicKey):
            public_key.verify(
                signature=cert.signature,
                data=cert.tbs_certificate_bytes,
                algorithm=hash_algorithm
            )
        else:
            return False  # Unsupported key type

        # 2. Validity window (UTC-aware)
        before: datetime = cert.not_valid_before_utc
        now: datetime = current_time or datetime.now(tz=timezone.utc)
        after: datetime = cert.not_valid_after_utc

        logger.debug(f'before:        {before} (type: {type(before)})')
        logger.debug(f'now:           {now} ({type(now)})')
        logger.debug(f'after:         {after} ({type(after)})')
        logger.debug(f'before <= now: {before <= now}')
        logger.debug(f'now <= after:  {now <= after}')

        if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
            return False

        # 3. Basic Constraints: must be a CA
        try:
            bc = cert.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS).value
            assert isinstance(bc, BasicConstraints), 'bc is not a BasicConstraints'
            if not bc.ca:
                return False
        except x509.ExtensionNotFound:
            return False

        return True

    except (InvalidSignature, ValueError, FileNotFoundError, x509.ExtensionNotFound):
        return False


def _build_subject_alt_names(sans: list[str]) -> x509.SubjectAlternativeName:
    """
    Convert a list of host identifiers into a SubjectAlternativeName extension.

    Each entry is added as an IP address if it parses as one, otherwise as a DNS name. Embedding the
    IP/hostname a client will connect to is required because modern TLS clients match against the SAN
    and ignore the legacy Common Name field.

    :param sans: List of IP addresses and/or DNS names to embed in the certificate
    :return: A SubjectAlternativeName extension value
    """

    entries: list[x509.GeneralName] = []
    for san in sans:
        try:
            entries.append(x509.IPAddress(ipaddress.ip_address(san)))
        except ValueError:
            entries.append(x509.DNSName(san))
    return x509.SubjectAlternativeName(entries)


def generate_self_signed_cert(
    sans: list[str],
    common_name: str = 'Self-Signed Certificate',
    valid_days: int = 825,
    key_size: int = 2048,
    cert_path: Path | None = None,
    key_path: Path | None = None,
) -> tuple[bytes, bytes]:
    """
    Generate a self-signed certificate and matching private key.

    The certificate is marked as a CA (BasicConstraints CA=True) so it can act as its own trust
    anchor: it may be used directly as a server cert/key and the same PEM distributed as the CA to
    trust. It also satisfies ``is_self_signed_certificate_valid``.

    :param sans: Host identifiers (IP addresses and/or DNS names) to embed in the SubjectAlternativeName.
      Must include the address/hostname the client will connect to.
    :param common_name: Subject/Issuer Common Name for the certificate
    :param valid_days: Number of days the certificate remains valid (default 825 = ~27 months, the
      CA/Browser-Forum max for leaf certs; kept conservative for tooling compatibility)
    :param key_size: RSA key size in bits
    :param cert_path: If set, write the PEM-encoded certificate to this path
    :param key_path: If set, write the PEM-encoded private key to this path (chmod 0600)
    :return: Tuple of (certificate_pem_bytes, private_key_pem_bytes)
    """

    key: rsa.RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now: datetime = datetime.now(tz=timezone.utc)

    cert: x509.Certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=valid_days))
        .add_extension(_build_subject_alt_names(sans), critical=False)
        .add_extension(BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256(), backend=default_backend())
    )

    cert_pem: bytes = cert.public_bytes(serialization.Encoding.PEM)
    key_pem: bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    if cert_path is not None:
        cert_path.write_bytes(cert_pem)
        logger.info(f'Wrote certificate to: {cert_path}')
    if key_path is not None:
        key_path.write_bytes(key_pem)
        os.chmod(key_path, 0o600)
        logger.info(f'Wrote private key to: {key_path}')

    return cert_pem, key_pem


def get_certificate_sans(source: Path | str) -> list[str]:
    """
    Extract the SubjectAlternativeName entries (IP addresses and DNS names) from a certificate.

    Useful to assert that a certificate actually covers the address/hostname a client will connect to.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :return: List of SAN values as strings (IP addresses and DNS names); empty if the SAN is absent
    """

    cert: x509.Certificate = load_cert(source)
    try:
        san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
        assert isinstance(san, x509.SubjectAlternativeName), 'extension value is not a SubjectAlternativeName'
    except x509.ExtensionNotFound:
        return []

    names: list[str] = [str(ip) for ip in san.get_values_for_type(x509.IPAddress)]
    names.extend(san.get_values_for_type(x509.DNSName))
    return names


def cert_matches_host(source: Path | str, host: str) -> bool:
    """
    Check whether a certificate is valid for the given hostname or IP address.

    Implements the SubjectAlternativeName matching that modern TLS clients perform (RFC 9525): IP
    targets are matched against ``iPAddress`` SANs, and hostnames against ``dNSName`` SANs
    (case-insensitive, with single-label ``*.`` wildcard support). The legacy Common Name field is
    intentionally ignored, mirroring real client behavior.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :param host: The hostname or IP address the client would connect to
    :return: True if the certificate covers ``host``; False otherwise
    """

    sans: list[str] = get_certificate_sans(source)

    # IP target: compare normalized IP objects against IP-type SANs only
    try:
        target_ip = ipaddress.ip_address(host)
    except ValueError:
        target_ip = None

    if target_ip is not None:
        for san in sans:
            try:
                if ipaddress.ip_address(san) == target_ip:
                    return True
            except ValueError:
                continue
        return False

    # Hostname target: case-insensitive exact or single-label wildcard match
    host_normalized: str = host.lower().rstrip('.')
    for san in sans:
        san_normalized: str = san.lower().rstrip('.')
        if san_normalized == host_normalized:
            return True
        if san_normalized.startswith('*.'):
            suffix: str = san_normalized[1:]  # e.g. ".example.com"
            if host_normalized.endswith(suffix):
                left_label: str = host_normalized[: -len(suffix)]
                # Wildcard matches exactly one left-most label (no embedded dot, non-empty)
                if left_label and '.' not in left_label:
                    return True
    return False


def cert_fingerprint(source: Path | str, algorithm: str = 'sha256', separator: str = ':') -> str:
    """
    Compute a certificate's fingerprint (a hash of its DER bytes), as used for cert pinning.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :param algorithm: Hash algorithm: 'sha256' (default), 'sha512', or 'sha1' (legacy compatibility only)
    :param separator: String placed between hex byte pairs (default ':' -> e.g. 'AB:CD:...')
    :return: The uppercase hex fingerprint string
    :raises ValueError: If ``algorithm`` is not one of the supported choices
    """

    algorithms: dict[str, hashes.HashAlgorithm] = {
        'sha256': hashes.SHA256(),
        'sha512': hashes.SHA512(),
        'sha1': hashes.SHA1(),  # noqa: S303  # identity/pinning use only, not a security signature
    }
    chosen = algorithms.get(algorithm.lower())
    if chosen is None:
        raise ValueError(f'Unsupported fingerprint algorithm: "{algorithm}". Choose from {sorted(algorithms)}')

    digest: bytes = load_cert(source).fingerprint(chosen)
    return separator.join(f'{byte:02X}' for byte in digest)


def get_cert_expiry(source: Path | str) -> datetime:
    """
    Get a certificate's expiry (``notAfter``) as a timezone-aware UTC datetime.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :return: The UTC datetime after which the certificate is no longer valid
    """

    return load_cert(source).not_valid_after_utc


def days_until_expiry(source: Path | str, current_time: datetime | None = None) -> int:
    """
    Get the number of whole days until a certificate expires (negative if already expired).

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :param current_time: If set, measure from this time rather than the system's actual current time
    :return: Whole days until expiry; negative if the certificate has already expired
    """

    now: datetime = current_time or datetime.now(tz=timezone.utc)
    return (get_cert_expiry(source) - now).days


def is_cert_expired(source: Path | str, current_time: datetime | None = None) -> bool:
    """
    Determine whether a certificate is past its expiry (``notAfter``) date.

    :param source: Either a Path pointing to the cert file or a str containing the raw certificate data
    :param current_time: If set, compare against this time rather than the system's actual current time
    :return: True if the certificate has expired; False otherwise
    """

    now: datetime = current_time or datetime.now(tz=timezone.utc)
    return now > get_cert_expiry(source)
