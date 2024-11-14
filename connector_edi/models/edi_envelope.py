import base64
import json

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class EdiEnvelope(models.Model):
    """
    Group of messages + optional header and footer
    """

    _name = "edi.envelope"
    _description = "EDI Envelope"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    route_id = fields.Many2one("edi.envelope.route", required=True, index=True)
    backend_id = fields.Many2one("edi.backend", index=True, required=True)
    partner_id = fields.Many2one(
        related="backend_id.partner_id", store=True, index=True
    )
    direction = fields.Selection([("in", "In"), ("out", "Out")], index=True)
    content = fields.Binary(attachment=True, copy=False)
    content_filename = fields.Char()
    legacy_body = fields.Text()
    use_legacy_body = fields.Boolean(default=False, index=True)
    body = fields.Text(
        compute="_compute_body",
        inverse="_inverse_body",
        store=False,
    )
    type = fields.Char(help="Optional message type")
    external_id = fields.Char(string="External ID", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    date_done = fields.Datetime()
    edi_message_ids = fields.One2many(
        "edi.message",
        "envelope_id",
    )
    message_count = fields.Integer(compute="_compute_edi_message_count", store=False)
    active = fields.Boolean(default=True)
    exc_info = fields.Text(string="Full Exception Information", readonly=True)
    exc_name = fields.Char(string="Exception Name", readonly=True)
    vacuum_date = fields.Datetime(default=False)
    metadata = fields.Serialized(
        help="Optional message metadata", string="Optional Metadata"
    )
    # XXX: Temporary workaround to display serialized field on frontend
    metadata_string = fields.Char(
        compute="_compute_metadata_string",
        string="Metadata",
    )

    def _compute_metadata_string(self):
        for record in self:
            record.metadata_string = json.dumps(record.metadata)

    def _get_content(self):
        self.ensure_one()
        if self.content:
            return base64.b64decode(self.with_context(bin_size=False).content).decode(
                "utf-8"
            )
        return False

    def _set_content(self, content, filename=None, encoding="utf-8"):
        self.ensure_one()
        if not isinstance(content, bytes):
            content = bytes(content, encoding)

        if filename:
            self.content_filename = filename
        self.content = base64.b64encode(content)

    def _compute_body(self):
        for record in self:
            if record.use_legacy_body:
                record.body = record.legacy_body
            else:
                record.body = record._get_content()

    def _inverse_body(self):
        for record in self:
            if record.body and record.use_legacy_body:
                record.legacy_body = record.body
            elif record.body and not record.use_legacy_body:
                record._set_content(record.body)

    def action_migrate_legacy_body_to_attachment(self):
        self.ensure_one()
        if not self.use_legacy_body:
            return

        self.use_legacy_body = False

        if not self.vacuum_date:
            self._set_content(self.legacy_body)
            self.legacy_body = False

    def _compute_edi_message_count(self):
        message_data = self.env["edi.message"].read_group(
            domain=[("envelope_id", "in", self.ids)],
            fields=["envelope_id"],
            groupby="envelope_id",
        )

        mapped_data = {
            data["envelope_id"][0]: data["envelope_id_count"] for data in message_data
        }

        for record in self:
            record.message_count = mapped_data.get(record.id, 0)

    def run(self):
        for record in self.filtered(lambda r: r.state == "pending"):
            if record.direction == "in":
                record._open_messages()
            if record.direction == "out":
                record._send_envelopes()

    def _open_messages(self):
        # Extract messages from an envelope
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            usage = "codec.{action}".format(action=self.route_id.codec)
            exporter = work.component(usage=usage)
            exporter.open(self)
        self.action_done()

    def _send_envelopes(self):
        route_ids = self.mapped("route_id")
        for route_id in route_ids:
            route_id.send_envelopes(
                envelope_ids=self.filtered(lambda e: e.route_id == route_id)
            )

    @api.model
    def _enclose_messages(self, route_id, message_ids=None):
        assert route_id.direction in [
            "both",
            "out",
        ], "Must be an export route to use _create_envelopes_from_messages"

        if not message_ids:
            message_ids = self.env["edi.message"].search(
                [
                    ("state", "=", "pending"),
                    ("direction", "=", "export"),
                    ("route_id", "=", route_id.id),
                    ("envelope_id", "=", False),
                    ("backend_id", "=", route_id.backend_id.id),
                ]
            )

        with route_id.backend_id.work_on(self._name) as work:
            usage = "codec.{action}".format(action=route_id.codec)
            exporter = work.component(usage=usage)
            exporter.enclose(message_ids)

        message_ids.action_done()

    def action_view_messages(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_message"
        )
        action["domain"] = [("envelope_id", "in", self.ids)]
        return action

    def action_error(self, msg=None, exc_info=None, exc_name=None):
        for record in self:
            record.state = "error"
            partners_to_subscribe = record.backend_id._subscribe_partners()
            if partners_to_subscribe:
                record.message_subscribe(partner_ids=partners_to_subscribe.ids)

            if not msg:
                msg = "Unknown error occured" if not exc_name else exc_name

            vals = {
                "exc_name": False,
                "exc_info": False,
            }

            if exc_name:
                vals.update(
                    {
                        "exc_name": exc_name,
                    }
                )

            if exc_info:
                vals.update(
                    {
                        "exc_info": exc_info,
                    }
                )

            record.message_post(
                body=tools.html_escape(msg),
                subtype_xmlid="connector_edi.mt_message_error",
            )

            if vals:
                record.write(vals)

    def action_pending(self):
        for record in self:
            if record.state == "done":
                raise UserError(
                    _("Cannot mark as envelope as pending when already done!")
                )
            record.state = "pending"
            record._event("on_pending").notify(record)

    def action_done(self, msg=None):
        for record in self:
            if record.state == "done":
                raise UserError(_("Cannot mark as envelope as done when already done!"))
            record.date_done = fields.Datetime.now()
            record.state = "done"
            record.exc_name = False
            record.exc_info = False
            record._event("on_done").notify(record)
            if msg:
                record.message_post(body=msg)
