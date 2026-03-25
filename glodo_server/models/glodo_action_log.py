from odoo import api, fields, models

ACTION_TYPES = [
    ("become", "Become User"),
    ("archive", "Archive User"),
    ("unarchive", "Unarchive User"),
    ("sync", "Sync Users"),
    ("enroll", "Enrollment"),
    ("other", "Other"),
]


class GlodoActionLog(models.Model):
    _name = "glodo.action.log"
    _description = "Glodo Cloud Action Log"
    _order = "create_date desc"

    instance_id = fields.Many2one(
        "glodo.instance",
        required=True,
        ondelete="cascade",
        index=True,
    )

    instance_name = fields.Char(
        related="instance_id.name",
        string="Instance Name",
        store=True,
    )

    remote_user_id = fields.Many2one(
        "glodo.remote.user",
        ondelete="set null",
    )

    remote_user_login = fields.Char(
        related="remote_user_id.login",
        string="Remote User Login",
        store=True,
    )

    admin_user_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="restrict",
        default=lambda self: self.env.user,
    )

    admin_user_login = fields.Char(
        related="admin_user_id.login",
        string="Admin Login",
        store=True,
    )

    action_type = fields.Selection(
        ACTION_TYPES,
        required=True,
        index=True,
    )

    action_timestamp = fields.Datetime(
        default=fields.Datetime.now,
        required=True,
    )

    payload = fields.Text(
        help="The payload sent with the request (if applicable)",
    )

    result = fields.Char(
        help="Outcome of the action",
    )

    notes = fields.Text()

    ip_address = fields.Char(
        help="IP address from which the action was initiated",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("action_timestamp"):
                vals["action_timestamp"] = fields.Datetime.now()
        return super().create(vals_list)

    def _compute_display_name(self):
        for log in self:
            action_label = dict(ACTION_TYPES).get(log.action_type, log.action_type)
            log.display_name = (
                f"{log.instance_name} - {action_label} - {log.admin_user_login}"
            )
