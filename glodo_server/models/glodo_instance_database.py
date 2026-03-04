"""
Glodo Cloud instance database model.

Represents a database within a managed Odoo instance.
Each instance can have multiple databases.
"""

import json
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GlodoInstanceDatabase(models.Model):
    _name = "glodo.instance.database"
    _description = "Database on Managed Instance"
    _order = "instance_id, name"

    name = fields.Char(
        string="Database Name",
        required=True,
        index=True,
    )

    active = fields.Boolean(
        default=True,
    )

    instance_id = fields.Many2one(
        "glodo.instance",
        string="Instance",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )

    instance_name = fields.Char(
        related="instance_id.name",
        string="Instance Name",
        store=True,
        readonly=True,
    )

    instance_url = fields.Char(
        related="instance_id.url",
    )

    instance_active = fields.Boolean(
        related="instance_id.active",
        string="Instance Active",
    )

    remote_user_ids = fields.One2many(
        "glodo.remote.user",
        "database_id",
        string="Remote Users",
        readonly=True,
    )

    remote_user_count = fields.Integer(
        compute="_compute_remote_user_count",
        store=True,
        readonly=True,
    )

    user_count = fields.Integer(
        string="Internal User Count",
        readonly=True,
        help="Number of internal users reported by the remote",
    )

    installed_modules_json = fields.Text(
        string="Installed Modules (JSON)",
        readonly=True,
    )

    installed_modules_html = fields.Html(
        string="Installed Modules",
        readonly=True,
        compute="_compute_installed_modules_html",
    )

    cloc_output = fields.Text(
        string="CLOC Output",
        readonly=True,
    )

    last_user_sync = fields.Datetime(
        readonly=True,
    )

    notes = fields.Text()

    _unique_instance_database = models.Constraint(
        "UNIQUE(instance_id, name)", "Database name must be unique per instance."
    )

    @api.depends("remote_user_ids")
    def _compute_remote_user_count(self):
        for db in self:
            db.remote_user_count = len(db.remote_user_ids)

    @api.depends("installed_modules_json")
    def _compute_installed_modules_html(self):
        for db in self:
            if db.installed_modules_json:
                try:
                    modules = json.loads(db.installed_modules_json)
                    module_list = "<div class='d-flex flex-wrap'>"
                    for mod in modules:
                        module_list += f"<div class='p-2 border rounded m-1'>{mod.get('name', 'Unknown')} (v{mod.get('version', 'x.x.x')})</div>"  # noqa: E501
                    module_list += "</div>"
                    db.installed_modules_html = module_list
                except Exception as e:
                    _logger.error(
                        "Failed to parse installed modules JSON for %s/%s: %s",
                        db.instance_name,
                        db.name,
                        e,
                    )
                    db.installed_modules_html = "<p><em>Invalid module data</em></p>"
            else:
                db.installed_modules_html = "<p><em>No module data</em></p>"

    def action_sync_users(self):
        """Sync users from this database on the remote instance."""
        self.ensure_one()

        instance = self.instance_id
        if not instance.active:
            raise UserError(self.env._("Instance is not active."))

        try:
            response = instance._make_encrypted_request(
                "/glodo_cloud/users",
                {"database": self.name},
            )
        except Exception as e:
            _logger.error(
                "Failed to sync users from %s/%s: %s",
                instance.name,
                self.name,
                e,
            )
            raise

        users_data = response.get("users", [])
        RemoteUser = self.env["glodo.remote.user"]

        seen_remote_ids = set()

        for user_data in users_data:
            remote_id = user_data.get("id")
            if not remote_id:
                continue

            seen_remote_ids.add(remote_id)

            existing = RemoteUser.search(
                [
                    ("database_id", "=", self.id),
                    ("remote_id", "=", remote_id),
                ],
                limit=1,
            )

            user_vals = {
                "name": user_data.get("name", ""),
                "login": user_data.get("login", ""),
                "email": user_data.get("email") or "",
                "is_archived": not user_data.get("active", True),
                "last_login": user_data.get("last_login") or False,
            }

            if existing:
                existing.write(user_vals)
            else:
                user_vals.update(
                    {
                        "database_id": self.id,
                        "remote_id": remote_id,
                    }
                )
                RemoteUser.create(user_vals)

        # Mark users no longer present as deleted
        stale_users = RemoteUser.search(
            [
                ("database_id", "=", self.id),
                ("remote_id", "not in", list(seen_remote_ids)),
            ]
        )
        if stale_users:
            _logger.info(
                "Removing %d stale users for %s/%s",
                len(stale_users),
                instance.name,
                self.name,
            )
            stale_users.unlink()

        self.last_user_sync = fields.Datetime.now()

        _logger.info(
            "Synced %d users from %s/%s",
            len(users_data),
            instance.name,
            self.name,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Users Synced"),
                "message": self.env._(
                    "Successfully synced %(count)d users from %(db)s.",
                    count=len(users_data),
                    db=self.name,
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_remote_users(self):
        """View remote users for this database."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Users - %(db)s", db=self.name),
            "res_model": "glodo.remote.user",
            "view_mode": "list,form",
            "domain": [("database_id", "=", self.id)],
            "context": {"default_database_id": self.id},
        }
