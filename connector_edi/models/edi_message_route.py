from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr

from .edi_envelope_route import INTERVAL_TYPES


class EdiMessageRoute(models.Model):
    _name = "edi.route"
    _description = "EDI Message Route"
    _order = "sequence,id"

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
    )
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

    @api.constrains("envelope_route_id", "backend_id")
    def _constrain_envelope_backend(self):
        for record in self:
            if record.backend_id != record.envelope_route_id.backend_id:
                raise ValidationError(_("Envelope route and backend must match!"))

    def _component_usage(self):
        self.ensure_one()
        return "action.{action}".format(action=self.action)

    def send_messages(self, **kwargs):
        # generate and send messages
        todo = self.filtered(lambda m: m.direction == "out")
        for record in todo:
            record.with_delay()._run_out(**kwargs)

    def read_messages(self, **kwargs):
        # TODO: This function is missing :|
        raise NotImplementedError("Whoops... I guess we need to fix this bit")

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

        return super(EdiMessageRoute, self).unlink()

    def write(self, vals):
        res = super(EdiMessageRoute, self).write(vals)

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
            "name": "EDI: {} - Message Route {}".format(
                self.backend_id.name, self.name
            ),
            "numbercall": -1,
            "interval_number": self.cron_interval_number,
            "interval_type": self.cron_interval_type,
            "active": self.active,
            "model_id": self.env["ir.model"]
            .search([("model", "=", self._name)], limit=1)
            .id,
            "code": """
record = model.browse(%d)
record.with_delay()._run_out()
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
