import base64
import json
import os
import tempfile
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.autopilot import tools


def _key_text(password=None):
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )
    return (
        ed25519.Ed25519PrivateKey.generate()
        .private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.OpenSSH, encryption
        )
        .decode()
    )


def _upload(text):
    return base64.b64encode(text.encode())


@tagged("post_install", "-at_install")
class TestConnection(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Connection = cls.env["autopilot_sale.connection"]
        cls.connection = cls.Connection.create({"name": "SFTP", "protocol": "sftp"})

    def _captured_options(self, connection):
        captured = {}

        def fake_filesystem(protocol, options=None, **extra):
            captured.update(options)

        with patch.object(tools.files, "filesystem", fake_filesystem):
            connection._fs()
        return captured

    def test_private_key_wrong_password_rejected(self):
        with self.assertRaises(ValidationError):
            self.connection.write(
                {
                    "private_key_input": _upload(_key_text("pw")),
                    "private_key_password_input": "wrong",
                }
            )

    def test_service_account_must_be_one(self):
        with self.assertRaises(ValidationError):
            self.connection.service_account_input = _upload(
                '{"type": "authorized_user"}'
            )

    def test_storage_options_validated(self):
        with self.assertRaises(ValidationError):
            self.connection.storage_options = "not json"

    def test_sftp_options(self):
        key = tools.ssh.load_private_key(_key_text())
        self.connection.write(
            {
                "host": "sftp.example",
                "port": 2222,
                "username": "edi",
                "password_input": "secret",
                "private_key_input": _upload(_key_text()),
                "host_key": tools.ssh.host_key_line(key),
                # The field wins over the same advanced option.
                "storage_options": '{"port": 1, "look_for_keys": false}',
            }
        )
        options = self._captured_options(self.connection)
        self.assertEqual(options["host"], "sftp.example")
        self.assertEqual(options["port"], 2222)
        self.assertEqual(options["password"], "secret")
        self.assertIs(options["look_for_keys"], False)
        self.assertIn("pkey", options)
        self.assertIn("host_key_policy", options)
        self.assertNotIn("timeout", options)

    def test_provider_builders(self):
        # Built from new records: the providers' packages needn't be installed.
        s3 = self.Connection.new(
            {"protocol": "s3", "s3_access_key_id": "AK", "s3_region": "eu-west-2"}
        )
        self.assertEqual(
            s3._fsspec_kwargs_s3({"s3_secret_access_key": "SK"}),
            {
                "key": "AK",
                "secret": "SK",
                "endpoint_url": None,
                "client_kwargs": {"region_name": "eu-west-2"},
            },
        )
        azure = self.Connection.new(
            {
                "protocol": "abfs",
                "azure_auth": "service_principal",
                "azure_account_name": "acct",
                "azure_tenant_id": "t",
                "azure_client_id": "c",
            }
        )
        self.assertEqual(
            azure._fsspec_kwargs_abfs({"azure_client_secret": "cs"}),
            {
                "account_name": "acct",
                "tenant_id": "t",
                "client_id": "c",
                "client_secret": "cs",
            },
        )
        azure.azure_auth = "default"
        self.assertIs(azure._fsspec_kwargs_abfs({})["anon"], False)
        gcs = self.Connection.new({"protocol": "gcs", "gcs_auth": "service_account"})
        info = {"type": "service_account", "client_email": "x@y"}
        options = gcs._fsspec_kwargs_gcs({"service_account": json.dumps(info)})
        self.assertEqual(options["token"], info)

    def test_from_legacy_splits_shares_and_keeps_bad_options(self):
        options = json.dumps(
            {
                "host": "sftp.example",
                "username": "edi",
                "password": "pw",
                "port": 22,
                "look_for_keys": False,
            }
        )
        first = self.Connection._from_legacy("ssh", options)
        self.assertEqual(first.protocol, "sftp")
        self.assertEqual(first.name, "sftp://edi@sftp.example")
        self.assertEqual((first.host, first.port), ("sftp.example", 22))
        self.assertEqual(first.sudo().secrets, {"password": "pw"})
        self.assertEqual(
            json.loads(first.sudo().storage_options), {"look_for_keys": False}
        )
        self.assertEqual(self.Connection._from_legacy("sftp", options), first)

        broken = self.Connection._from_legacy("sftp", "{not json")
        self.assertNotEqual(broken, first)
        self.assertEqual(broken.sudo().storage_options, "{not json")

        with self.assertRaises(UserError):
            self.Connection._from_legacy("webdav", "{}")

    def test_file_operations(self):
        local = self.Connection.create({"name": "Local", "protocol": "file"})
        root = tempfile.mkdtemp()
        source = os.path.join(root, "in", "orders.csv")
        with local._opened(source) as handle:  # creates in/
            handle.write(b"a,b\n")
        self.assertEqual(local._glob(os.path.join(root, "in", "*.csv")), [source])

        claimed = local._sweep(
            os.path.join(root, "in", "*.csv"), os.path.join(root, "done")
        )
        self.assertEqual(claimed, [os.path.join(root, "done", "orders.csv")])
        with local._open(claimed[0]) as handle:
            self.assertEqual(handle.read(), b"a,b\n")

    def test_no_connection_raises(self):
        with self.assertRaises(UserError):
            self.Connection.browse()._open("/tmp/x")
