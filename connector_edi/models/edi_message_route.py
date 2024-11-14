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

    sequence = fields.Integer()
    name = fields.Char(required=True)
    backend_id = fields.Many2one(
        "edi.backend", index=True, required=True, ondelete="cascade"
    )
    active = fields.Boolean(related="backend_id.active", store=True)
    envelope_route_id = fields.Many2one(
        "edi.envelope.route",
        index=True,
        required=True,
    )
    direction = fields.Selection(
        [("in", "In"), ("out", "Out")],
        required=True,
    )
    action = fields.Selection(
        [("none", "None"), ("code", "Python Code")],
        required=True,
        string="Message Action",
    )
    action_code = fields.Text(string="Message Action Code")
    action_trigger = fields.Selection(
        [("none", "None"), ("model_event", "Model Event"), ("schedule", "Schedule")],
        required=True,
        copy=False,
        default="none",
    )
    show_action_code = fields.Boolean(compute="_compute_show_action_code")
    model_event_id = fields.Many2one(
        "edi.route.event",
        string="Model Event",
    )
    model = fields.Char(
        related="model_event_id.res_model",
        readonly=True,
        store=True,
        index=True,
    )
    model_event = fields.Char(related="model_event_id.name", store=True, index=True)
    domain = fields.Char(
        default="[]",
        string="Model Event Domain",
        help=(
            "This domain is appended to the existing search criteria (i.e."
            " direction, state, etc.)"
        ),
    )
    cron_id = fields.Many2one(
        "ir.cron",
        copy=False,
    )
    cron_interval_number = fields.Integer(default=5)
    cron_interval_type = fields.Selection(INTERVAL_TYPES, default="minutes")

    queue_priority = fields.Integer(default=QUEUE_PRIORITY_DEFAULT)
    queue_identity_exact = fields.Boolean(default=False)
    queue_channel = fields.Char()
    queue_max_retries = fields.Integer(default=0)

    vacuum_content = fields.Boolean(default=False)
    vacuum_content_after_days = fields.Integer(default=14)

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
        for record in self:
            record.show_action_code = record.action == "code"

    @api.constrains("envelope_route_id", "backend_id")
    def _constrain_envelope_backend(self):
        for record in self:
            if record.backend_id != record.envelope_route_id.backend_id:
                raise ValidationError(_("Envelope route and backend must match!"))

    def _component_usage(self):
        self.ensure_one()
        return f"action.{self.action}"

    def send_messages(self, **kwargs):
        # generate and send messages
        todo = self.filtered(lambda m: m.direction == "out")
        for record in todo:
            record.with_delay(**record._with_delay_options())._run_out(**kwargs)

    def read_messages(self, **kwargs):
        # TODO: This function is missing :|
        raise NotImplementedError("Whoops... I guess we need to fix this bit")

    def _with_delay_options(self):
        self.ensure_one()

        opts = {}

        if self.queue_identity_exact:
            opts.update({"identity_key": identity_exact})

        items = [
            "priority",
            "channel",
            "max_retries",
        ]

        for i in items:
            value = getattr(self, "queue_%s" % (i))
            if value:
                opts.update({i: value})

        return opts

    def _run_out(self, **kwargs):
        self.ensure_one()

        assert self.direction == "out", "Must be an export route to use _run_out"

        with self.backend_id.work_on("edi.message") as work:
            component = work.component(usage=self._component_usage())
            component.run_write(self, **kwargs)

    def _run_in(self, **kwargs):
        self.ensure_one()

        assert self.direction == "in", "Must be an export route to use _run_out"

        with self.backend_id.work_on("edi.message") as work:
            component = work.component(usage=self._component_usage())
            component.run_read(self, **kwargs)

    def unlink(self):
        cron_ids = self.mapped("cron_id")

        if cron_ids:
            cron_ids.unlink()

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
            if any(i in trigger_fields for i in vals.keys()):
                self.with_context(
                    edi_connector_envelope_route_skip_cron_sync=True
                ).action_sync_cron()

        return res

    def _cron_vals(self):
        self.ensure_one()

        return {
            "name": f"EDI: {self.backend_id.name} - Message Route {self.name}",
            "numbercall": -1,
            "interval_number": self.cron_interval_number,
            "interval_type": self.cron_interval_type,
            "active": self.active,
            "model_id": self.env["ir.model"]
            .search([("model", "=", self._name)], limit=1)
            .id,
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
        for record in self:
            record._cron_sync()

    @api.model
    def send_messages_using_first_match(self, backend_id, record, domain=None):
        if not domain:
            domain = []

        domain += [("backend_id", "=", backend_id.id), ("direction", "=", "out")]

        matching_ids = self.search(domain)
        for route_id in matching_ids:
            if not route_id.domain or route_id.domain == "[]":
                route_id.send_messages(record=record)
                break

            if route_id.model_event_id and route_id.model:
                record_count = self.env[route_id.model].search_count(
                    safe_eval(route_id.domain) + [("id", "=", record.id)]
                )
                if record_count > 0:
                    route_id.send_messages(record=record)
                    break

    @api.constrains("action", "action_code")
    def _check_python_code(self):
        for r in self.sudo().filtered(lambda r: r.action == "code"):
            msg = test_python_expr(expr=(r.action_code or "").strip(), mode="exec")
            if msg:
                raise ValidationError(msg)
