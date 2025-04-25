import base64
import json

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class EdiEnvelope(models.Model):
    """
    Group of messages, plus optional header and footer
    """

    _name = "edi.envelope"
    _description = "EDI Envelope"
    _inherit = ["mail.activity.mixin", "mail.thread"]

    active = fields.Boolean(
        default=True,
    )

    backend_id = fields.Many2one(
        "edi.backend",
        index=True,
        required=True,
    )

    route_id = fields.Many2one(
        "edi.envelope.route",
        index=True,
        required=True,
    )

    partner_id = fields.Many2one(
        related="backend_id.partner_id",
        index=True,
        store=True,
    )

    edi_message_ids = fields.One2many(
        "edi.message",
        "envelope_id",
    )

    message_count = fields.Integer(
        compute="_compute_edi_message_count",
    )

    direction = fields.Selection(
        [("in", "In"), ("out", "Out")],
        index=True,
    )

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

    use_legacy_body = fields.Boolean(
        index=True,
    )

    exc_name = fields.Char(
        string="Exception",
        readonly=True,
    )

    external_id = fields.Char(
        "External ID",
        required=True,
    )

    type = fields.Char(help="Optional Message Type")

    body = fields.Text(
        compute="_compute_body",
        inverse="_inverse_body",
        store=False,
    )

    exc_info = fields.Text(
        string="Exception Info",
        readonly=True,
    )

    legacy_body = fields.Text()

    date_done = fields.Datetime()

    vacuum_date = fields.Datetime()

    metadata = fields.Serialized(
        help="Optional message metadata", string="Optional Metadata"
    )

    # XXX: Temporary workaround to display serialized field on frontend
    metadata_string = fields.Char(
        compute="_compute_metadata_string",
        string="Metadata",
    )

    content = fields.Binary(attachment=True, copy=False)
    content_filename = fields.Char()

    def _compute_metadata_string(self):
        for record in self:
            record.metadata_string = json.dumps(record.metadata)

    def _get_content(self):
        self.ensure_one()

        return (
            base64.b64decode(self.with_context(bin_size=False).content).decode("utf-8")  # noqa: E501
            if self.content
            else False
        )

    def _set_content(self, content, filename=None, encoding="utf-8"):
        self.ensure_one()

        if not isinstance(content, bytes):
            content = bytes(content, encoding)

        if filename:
            self.content_filename = filename

        self.content = base64.b64encode(content)

    def _compute_body(self):
        for envelope in self:
            envelope.body = (
                envelope.legacy_body
                if envelope.use_legacy_body
                else envelope._get_content()
            )

    def _inverse_body(self):
        for envelope in self:
            if envelope.body and envelope.use_legacy_body:
                envelope.legacy_body = envelope.body
            elif envelope.body and not envelope.use_legacy_body:
                envelope._set_content(envelope.body)

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
        for envelope in self.filtered(lambda e: e.state == "pending"):
            if envelope.direction == "in":
                envelope._open_messages()
            if envelope.direction == "out":
                envelope._send_envelopes()

    def _open_messages(self):
        self.ensure_one()

        with self.backend_id.work_on(self._name) as work:
            usage = f"codec.{self.route_id.codec}"
            exporter = work.component(usage=usage)
            exporter.open(self)

        self.action_done()

    def _send_envelopes(self):
        for route in self.mapped("route_id"):
            route.send_envelopes(
                envelope_ids=self.filtered(
                    lambda e, route_id=route_id: e.route_id == route_id
                )
            )

    @api.model
    def _enclose_messages(self, route_id, message_ids=None):
        if route_id.direction not in ("out", "both"):
            msg = _("Must be an export route to use _enclose_messages")
            raise UserError(msg)

        if not message_ids:
            message_ids = self.env["edi.message"].search(
                [
                    ("direction", "=", "export"),
                    ("state", "=", "pending"),
                    ("backend_id", "=", route_id.backend_id.id),
                    ("envelope_id", "=", False),
                    ("route_id", "=", route_id.id),
                ]
            )

        with route_id.backend_id.work_on(self._name) as work:
            usage = f"codec.{route_id.codec}"
            exporter = work.component(usage=usage)
            exporter.enclose(message_ids)

        message_ids.action_done()

    def action_view_messages(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_message"
        )

        action.update({"domain": [("envelope_id", "in", self.ids)]})

        return action

    def action_error(self, msg=None, exc_info=None, exc_name=None):
        for message in self:
            message.state = "error"

            partners_to_subscribe = message.backend_id._subscribe_partners()
            if partners_to_subscribe:
                message.message_subscribe(partner_ids=partners_to_subscribe.ids)

            if not msg:
                msg = "Unknown error occured" if not exc_name else exc_name

            vals = {
                "exc_name": exc_name or False,
                "exc_info": exc_info or False,
            }

            message.message_post(
                body=tools.html_escape(msg),
                subtype_xmlid="connector_edi.mt_message_error",
            )

            if vals:
                message.write(vals)

    def action_done(self, msg=None):
        for envelope in self:
            if envelope.state == "done":
                msg = _("Cannot mark a Done envelope as Done!")
                raise UserError(msg)

            envelope.write(
                {
                    "exc_info": False,
                    "exc_name": False,
                    "date_done": fields.Datetime.now(),
                    "state": "done",
                }
            )

            envelope._event("on_done").notify(envelope)

            if msg:
                envelope.message_post(body=msg)

    def action_pending(self):
        for envelope in self:
            if envelope.state == "done":
                msg = _("Cannot mark a Done envelope as Pending!")
                raise UserError(msg)

            envelope.state = "pending"

            envelope._event("on_pending").notify(envelope)
