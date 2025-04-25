from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, registry
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr

from odoo.addons.queue_job.job import identity_exact

from .edi_envelope_route import INTERVAL_TYPES, QUEUE_PRIORITY_DEFAULT


class EdiMessageRoute(models.Model):
    _name = "edi.route"
    _description = "EDI Message Route"
    _order = "sequence,id"
    _inherit = ["edi.external_id.warning.mixin"]

    name = fields.Char(
        required=True,
    )

    sequence = fields.Integer()

    backend_id = fields.Many2one(
        "edi.backend",
        index=True,
        ondelete="cascade",
        required=True,
    )

    active = fields.Boolean(
        related="backend_id.active",
        store=True,
    )

    envelope_route_id = fields.Many2one(
        "edi.envelope.route",
        index=True,
        required=True,
    )

    action = fields.Selection(
        [("none", "None"), ("code", "Python Code")],
        required=True,
    )

    action_trigger = fields.Selection(
        [("none", "None"), ("model_event", "Model Event"), ("schedule", "Schedule")],  # noqa: E501
        copy=False,
        default="none",
        required=True,
    )

    direction = fields.Selection(
        [("in", "In"), ("out", "Out")],
        required=True,
    )

    show_action_code = fields.Boolean(
        compute="_compute_show_action_code",
    )

    action_code = fields.Text(
        "Message Action Code",
    )

    model_event_id = fields.Many2one(
        "edi.route.event",
    )

    model = fields.Char(
        related="model_event_id.res_model",
        index=True,
        store=True,
    )

    model_event = fields.Char(
        related="model_event_id.name",
        index=True,
        store=True,
    )

    domain = fields.Char(
        default="[]",
        string="Model Event Domain",
        help="This domain is appended to the existing search criteria",
    )

    cron_id = fields.Many2one(
        "ir.cron",
        copy=False,
    )

    cron_interval_number = fields.Integer(
        default=5,
    )

    cron_interval_type = fields.Selection(
        INTERVAL_TYPES,
        default="minutes",
    )

    queue_identity_exact = fields.Boolean()

    queue_channel = fields.Char()

    queue_max_retries = fields.Integer(
        default=0,
    )

    queue_priority = fields.Integer(
        default=QUEUE_PRIORITY_DEFAULT,
    )

    vacuum_content = fields.Boolean()

    vacuum_content_after_days = fields.Integer(
        default=14,
    )

    @api.constrains("action", "action_code")
    def _check_python_code(self):
        for route in self.sudo().filtered(lambda r: r.action == "code"):
            msg = test_python_expr(expr=route.code.strip() or "", mode="exec")
            if msg:
                raise ValidationError(msg)

    def action_vacuum_content(self):
        for route_id in self.filtered_domain([("vacuum_content", "=", True)]):
            cut_off = fields.Datetime.now() - relativedelta(
                days=route_id.vacuum_content_after_days
            )
            while True:
                with api.Environment.manage():
                    with registry(self.env.cr.dbname).cursor() as cr:
                        env = api.Environment(cr, self.env.uid, self.env.context)
                        edi_message_ids = env["edi.message"].search(
                            [
                                ("message_route_id", "=", route_id.id),
                                ("state", "=", "done"),
                                ("done_date", "<=", cut_off),
                            ],
                            limit=10,
                        )
                        if not edi_message_ids:
                            break
                        edi_message_ids.unlink()

    @api.depends("action")
    def _compute_show_action_code(self):
        for message_route in self:
            message_route.show_action_code = message_route.action == "code"

    @api.constrains("envelope_route_id", "backend_id")
    def _constrains_backend_id_envelope_route_id(self):
        for message_route in self:
            if message_route.backend_id != message_route.envelope_route_id.backend_id:
                msg = _("The envelope route's backend must match!")
                raise ValidationError(msg)

    def _component_usage(self):
        self.ensure_one()
        return f"action.{self.action}"

    def send_messages(self, **kwargs):
        for route in self.filtered(lambda r: r.direction == "out"):
            route.with_delay(**route._with_delay_options())._run_out(**kwargs)

    def read_messages(self, **kwargs):
        # TODO: This function is missing :|
        raise NotImplementedError("Whoops... I guess we need to fix this bit")

    def _with_delay_options(self):
        self.ensure_one()
        opts = {}

        if self.queue_identity_exact:
            opts.update({"identity_key": identity_exact})

        field_suffix = [
            "channel",
            "max_retries",
            "priority",
        ]

        for suffix in field_suffix:
            value = getattr(self, "queue_%s" % (suffix))
            if value:
                opts.update({suffix: value})

        return opts

    def _run_out(self, **kwargs):
        self.ensure_one()

        if self.direction != "out":
            msg = _("The Direction must be Out to use the _run_out method")
            raise ValidationError(msg)

        with self.backend_id.work_on("edi.message") as work:
            component = work.component(usage=self._component_usage())
            component.run_write(self, **kwargs)

    def _run_in(self, **kwargs):
        self.ensure_one()

        if self.direction != "in":
            msg = _("The Direction must be In to use the _run_in method")
            raise ValidationError(msg)

        with self.backend_id.work_on("edi.message") as work:
            component = work.component(usage=self._component_usage())
            component.run_read(self, **kwargs)

    def unlink(self):
        self.mapped("cron_id").unlink()
        return super().unlink()

    def write(self, vals):
        res = super().write(vals)

        if not self.env.context.get(
            "connector_edi_message_route_skip_cron_sync", False
        ):
            trigger_fields = [
                "active",
                "cron_id",
                "cron_interval_number",
                "cron_interval_type",
            ]

            if any(field in trigger_fields for field in vals.keys()):
                self.with_context(
                    edi_connector_envelope_route_skip_cron_sync=True
                ).action_sync_cron()

        return res

    def _cron_vals(self):
        self.ensure_one()

        ir_model_id = self.env["ir.model"].search([("model", "=", self._name)], limit=1)

        return {
            "name": f"EDI: {self.backend_id.name} - Message Route {self.name}",
            "active": self.active,
            "interval_number": self.cron_interval_number,
            "interval_type": self.cron_interval_type,
            "model_id": ir_model_id.id,
            "code": """
record = model.browse(%d)
record.with_delay(**record._with_delay_options())._run_out()
"""
            % (self.id),
        }

    def _cron_sync(self):
        self.ensure_one()

        if self.action_trigger != "schedule" and self.cron_id:
            self.cron_id.unlink()

        vals = self._cron_vals()

        if self.action_trigger == "schedule" and self.cron_id:
            self.cron_id.sudo().write(vals)

        if self.action_trigger == "schedule" and not self.cron_id:
            self.cron_id = self.env["ir.cron"].sudo().create(vals)

        if self.cron_id:
            self.cron_id.active = self.active

    def action_sync_cron(self):
        for route in self:
            route._cron_sync()

    @api.model
    def send_messages_using_first_match(self, backend_id, record, domain=None):
        if not domain:
            domain = []

        domain += [
            ("backend_id", "=", backend_id.id),
            ("direction", "=", "out"),
        ]

        matching_route_ids = self.search(domain)

        for route in matching_route_ids:
            if not route.domain or route.domain == "[]":
                route.send_messages(record=record)
                break

            if route.model_event_id and route.model:
                record_count = self.env[route.model].search_count(
                    safe_eval(route.domain) + [("id", "=", record.id)]
                )
                if record_count > 0:
                    route.send_messages(record=record)
                    break
