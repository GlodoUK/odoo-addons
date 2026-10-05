from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

from odoo.tests import BaseCase, tagged

from odoo.addons.autopilot import tools


def _key_text(key, fmt=serialization.PrivateFormat.OpenSSH, password=None):
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )
    return key.private_bytes(serialization.Encoding.PEM, fmt, encryption).decode()


@tagged("post_install", "-at_install")
class TestToolsSsh(BaseCase):
    def test_load_private_key_formats(self):
        for key, fmt in (
            (ed25519.Ed25519PrivateKey.generate(), serialization.PrivateFormat.OpenSSH),
            (rsa.generate_private_key(65537, 2048), serialization.PrivateFormat.PKCS8),
        ):
            loaded = tools.ssh.load_private_key(_key_text(key, fmt))
            public = key.public_key().public_bytes(
                serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH
            )
            self.assertEqual(loaded.get_base64(), public.decode().split()[1])

    def test_load_private_key_password(self):
        text = _key_text(ed25519.Ed25519PrivateKey.generate(), password="secret")
        self.assertTrue(tools.ssh.load_private_key(text, "secret"))
        for wrong in ("nope", None):
            with self.assertRaises(ValueError):
                tools.ssh.load_private_key(text, wrong)
        with self.assertRaises(ValueError):
            tools.ssh.load_private_key("not a key")

    def test_pinned_host_key_policy(self):
        import paramiko

        server = tools.ssh.load_private_key(
            _key_text(ed25519.Ed25519PrivateKey.generate())
        )
        other = tools.ssh.load_private_key(
            _key_text(ed25519.Ed25519PrivateKey.generate())
        )
        policy = tools.ssh.pinned_host_key_policy(tools.ssh.host_key_line(server))
        policy.missing_host_key(None, "sftp.example", server)
        with self.assertRaises(paramiko.SSHException):
            policy.missing_host_key(None, "sftp.example", other)

    def test_parse_options(self):
        self.assertEqual(tools.files.parse_options(""), {})
        self.assertEqual(tools.files.parse_options('{"port": 22}'), {"port": 22})
        for bad in ("not json", "[1, 2]"):
            with self.assertRaises(ValueError):
                tools.files.parse_options(bad)
