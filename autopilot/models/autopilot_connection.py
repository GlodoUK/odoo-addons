import base64
import binascii
import json

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL

from .. import tools

# A module adds a provider with ``selection_add``, a
# ``_fsspec_kwargs_<protocol>`` builder and a page on the form.
PROTOCOLS = [
    ("file", "Local Filesystem"),
    ("ftp", "FTP"),
    ("sftp", "SFTP"),
    ("s3", "Amazon S3 / S3-compatible"),
    ("gcs", "Google Cloud Storage"),
    ("abfs", "Azure Blob Storage"),
    ("http", "HTTP(S)"),
    ("gdrive", "Google Drive"),
]

# fsspec aliases, for ``_from_legacy``.
LEGACY_ALIASES = {
    "local": "file",
    "ssh": "sftp",
    "s3a": "s3",
    "gs": "gcs",
    "az": "abfs",
    "abfss": "abfs",
    "https": "http",
}

# Write-only: set through ``<name>_input``, kept in admin-only ``secrets``,
# never sent to the browser. ``<name>_set`` says one is stored.
SECRETS = (
    "password",
    "private_key",
    "private_key_password",
    "s3_secret_access_key",
    "service_account",
    "azure_account_key",
    "azure_connection_string",
    "azure_sas_token",
    "azure_client_secret",
    "http_token",
)

# Uploaded as files: a password input would lose their newlines.
UPLOADED_SECRETS = ("private_key", "service_account")

# For ``_from_legacy``: option -> field, or ("secret", name).
LEGACY_FIELDS = {
    "ftp": {
        "host": "host",
        "port": "port",
        "username": "username",
        "password": ("secret", "password"),
        "timeout": "timeout",
        "tls": "ftp_tls",
    },
    "sftp": {
        "host": "host",
        "port": "port",
        "username": "username",
        "password": ("secret", "password"),
        "timeout": "timeout",
    },
    "s3": {
        "key": "s3_access_key_id",
        "secret": ("secret", "s3_secret_access_key"),
        "endpoint_url": "s3_endpoint_url",
    },
    "abfs": {
        "account_name": "azure_account_name",
        "account_key": ("secret", "azure_account_key"),
        "connection_string": ("secret", "azure_connection_string"),
        "sas_token": ("secret", "azure_sas_token"),
        "tenant_id": "azure_tenant_id",
        "client_id": "azure_client_id",
        "client_secret": ("secret", "azure_client_secret"),
    },
}


def _secret_input(string, upload=False, **kwargs):
    if upload:
        field, kwargs = fields.Binary, dict(kwargs, attachment=False)
    else:
        field = fields.Char
    return field(
        string=string,
        compute="_compute_secret_inputs",
        inverse="_inverse_secret_inputs",
        **kwargs,
    )


def _secret_set():
    return fields.Boolean(compute="_compute_secret_set", compute_sudo=True)


def _merge(base, override):
    """Deep merge, e.g. a region into advanced ``client_kwargs``."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


class AutopilotConnection(models.Model):
    """A file endpoint shared by every connector. Backends point at one and
    keep their own paths. Work through ``_glob``, ``_sweep``, ``_archive``,
    ``_open`` and ``_opened`` rather than the filesystem.

    The provider's fields override the same option in ``storage_options``.
    """

    _name = "autopilot.connection"
    _description = "Connection"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", index=True, default=lambda self: self.env.company
    )
    protocol = fields.Selection(
        PROTOCOLS,
        string="Provider",
        required=True,
        default="sftp",
    )
    storage_options = fields.Text(
        string="Advanced Options",
        groups="base.group_system",
        copy=False,
        help="Any other settings for this provider, as JSON. The fields above "
        "win over the same setting here.",
    )

    # FTP / SFTP (username also for HTTP basic auth)
    host = fields.Char(help="The server's name or address.")
    port = fields.Integer(help="Empty for the protocol's default (FTP 21, SFTP 22).")
    username = fields.Char()
    timeout = fields.Integer(string="Timeout (s)")
    ftp_tls = fields.Boolean(string="Use TLS (FTPS)")
    host_key = fields.Char(
        copy=False,
        help="The SFTP server's public host key ('<type> <base64>'). Once set, "
        "a server presenting any other key is refused. Empty trusts whatever "
        "key the server presents. Test Connection pins it when empty.",
    )

    # S3 and S3-compatible
    s3_access_key_id = fields.Char(string="Access Key ID")
    s3_endpoint_url = fields.Char(
        string="Endpoint URL",
        help="Empty for Amazon S3. For an S3-compatible store (MinIO, Wasabi, "
        "Cloudflare R2, DigitalOcean Spaces, ...), its endpoint.",
    )
    s3_region = fields.Char(string="Region", help="e.g. eu-west-2")

    # Google Cloud Storage / Google Drive
    gcs_auth = fields.Selection(
        [
            ("service_account", "Service Account Key"),
            ("google_default", "Application Default Credentials"),
            ("cloud", "Compute Metadata (running on Google Cloud)"),
            ("anon", "Anonymous (public buckets only)"),
        ],
        string="Google Authentication",
        default="service_account",
    )
    gcs_project = fields.Char(string="Project")
    gdrive_root_id = fields.Char(
        string="Root Folder ID",
        help="A shared drive or folder ID to treat as the root. Empty for the "
        "service account's own drive. Share files with the service account's "
        "email address.",
    )
    read_only = fields.Boolean(help="Request read-only access.")

    # Azure Blob Storage
    azure_auth = fields.Selection(
        [
            ("account_key", "Account Key"),
            ("connection_string", "Connection String"),
            ("sas_token", "SAS Token"),
            ("service_principal", "Service Principal (Entra ID)"),
            ("default", "Default Azure Credential (managed identity, ...)"),
            ("anon", "Anonymous (public containers only)"),
        ],
        string="Azure Authentication",
        default="account_key",
    )
    azure_account_name = fields.Char(string="Storage Account")
    azure_tenant_id = fields.Char(string="Tenant ID")
    azure_client_id = fields.Char(string="Client ID")

    # HTTP(S)
    http_auth = fields.Selection(
        [("none", "None"), ("basic", "Basic"), ("bearer", "Bearer Token")],
        string="HTTP Authentication",
        default="none",
    )

    # Never shown: written through the *_input fields, read with sudo().
    secrets = fields.Json(groups="base.group_system", copy=False, prefetch=False)
    password_input = _secret_input("Password")
    password_set = _secret_set()
    private_key_input = _secret_input(
        "Private Key File",
        upload=True,
        help="Upload an SSH private key file (OpenSSH or PEM) to replace the "
        "stored one. It is checked, then stored and never shown again.",
    )
    private_key_set = _secret_set()
    private_key_password_input = _secret_input(
        "Private Key Password",
        help="The password the private key is encrypted with, if any.",
    )
    private_key_password_set = _secret_set()
    s3_secret_access_key_input = _secret_input("Secret Access Key")
    s3_secret_access_key_set = _secret_set()
    service_account_input = _secret_input(
        "Service Account Key File",
        upload=True,
        help="Upload the service account's JSON key file, as downloaded from "
        "Google Cloud.",
    )
    service_account_set = _secret_set()
    azure_account_key_input = _secret_input("Account Key")
    azure_account_key_set = _secret_set()
    azure_connection_string_input = _secret_input("Connection String")
    azure_connection_string_set = _secret_set()
    azure_sas_token_input = _secret_input("SAS Token")
    azure_sas_token_set = _secret_set()
    azure_client_secret_input = _secret_input("Client Secret")
    azure_client_secret_set = _secret_set()
    http_token_input = _secret_input("Bearer Token")
    http_token_set = _secret_set()
    private_key_fingerprint = fields.Char(
        compute="_compute_private_key_fingerprint",
        compute_sudo=True,
        help="The stored private key's type and SHA256 fingerprint.",
    )

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    def _compute_secret_inputs(self):
        for connection in self:
            for name in SECRETS:
                connection[f"{name}_input"] = False

    def _inverse_secret_inputs(self):
        # One inverse for every input, so values saved together (a key and
        # its password) are checked together.
        for connection in self:
            values = {
                name: connection[f"{name}_input"]
                for name in SECRETS
                if connection[f"{name}_input"]
            }
            for name in UPLOADED_SECRETS:
                if name in values:
                    values[name] = connection._decode_upload(values[name])
            if values:
                connection._store_secrets(values)

    def _decode_upload(self, value):
        try:
            return base64.b64decode(value).decode()
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValidationError(
                self.env._("The uploaded file is not a text key file.")
            ) from exc

    def _store_secrets(self, values):
        self.ensure_one()
        stored = self.sudo()
        secrets = dict(stored.secrets or {})
        # Never trim a password: spaces can be part of it.
        secrets.update(
            {
                name: value.strip()
                if name in ("private_key", "service_account")
                else value
                for name, value in values.items()
            }
        )
        if secrets.get("private_key") and (
            "private_key" in values or "private_key_password" in values
        ):
            try:
                tools.ssh.load_private_key(
                    secrets["private_key"], secrets.get("private_key_password")
                )
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
        if "service_account" in values:
            try:
                info = json.loads(secrets["service_account"])
            except ValueError as exc:
                raise ValidationError(
                    self.env._("The service account key is not valid JSON.")
                ) from exc
            if not isinstance(info, dict) or info.get("type") != "service_account":
                raise ValidationError(
                    self.env._(
                        "That is not a service account key (its JSON has no "
                        '"type": "service_account").'
                    )
                )
        stored.secrets = secrets

    def _secrets(self):
        self.ensure_one()
        return dict(self.sudo().secrets or {})

    @api.depends("secrets")
    def _compute_secret_set(self):
        for connection in self:
            secrets = connection.secrets or {}
            for name in SECRETS:
                connection[f"{name}_set"] = bool(secrets.get(name))

    @api.depends("secrets")
    def _compute_private_key_fingerprint(self):
        for connection in self:
            secrets = connection.secrets or {}
            if not secrets.get("private_key"):
                connection.private_key_fingerprint = False
                continue
            try:
                key = connection._load_private_key()
            except ValueError:
                connection.private_key_fingerprint = self.env._("Unreadable key")
                continue
            connection.private_key_fingerprint = (
                f"{key.get_name()} {tools.ssh.fingerprint(key)}"
            )

    def _load_private_key(self):
        secrets = self._secrets()
        return tools.ssh.load_private_key(
            secrets["private_key"], secrets.get("private_key_password") or None
        )

    def action_clear_secret(self):
        """Clears the credentials named in context ``secret`` (one or a
        list)."""
        self.check_access("write")
        names = self.env.context.get("secret") or ()
        if isinstance(names, str):
            names = (names,)
        if not set(names) <= set(SECRETS):
            raise UserError(self.env._("Unknown credential: %s", names))
        for connection in self:
            stored = connection.sudo()
            secrets = dict(stored.secrets or {})
            for name in names:
                secrets.pop(name, None)
            stored.secrets = secrets

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    @api.constrains("protocol")
    def _check_protocol(self):
        import fsspec

        for connection in self:
            try:
                fsspec.get_filesystem_class(connection.protocol)
            except (ImportError, ValueError) as exc:
                raise ValidationError(
                    self.env._(
                        "The '%(protocol)s' provider is not available: %(error)s",
                        protocol=connection.protocol,
                        error=exc,
                    )
                ) from exc

    @api.constrains("active")
    def _check_archive_unused(self):
        """Users are found from every stored Many2one to this model in the
        registry, so connectors declare nothing."""
        archived = self.filtered(lambda connection: not connection.active)
        if not archived:
            return
        for model in self.env.registry.values():
            if model._abstract:
                continue
            for field in model._fields.values():
                if not (
                    field.type == "many2one"
                    and field.store
                    and field.comodel_name == self._name
                ):
                    continue
                users = (
                    self.env[model._name]
                    .sudo()
                    .search([(field.name, "in", archived.ids)], limit=1)
                )
                if users:
                    raise ValidationError(
                        self.env._(
                            "%(connection)s is still used by %(record)s; point "
                            "that elsewhere (or archive it) first.",
                            connection=users[field.name].display_name,
                            record=users.display_name,
                        )
                    )

    @api.constrains("storage_options")
    def _check_storage_options(self):
        for connection in self.sudo():
            try:
                tools.files.parse_options(connection.storage_options)
            except ValueError as exc:
                raise ValidationError(
                    self.env._("%(name)s: %(error)s", name=connection.name, error=exc)
                ) from exc

    @api.constrains("host_key")
    def _check_host_key(self):
        for connection in self.filtered("host_key"):
            try:
                tools.ssh.parse_host_key_line(connection.host_key)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

    # ------------------------------------------------------------------
    # The filesystem
    # ------------------------------------------------------------------
    def _fs(self, **extra):
        """Advanced options, overridden by the provider's fields (``None``
        dropped), overridden by ``extra``. Credentials are read with
        ``sudo()``, so a job connects whoever runs it. fsspec caches the
        instance by its arguments, so calling this per operation is cheap."""
        if not self:
            raise UserError(self.env._("No %s is configured.", self._description))
        self.ensure_one()
        stored = self.sudo()
        try:
            options = tools.files.parse_options(stored.storage_options)
        except ValueError as exc:
            raise UserError(
                self.env._("%(name)s: %(error)s", name=self.name, error=exc)
            ) from exc
        builder = getattr(self, f"_fsspec_kwargs_{self.protocol}", None)
        if builder:
            try:
                provided = builder(self._secrets())
            except ValueError as exc:
                raise UserError(
                    self.env._("%(name)s: %(error)s", name=self.name, error=exc)
                ) from exc
            provided = {k: v for k, v in provided.items() if v is not None}
            options = _merge(options, provided)
        options.update(extra)
        return tools.files.filesystem(self.protocol, options)

    def _fsspec_kwargs_file(self, secrets):
        return {}

    def _fsspec_kwargs_ftp(self, secrets):
        return {
            "host": self.host or None,
            "port": self.port or None,
            "username": self.username or None,
            "password": secrets.get("password"),
            "timeout": self.timeout or None,
            "tls": self.ftp_tls,
        }

    def _fsspec_kwargs_sftp(self, secrets):
        options = {
            "host": self.host or None,
            "port": self.port or None,
            "username": self.username or None,
            "password": secrets.get("password"),
            "timeout": self.timeout or None,
        }
        if secrets.get("private_key"):
            options["pkey"] = self._load_private_key()
        if self.host_key:
            options["host_key_policy"] = tools.ssh.pinned_host_key_policy(self.host_key)
        return options

    def _fsspec_kwargs_s3(self, secrets):
        options = {
            "key": self.s3_access_key_id or None,
            "secret": secrets.get("s3_secret_access_key"),
            "endpoint_url": self.s3_endpoint_url or None,
        }
        if self.s3_region:
            options["client_kwargs"] = {"region_name": self.s3_region}
        return options

    def _fsspec_kwargs_gcs(self, secrets):
        if self.gcs_auth == "service_account":
            token = self._service_account(secrets)
        else:
            token = self.gcs_auth
        return {
            "project": self.gcs_project or None,
            "token": token,
            "access": "read_only" if self.read_only else None,
        }

    def _fsspec_kwargs_abfs(self, secrets):
        options = {"account_name": self.azure_account_name or None}
        auth = self.azure_auth
        if auth == "account_key":
            options["account_key"] = secrets.get("azure_account_key")
        elif auth == "connection_string":
            options["connection_string"] = secrets.get("azure_connection_string")
        elif auth == "sas_token":
            options["sas_token"] = secrets.get("azure_sas_token")
        elif auth == "service_principal":
            options.update(
                tenant_id=self.azure_tenant_id or None,
                client_id=self.azure_client_id or None,
                client_secret=secrets.get("azure_client_secret"),
            )
        elif auth == "default":
            # Explicit, so adlfs doesn't consult AZURE_STORAGE_ANON.
            options["anon"] = False
        elif auth == "anon":
            options["anon"] = True
        return options

    def _fsspec_kwargs_http(self, secrets):
        if self.http_auth == "basic":
            import aiohttp

            auth = aiohttp.BasicAuth(self.username or "", secrets.get("password") or "")
            return {"client_kwargs": {"auth": auth}}
        if self.http_auth == "bearer":
            token = secrets.get("http_token") or ""
            return {"client_kwargs": {"headers": {"Authorization": f"Bearer {token}"}}}
        return {}

    def _fsspec_kwargs_gdrive(self, secrets):
        # Only a service account works unattended; the browser flows can't.
        return {
            "token": "service_account",
            "creds": self._service_account(secrets),
            "root_file_id": self.gdrive_root_id or None,
            "access": "read_only" if self.read_only else None,
        }

    def _service_account(self, secrets):
        if not secrets.get("service_account"):
            raise ValueError(self.env._("No service account key is stored."))
        return json.loads(secrets["service_account"])

    # ------------------------------------------------------------------
    # autopilot.tools.files on this endpoint
    # ------------------------------------------------------------------
    def _glob(self, pattern, **kwargs):
        """See ``tools.files.glob``."""
        return tools.files.glob(self._fs(), pattern, **kwargs)

    def _sweep(self, pattern, directory):
        """Claims the matching files by moving them into ``directory``.
        Returns their new paths."""
        return tools.files.sweep(self._fs(), pattern, directory)

    def _archive(self, path, directory):
        """See ``tools.files.archive``."""
        return tools.files.archive(self._fs(), path, directory)

    def _open(self, path, mode="rb", **kwargs):
        """For reading: ``with connection._open(path) as fh``."""
        return self._fs().open(path, mode, **kwargs)

    def _opened(self, path, mode="wb", **kwargs):
        """For writing. Creates the folder, which SFTP won't."""
        return tools.files.opened(self._fs(), path, mode, **kwargs)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_test_connection(self):
        """On SFTP with no host key yet, pins the one presented: trust on
        first use, by someone who can edit the connection."""
        self.ensure_one()
        self.check_access("write")
        recorder = None
        extra = {"skip_instance_cache": True}
        if self.protocol == "sftp" and not self.host_key:
            recorder = tools.ssh.recording_host_key_policy()
            extra["host_key_policy"] = recorder
        try:
            fs = self._fs(**extra)
            path = self._fsspec_test_path(fs)
            if path is not None:
                fs.ls(path)
        except Exception as exc:  # noqa: BLE001  shown to the user
            return self._connection_notification(
                "danger", self.env._("Connection failed"), str(exc)
            )
        message = self.env._("Connected to %s.", self.name)
        if recorder and recorder.key:
            self.host_key = tools.ssh.host_key_line(recorder.key)
            message = self.env._(
                "Connected to %(name)s and pinned its host key %(fingerprint)s. "
                "Check it with the server's administrator.",
                name=self.name,
                fingerprint=tools.ssh.fingerprint(recorder.key),
            )
        return self._connection_notification(
            "success", self.env._("Connection OK"), message, reload=bool(recorder)
        )

    def _fsspec_test_path(self, fs):
        """None only builds the filesystem. SFTP logs in on construction but
        has no root marker, so list its login folder. HTTP has nothing to
        list."""
        if self.protocol == "sftp":
            return "."
        if self.protocol == "http":
            return None
        return fs.root_marker

    def _connection_notification(self, kind, title, message, reload=False):
        params = {"type": kind, "title": title, "message": message, "sticky": False}
        if reload:
            params["next"] = {"type": "ir.actions.client", "tag": "soft_reload"}
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": params,
        }

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------
    @api.model
    def _from_legacy(self, protocol, storage_options, company_id=False):
        """For a connector's migration off ``(protocol, storage_options)``:
        known options move onto fields and ``secrets``, the rest stay as
        advanced options. An identical connection is reused. Options that
        don't parse are kept as they are, bypassing the check."""
        protocol = LEGACY_ALIASES.get(protocol, protocol)
        if protocol not in dict(PROTOCOLS):
            raise UserError(
                self.env._("No connection provider for protocol %r.", protocol)
            )
        raw = (storage_options or "").strip() or False
        try:
            options = tools.files.parse_options(raw)
            valid = True
        except ValueError:
            options, valid = {}, False
        vals, secrets = self._legacy_split(protocol, options)
        advanced = (json.dumps(options) if options else False) if valid else raw
        for existing in self.with_context(active_test=False).search(
            [("protocol", "=", protocol), ("company_id", "=", company_id)]
        ):
            stored = existing.sudo()
            if (
                all(existing[name] == value for name, value in vals.items())
                and (stored.secrets or {}) == secrets
                and (stored.storage_options or False) == advanced
            ):
                return existing
        connection = self.create(
            dict(
                vals,
                protocol=protocol,
                company_id=company_id,
                name=self._legacy_name(protocol, vals),
                storage_options=advanced if valid else False,
            )
        )
        connection.sudo().secrets = secrets or False
        if not valid:
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET storage_options = %s WHERE id = %s",
                    SQL.identifier(self._table),
                    raw,
                    connection.id,
                )
            )
            connection.invalidate_recordset(["storage_options"])
        return connection

    @api.model
    def _legacy_split(self, protocol, options):
        """Pops the options the provider knows into ``(vals, secrets)``."""
        vals, secrets = {}, {}
        for option, target in LEGACY_FIELDS.get(protocol, {}).items():
            if option not in options:
                continue
            value = options[option]
            if isinstance(target, tuple):
                if isinstance(value, str):
                    secrets[target[1]] = options.pop(option)
                continue
            if self._fields[target].type == "integer":
                if isinstance(value, bool) or not isinstance(value, int | float):
                    continue
                if value != int(value):
                    continue
                value = int(value)
            options.pop(option)
            vals[target] = value
        if protocol == "abfs":
            for auth, secret in (
                ("connection_string", "azure_connection_string"),
                ("account_key", "azure_account_key"),
                ("sas_token", "azure_sas_token"),
                ("service_principal", "azure_client_secret"),
            ):
                if secret in secrets:
                    vals["azure_auth"] = auth
                    break
            else:
                vals["azure_auth"] = "default"
        return vals, secrets

    @api.model
    def _legacy_name(self, protocol, vals):
        host = vals.get("host") or vals.get("s3_endpoint_url")
        host = host or vals.get("azure_account_name")
        user = vals.get("username") or vals.get("s3_access_key_id")
        if host:
            return f"{protocol}://{user}@{host}" if user else f"{protocol}://{host}"
        return protocol
