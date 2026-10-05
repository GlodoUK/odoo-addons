"""SSH credentials for fsspec's SFTP filesystem, held in memory.

Two things an SFTP connection needs that cannot travel as JSON storage options:

* a **private key** - paramiko wants a ``PKey``, and its own loaders read from
  a file path. :func:`load_private_key` builds one from the key text instead,
  so key material never touches the disk.
* a **pinned host key** - fsspec's default policy (``auto_add``) trusts
  whatever key a server presents, so a man-in-the-middle could collect the
  credentials. :class:`PinnedHostKeyPolicy` accepts only the pinned key.

Both are passed to :func:`autopilot.tools.files.filesystem` as ``pkey`` /
``host_key_policy``. paramiko and cryptography are imported lazily, so the
rest of ``tools`` works without them.
"""

import base64
import hashlib
import io


def load_private_key(text, password=None):
    """A paramiko ``PKey`` from private key ``text`` (OpenSSH or PEM; RSA,
    ECDSA or Ed25519), decrypted with ``password`` if given. Raises
    ``ValueError`` when the key is unreadable, of an unsupported type, or the
    password is wrong."""
    import paramiko
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa

    data = (text or "").strip().encode() + b"\n"
    secret = password.encode() if password else None
    # Detect the type the way paramiko.PKey.from_path does, minus the file.
    try:
        try:
            loaded = serialization.load_ssh_private_key(data, password=secret)
        except ValueError:
            loaded = serialization.load_pem_private_key(data, password=secret)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Unreadable private key (wrong password, or not a key): {exc}"
        ) from exc
    if isinstance(loaded, rsa.RSAPrivateKey):
        key_class = paramiko.RSAKey
    elif isinstance(loaded, ed25519.Ed25519PrivateKey):
        key_class = paramiko.Ed25519Key
    elif isinstance(loaded, ec.EllipticCurvePrivateKey):
        key_class = paramiko.ECDSAKey
    else:
        raise ValueError(f"Unsupported private key type: {type(loaded).__name__}")
    # paramiko's loaders don't read every format cryptography does (PKCS#8),
    # so hand it the decoded key re-encoded as OpenSSH, in memory only.
    openssh = loaded.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption(),
    )
    return key_class.from_private_key(io.StringIO(openssh.decode()))


def fingerprint(key):
    """``key``'s OpenSSH-style SHA256 fingerprint, e.g. ``SHA256:nThbg6k...``."""
    digest = hashlib.sha256(key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode().rstrip("=")


def host_key_line(key):
    """``key`` as a ``<type> <base64>`` line, as stored when pinning it."""
    return f"{key.get_name()} {key.get_base64()}"


def parse_host_key_line(line):
    """``(type, base64)`` from a ``<type> <base64>`` line (a known_hosts
    entry's host field, if present, is ignored). Raises ``ValueError``."""
    parts = (line or "").split()
    if len(parts) == 3:
        parts = parts[1:]
    if len(parts) != 2:
        raise ValueError(
            "A host key reads '<type> <base64>', e.g. 'ssh-ed25519 AAAA...'."
        )
    try:
        base64.b64decode(parts[1], validate=True)
    except ValueError as exc:
        raise ValueError(f"The host key is not valid base64: {exc}") from exc
    return parts[0], parts[1]


def pinned_host_key_policy(line):
    """A paramiko ``MissingHostKeyPolicy`` accepting only the host key in
    ``line`` (see :func:`parse_host_key_line`). fsspec's SFTP client loads no
    known_hosts, so every connection consults it."""
    import paramiko

    expected = parse_host_key_line(line)

    class PinnedHostKeyPolicy(paramiko.MissingHostKeyPolicy):
        def __repr__(self):
            # Stable, so fsspec's instance cache (keyed on str() of the
            # arguments) reuses the connection; a new pin is a new one.
            return f"PinnedHostKeyPolicy({expected[0]} {expected[1]})"

        def missing_host_key(self, client, hostname, key):
            if (key.get_name(), key.get_base64()) != expected:
                raise paramiko.SSHException(
                    f"Host key for {hostname} does not match the pinned key "
                    f"(server presented {key.get_name()} {fingerprint(key)})."
                )

    return PinnedHostKeyPolicy()


def recording_host_key_policy():
    """A paramiko policy that accepts and remembers the presented key on
    ``policy.key`` - for pinning a server's key on an explicit, first test."""
    import paramiko

    class RecordingHostKeyPolicy(paramiko.MissingHostKeyPolicy):
        key = None

        def missing_host_key(self, client, hostname, key):
            self.key = key

    return RecordingHostKeyPolicy()
