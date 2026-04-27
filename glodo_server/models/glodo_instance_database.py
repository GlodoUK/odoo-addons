"""
Glodo Cloud instance database model.

Represents a database within a managed Odoo instance.
Each instance can have multiple databases.
"""

import json
import logging
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

EXPIRY_WARNING_DAYS = 30


class GlodoInstanceDatabase(models.Model):
    _name = "glodo.instance.database"
    _description = "Database on Managed Instance"
    _order = "instance_id, name"

    name = fields.Char(
        required=True,
        index=True,
    )

    active = fields.Boolean(
        default=True,
    )

    instance_id = fields.Many2one(
        "glodo.instance",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )

    instance_name = fields.Char(
        related="instance_id.name",
        store=True,
        readonly=True,
    )

    instance_url = fields.Char(
        related="instance_id.url",
    )

    instance_active = fields.Boolean(
        related="instance_id.active",
    )

    remote_user_ids = fields.One2many(
        "glodo.remote.user",
        "database_id",
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

    user_count = fields.Integer(
        string="Internal User Count",
        readonly=True,
        help="Number of internal users reported by the remote",
    )

    expiration_date = fields.Datetime(
        readonly=True,
        help="Enterprise subscription expiration date reported by the remote",
    )

    expiration_reason = fields.Char(
        readonly=True,
        help="Enterprise subscription expiration reason reported by the remote",
    )

    expiration_state = fields.Selection(
        [("success", "OK"), ("warning", "Expiring Soon"), ("danger", "Expired")],
        compute="_compute_expiration_state",
        search="_search_expiration_state",
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

    cloc_data_json = fields.Text(
        string="CLOC (JSON)",
        readonly=True,
        help="Raw CLOC payload as reported by the remote.",
    )

    cloc_total = fields.Integer(
        string="CLOC Total",
        compute="_compute_cloc_totals",
        store=True,
        readonly=True,
    )

    cloc_modules_total = fields.Integer(
        string="CLOC Modules",
        compute="_compute_cloc_totals",
        store=True,
        readonly=True,
        help="Lines of code counted in custom-module source trees, including "
        "tests/ and static/tests/. Excludes core, enterprise, and any modules "
        "listed in the instance's CLOC Excluded Modules.",
    )

    cloc_customization_total = fields.Integer(
        string="CLOC Customization",
        compute="_compute_cloc_totals",
        store=True,
        readonly=True,
        help="Lines of code counted in studio actions, manual compute fields, "
        "and imported-module artifacts stored in the database. Excludes any "
        "modules listed in the instance's CLOC Excluded Modules.",
    )

    last_user_sync = fields.Datetime(
        readonly=True,
    )

    notes = fields.Text()

    _unique_instance_database = models.Constraint(
        "UNIQUE(instance_id, name)", "Database name must be unique per instance."
    )

    @api.depends("remote_user_ids", "remote_user_ids.is_archived")
    def _compute_remote_user_count(self):
        if not self.ids:
            self.active_remote_user_count = self.inactive_remote_user_count = 0
            return

        count_data = defaultdict(lambda: {"active": 0, "inactive": 0})

        remote_user_data = self.env["glodo.remote.user"]._read_group(
            [("database_id", "in", self.ids)],
            ["database_id", "is_archived"],
            ["__count"],
        )

        for database, is_archived, count in remote_user_data:
            key = "inactive" if is_archived else "active"
            count_data[database.id][key] = count

        for db in self:
            db.active_remote_user_count = count_data[db.id]["active"]
            db.inactive_remote_user_count = count_data[db.id]["inactive"]

    @api.depends("expiration_date")
    def _compute_expiration_state(self):
        now = fields.Datetime.now()
        warning_threshold = now + relativedelta(days=EXPIRY_WARNING_DAYS)
        for db in self:
            expiration_date = db.expiration_date
            if not expiration_date:
                db.expiration_state = "success"
                continue
            db.expiration_state = (
                "danger"
                if expiration_date <= now
                else "warning"
                if expiration_date <= warning_threshold
                else "success"
            )

    # See _search_status on HelpdeskSlaStatus for a similar search method
    @api.model
    def _search_expiration_state(self, operator, value):
        if operator != "in":
            return NotImplemented
        now = fields.Datetime.now()
        warning_threshold = now + relativedelta(days=EXPIRY_WARNING_DAYS)
        domains = []
        if "success" in value:
            domains.append(
                [
                    "|",
                    ("expiration_date", "=", False),
                    ("expiration_date", ">", warning_threshold),
                ]
            )
        if "warning" in value:
            domains.append(
                [
                    ("expiration_date", "!=", False),
                    ("expiration_date", ">", now),
                    ("expiration_date", "<=", warning_threshold),
                ]
            )
        if "danger" in value:
            domains.append(
                [
                    ("expiration_date", "!=", False),
                    ("expiration_date", "<=", now),
                ]
            )
        return Domain.OR(domains)

    @api.model
    def _cloc_vals_from_payload(self, cloc_payload):
        """Return ``{cloc_data_json: ...}`` from a ``cloc`` payload.

        The payload follows the shape emitted by
        ``glodo_client.utils.cloc.count``: a dict with ``modules``,
        ``customization``, ``errors``. Totals are derived in
        ``_compute_cloc_totals`` so they pick up changes to the instance's
        excluded-modules list without re-syncing.
        """
        if not isinstance(cloc_payload, dict) or not cloc_payload:
            return {"cloc_data_json": False}
        return {"cloc_data_json": json.dumps(cloc_payload, sort_keys=True)}

    @api.depends("cloc_data_json", "instance_id.cloc_excluded_modules")
    def _compute_cloc_totals(self):
        for db in self:
            modules_total = 0
            customization_total = 0
            if db.cloc_data_json:
                try:
                    payload = json.loads(db.cloc_data_json)
                except Exception:
                    payload = {}
                excluded = db.instance_id._parse_excluded_modules()
                modules_total = sum(
                    v
                    for k, v in (payload.get("modules") or {}).items()
                    if k not in excluded and isinstance(v, int)
                )
                customization_total = sum(
                    v
                    for k, v in (payload.get("customization") or {}).items()
                    if k not in excluded and isinstance(v, int)
                )
            db.cloc_modules_total = modules_total
            db.cloc_customization_total = customization_total
            db.cloc_total = modules_total + customization_total

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
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Users - %(db)s", db=self.name),
            "res_model": "glodo.remote.user",
            "view_mode": "list,form",
            "domain": [("database_id", "=", self.id)],
            "context": {
                "default_database_id": self.id,
                "search_default_filter_active": 1,
            },
        }
