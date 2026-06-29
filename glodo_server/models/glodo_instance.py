"""
Glodo Cloud managed instance model.

Represents a remote Odoo server that can contain multiple databases.
Uses AES-GCM with a shared secret for secure communication.
"""

import base64
import json
import logging
import secrets
from collections import defaultdict

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..utils.crypto import AESGCMCrypto, generate_shared_secret

_logger = logging.getLogger(__name__)


class GlodoInstance(models.Model):
    _name = "glodo.instance"
    _description = "Glodo Cloud Managed Instance"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(
        required=True,
    )

    active = fields.Boolean(
        default=True,
        tracking=True,
    )

    unique_id = fields.Char(
        readonly=True,
        copy=False,
        index=True,
    )

    url = fields.Char(
        string="Instance URL",
        help="Base URL of the managed Odoo instance",
    )

    git_repo_url = fields.Char(
        string="Git Repo URL", help="URL for the Active GitHub Repository"
    )

    git_branch = fields.Char(help="The name of the live branch")

    shared_secret = fields.Char(
        string="Shared Secret (Base64)",
        readonly=True,
        copy=False,
        groups="base.group_system",
        help="AES-256 shared secret for encrypted communication",
    )

    partner_id = fields.Many2one(
        "res.partner",
        index=True,
    )

    tag_ids = fields.Many2many(
        "glodo.instance.tag",
    )

    database_ids = fields.One2many(
        "glodo.instance.database",
        "instance_id",
        string="Databases",
        readonly=True,
    )

    action_log_ids = fields.One2many(
        "glodo.action.log",
        "instance_id",
        string="Action Logs",
        readonly=True,
    )

    database_count = fields.Integer(
        compute="_compute_database_count",
        store=True,
        readonly=True,
    )

    active_remote_user_count = fields.Integer(
        "Active Users",
        compute="_compute_remote_user_count",
        store=True,
    )

    inactive_remote_user_count = fields.Integer(
        "Inactive Users",
        compute="_compute_remote_user_count",
        store=True,
    )

    last_sync_date = fields.Datetime(
        string="Last Sync",
        readonly=True,
    )

    odoo_version = fields.Char(
        readonly=True,
    )

    cloc_excluded_modules = fields.Char(
        string="CLOC Excluded Modules",
        help="Comma-separated list of module names (or the literal "
        "'odoo/studio') to exclude from CLOC totals for this instance. "
        "Applies to every database under the instance.",
    )

    notes = fields.Text()

    is_managed = fields.Boolean(string="Managed?", default="1")

    host_id = fields.Many2one("glodo.instance.host")

    def _parse_excluded_modules(self):
        self.ensure_one()
        raw = self.cloc_excluded_modules
        if not raw:
            return set()
        return {part.strip() for part in raw.split(",") if part.strip()}

    @api.depends("database_ids")
    def _compute_database_count(self):
        for instance in self:
            instance.database_count = len(instance.database_ids)

    @api.depends(
        "database_ids.remote_user_ids", "database_ids.remote_user_ids.is_archived"
    )
    def _compute_remote_user_count(self):
        if not self.ids:
            self.active_remote_user_count = self.inactive_remote_user_count = 0
            return

        count_data = defaultdict(lambda: {"active": 0, "inactive": 0})

        remote_user_data = self.env["glodo.remote.user"]._read_group(
            [("instance_id", "in", self.ids)],
            ["instance_id", "is_archived"],
            ["__count"],
        )

        for instance, is_archived, count in remote_user_data:
            key = "inactive" if is_archived else "active"
            count_data[instance.id][key] = count

        for instance in self:
            instance.active_remote_user_count = count_data[instance.id]["active"]
            instance.inactive_remote_user_count = count_data[instance.id]["inactive"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("unique_id"):
                # Generate a short unique ID for this instance
                vals["unique_id"] = secrets.token_urlsafe(16)
            if not vals.get("shared_secret"):
                vals["shared_secret"] = generate_shared_secret()
        return super().create(vals_list)

    def action_regenerate_secret(self):
        self.ensure_one()

        self.shared_secret = generate_shared_secret()

        _logger.info("Glodo Cloud: Regenerated shared secret for %s", self.name)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Secret Regenerated"),
                "message": self.env._(
                    "New shared secret generated. "
                    "Update the client's odoo.conf with the new secret."
                ),
                "type": "warning",
                "sticky": True,
            },
        }

    def _get_crypto(self) -> AESGCMCrypto:
        """Get a crypto handler configured for this instance."""
        self.ensure_one()

        if not self.sudo().shared_secret:
            raise UserError(self.env._("Instance shared secret not configured."))

        try:
            secret_bytes = base64.b64decode(self.sudo().shared_secret)
        except Exception as e:
            raise UserError(self.env._("Invalid shared secret format.")) from e

        return AESGCMCrypto(secret_bytes, ttl=300)

    def _make_encrypted_request(
        self,
        endpoint: str,
        payload: dict,
        method: str = "POST",
        timeout: int = 30,
    ) -> dict:
        """
        Make an AES-GCM encrypted request to the client instance.

        Args:
            endpoint: API endpoint path (e.g., "/glodo_cloud/users")
            payload: Request payload to encrypt
            method: HTTP method (default: POST)
            timeout: Request timeout in seconds

        Returns:
            Response JSON data

        Raises:
            UserError: If request fails
        """
        self.ensure_one()

        if not self.active:
            raise UserError(self.env._("Instance is not active."))

        if not self.url:
            raise UserError(self.env._("Instance URL not configured."))

        crypto = self._get_crypto()
        encrypted_data = crypto.encrypt(payload)

        url = f"{self.url.rstrip('/')}{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        try:
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    json=encrypted_data,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                response = requests.get(
                    url,
                    params=encrypted_data,
                    headers=headers,
                    timeout=timeout,
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as e:
            raise UserError(
                self.env._(
                    "Connection to %(name)s timed out.",
                    name=self.name,
                )
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise UserError(
                self.env._(
                    "Could not connect to %(name)s at %(url)s.",
                    name=self.name,
                    url=self.url,
                )
            ) from e
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = response.json()
                error_msg = error_data.get("error", str(e))
            except (ValueError, AttributeError) as json_err:
                _logger.debug("Could not parse error response as JSON: %s", json_err)
            raise UserError(
                self.env._(
                    "Request to %(name)s failed: %(error)s",
                    name=self.name,
                    error=error_msg,
                )
            ) from e
        except ValueError as e:
            raise UserError(
                self.env._(
                    "Invalid response from %(name)s.",
                    name=self.name,
                )
            ) from e

    def action_sync_info(self):
        """Fetch and sync instance and database info from the remote."""
        self.ensure_one()

        if not self.active:
            raise UserError(self.env._("Instance is not active."))

        try:
            response = self._make_encrypted_request(
                "/glodo_cloud/info",
                {},
                timeout=180,
            )
        except Exception as e:
            _logger.error("Failed to fetch info from %s: %s", self.name, e)
            raise

        # Update instance-level info
        instance_info = response.get("instance", {})
        self.odoo_version = instance_info.get("odoo_version", "")

        # Sync databases
        Database = self.env["glodo.instance.database"]
        databases_data = response.get("databases", [])
        seen_db_names = set()

        for db_data in databases_data:
            db_name = db_data.get("name")
            if not db_name:
                continue

            seen_db_names.add(db_name)

            existing = Database.search(
                [
                    ("instance_id", "=", self.id),
                    ("name", "=", db_name),
                ],
                limit=1,
            )

            db_vals = {
                "user_count": db_data.get("user_count", 0),
                "expiration_date": db_data.get("expiration_date") or False,
                "expiration_reason": db_data.get("expiration_reason") or False,
                "installed_modules_json": json.dumps(
                    db_data.get("installed_modules", [])
                ),
            }
            db_vals.update(Database._cloc_vals_from_payload(db_data.get("cloc") or {}))

            if existing:
                existing.write(db_vals)
            else:
                db_vals.update(
                    {
                        "instance_id": self.id,
                        "name": db_name,
                    }
                )
                Database.create(db_vals)

        # Mark databases no longer present as inactive
        stale_dbs = Database.search(
            [
                ("instance_id", "=", self.id),
                ("name", "not in", list(seen_db_names)),
                ("active", "=", True),
            ]
        )
        if stale_dbs:
            stale_dbs.write({"active": False})

        self.last_sync_date = fields.Datetime.now()

        _logger.info(
            "Synced info from instance %s: %d databases",
            self.name,
            len(databases_data),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Info Synced"),
                "message": self.env._(
                    "Successfully synced %(count)d databases from %(name)s.",
                    count=len(databases_data),
                    name=self.name,
                ),
                "type": "success",
                "sticky": True,
            },
        }

    def action_view_databases(self):
        """View databases for this instance."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Databases - %(name)s", name=self.name),
            "res_model": "glodo.instance.database",
            "view_mode": "list,form" if self.database_count != 1 else "form",
            "domain": [("instance_id", "=", self.id)],
            "res_id": self.database_ids[0].id if len(self.database_ids) == 1 else False,
            "context": {"default_instance_id": self.id},
        }

    def action_view_remote_users(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Users - %(name)s", name=self.name),
            "res_model": "glodo.remote.user",
            "view_mode": "list,form",
            "domain": [("instance_id", "=", self.id)],
            "context": {
                "search_default_filter_active": 1,
            },
        }

    def action_view_action_logs(self):
        """View action logs for this instance."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Action Logs - %(name)s", name=self.name),
            "res_model": "glodo.action.log",
            "view_mode": "list,form",
            "domain": [("instance_id", "=", self.id)],
        }

    def action_ping_db(self):
        """Ping the remote instance to check connectivity."""
        self.ensure_one()

        if not self.active:
            raise UserError(self.env._("Instance is not active."))

        try:
            response = self._make_encrypted_request(
                "/glodo_cloud/ping",
                {},
                timeout=10,
                method="GET",
            )
        except Exception as e:
            _logger.error("Ping to %s failed: %s", self.name, e)
            raise

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Ping Successful"),
                "message": self.env._(
                    "Successfully connected to %(name)s."
                    " Status: %(response)s, Enrolled: %(enrolled)s",
                    name=self.name,
                    response=response.get("status", ""),
                    enrolled=response.get("enrolled", ""),
                ),
                "type": "success",
                "sticky": False,
            },
        }
