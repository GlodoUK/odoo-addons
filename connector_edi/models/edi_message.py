import base64
import io
import json
import traceback

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from ..exceptions import EdiException

LOOKUP_DICT = {"in": "read", "out": "write"}


class EdiMessageMixin(models.AbstractModel):
    """
    Model that might have related EDI messages
    """

    _name = "edi.message.mixin"
    _description = "Abstract model where EDI messages can be assigned"

    edi_message_ids = fields.One2many(
        "edi.message",
        compute="_compute_edi_message_ids",
    )

    edi_message_count = fields.Integer(
        compute="_compute_edi_message_ids",
    )

    def _edi_message_ids_domain(self):
        self.ensure_one()
        return [("model", "=", self._name), ("res_id", "=", self.id)]

    def _compute_edi_message_ids(self):
        for record in self:
            record.edi_message_ids = (
                self.env["edi.message"].sudo().search(self._edi_message_ids_domain())
            )
            record.edi_message_count = len(record.edi_message_ids)

    def action_view_edi_messages(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_message"
        )

        action.update({"domain": [("id", "in", self.mapped("edi_message_ids").ids)]})

        return action


class EdiMessage(models.Model):
    _name = "edi.message"
    _description = "EDI Message"
    _inherit = ["mail.activity.mixin", "mail.thread"]

    active = fields.Boolean(
        default=True,
    )

    backend_id = fields.Many2one(
        "edi.backend",
        index=True,
    )

    envelope_id = fields.Many2one(
        "edi.envelope",
        index=True,
        ondelete="cascade",
        required=False,
    )

    envelope_route_id = fields.Many2one(
        related="envelope_id.route_id",
        index=True,
        store=True,
    )

    message_route_id = fields.Many2one(
        "edi.route",
        index=True,
    )

    partner_id = fields.Many2one(
        related="backend_id.partner_id",
        index=True,
        store=True,
    )

    direction = fields.Selection(
        [("in", "In"), ("out", "Out")],
        index=True,
        required=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        index=True,
        required=True,
        tracking=True,
    )

    test = fields.Boolean(
        help="Indicates a test message.",
        readonly=True,
    )

    use_legacy_body = fields.Boolean(
        index=True,
    )

    external_id = fields.Char(
        required=True,
    )

    type = fields.Char(help="Optional message type")

    body = fields.Text(
        compute="_compute_body",
        inverse="_inverse_body",
    )

    legacy_body = fields.Text()

    metadata = fields.Serialized(
        help="Optional message metadata", string="Message Metadata"
    )
    # XXX: Temporary workaround to display serialized field on frontend
    metadata_string = fields.Char(
        compute="_compute_metadata_string",
        string="Metadata",
    )

    done_date = fields.Datetime(
        index=True,
    )

    vacuum_date = fields.Datetime()

    content = fields.Binary(attachment=True)
    content_filename = fields.Char()

    def _get_content(self):
        self.ensure_one()

        return (
            base64.b64decode(self.with_context(bin_size=False).content)
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
        for message in self:
            message.body = (
                message.legacy_body
                if message.use_legacy_body
                else message._get_content()
            )

    def _inverse_body(self):
        for message in self:
            if message.body and message.use_legacy_body:
                message.legacy_body = message.body
            elif message.body and not message.use_legacy_body:
                message._set_content(message.body)

    def action_migrate_legacy_body_to_attachment(self):
        self.ensure_one()

        if self.use_legacy_body:
            self._set_content(self.legacy_body)
            self.legacy_body = False
            self.use_legacy_body = False

    def _compute_metadata_string(self):
        for record in self:
            record.metadata_string = json.dumps(record.metadata)

    exc_info = fields.Text(
        string="Exception Info",
        readonly=True,
    )

    exc_name = fields.Char(
        string="Exception",
        readonly=True,
    )
    acknowledged = fields.Boolean(
        compute="_compute_acknowledged",
        store=True,
    )

    acknowledgement_message_id = fields.Many2one(
        "edi.message",
        index=True,
    )

    acknowledgement_for_message_ids = fields.One2many(
        "edi.message",
        "acknowledgement_message_id",
    )

    model = fields.Char(
        "Related Document",
        index=True,
        readonly=True,
    )

    related = fields.Char(
        "Reference",
        compute="_compute_reference",
        readonly=True,
    )

    res_id = fields.Integer(
        "Related Document ID",
        index=True,
    )

    @api.depends("acknowledgement_message_id")
    def _compute_acknowledged(self):
        for message in self:
            message.acknowledged = bool(message.acknowledgement_message_id)

    @api.depends("model", "res_id")
    def _compute_reference(self):
        for message in self:
            message.related = f"{message.model},{message.res_id}"

    @property
    def record(self):
        if self.model and self.res_id:
            return self.env[self.model].browse(self.res_id)

    def action_read(self):
        self._read_message()

    def action_send(self):
        for message in self:
            message._assign_envelope_route()

            opts = message.envelope_route_id._with_delay_options(
                usage="enclose_messages"
            )

            self.env["edi.envelope"].with_delay(**opts)._enclose_messages(
                message.envelope_route_id,
                message,
            )

    # FIXME

    # def _associate_with(self, record):
    #     self.ensure_one()

    #     self.write({
    #         "model": record._name,
    #         "res_id": record.id
    #     })

    #     message_post = getattr(record, "message_post", None)

    #     if message_post and callable(message_post):
    #         message_post(
    #             body=_(
    #                 "Created from <a href=# data-oe-model=edi.message"
    #                 " data-oe-id=%(id)d>%(name)s</a>"
    #             )
    #             % {"id": self.id, "name": self.display_name}
    #         )

    #     self.message_post(
    #         body=_(
    #             "Associated with <a href=# data-oe-model=%(model)s"
    #             " data-oe-id=%(id)d>%(name)s</a>"
    #         )
    #         % {
    #             "model": record._name,
    #             "id": record.id,
    #             "name": record.display_name,
    #         }
    #     )

    def _assign_message_route_domain(self):
        self.ensure_one()
        return [
            ("direction", "=", self.direction),
            ("envelope_route_id", "=", self.envelope_route_id.id),
        ]

    def _assign_envelope_route(self):
        self.ensure_one()
        if not self.envelope_route_id:
            self.envelope_route_id = self.message_route_id.envelope_route_id

    def _assign_message_route(self):
        self.ensure_one()

        if self.message_route_id:
            return

        domain = self._assign_message_route_domain()
        route_ids = self.env["edi.route"].search(domain)

        for route in route_ids:
            domain = [("id", "=", self.id)]

            if route.domain:
                domain += safe_eval(route.domain)

            if self.filtered_domain(domain):
                self.message_route_id = route
                return

        msg = _("Could not assign a message route!")
        raise EdiException(msg)

    def action_pending(self):
        for message in self:
            if message.state == "done":
                msg = _("You cannot reprocess a Done message!")
                raise UserError(msg)

            try:
                if not message.message_route_id and message.direction == "in":
                    message._assign_message_route()

                if not message.envelope_route_id and message.direction == "out":
                    message._assign_envelope_route()

                message.state = "pending"

                message._event("on_pending").notify(message)

            except EdiException as e:
                buff = io.StringIO()
                traceback.print_exc(file=buff)

                self.action_error(
                    exc_info=buff.getvalue(),
                    exc_name=e.__class__.__name__,
                    msg=str(e),
                )

    def action_done(self, msg=None):
        for message in self:
            if message.state == "done":
                msg = _("You cannot mark a Done message as Done!")
                raise UserError(msg)

            message.write(
                {
                    "done_date": fields.Datetime.now(),
                    "exc_info": False,
                    "exc_name": False,
                    "state": "done",
                }
            )

            if msg:
                message.message_post(body=msg)

    def action_error(self, msg=None, exc_info=None, exc_name=None):
        for message in self:
            message.state = "error"

            partners_to_subscribe = message.backend_id._subscribe_partners()
            if partners_to_subscribe:
                message.message_subscribe(partner_ids=partners_to_subscribe.ids)

            if not msg:
                msg = "Unknown error occured" if not exc_name else exc_name

            vals = {
                "exc_info": exc_info or False,
                "exc_name": exc_name or False,
            }

            message.message_post(
                body=tools.html_escape(msg),
                subtype_xmlid="connector_edi.mt_message_error",
            )

            if vals:
                message.write(vals)

    def action_process(self, **kwargs):
        for message in self:
            try:
                with self.env.cr.savepoint():
                    if message.state == "done":
                        msg = _("You cannot reprocess a Done message")
                        raise UserError(msg)

                    if not message.message_route_id:
                        msg = _("No assigned message action. Cannot process!")
                        raise UserError(msg)

                    with message.backend_id.work_on(message._name) as work:
                        exporter = work.component(
                            usage=message.message_route_id._component_usage()
                        )

                        method_name = f"run_{LOOKUP_DICT.get(message.direction)}"
                        method = getattr(exporter, method_name, None)
                        if not method:
                            raise NotImplementedError("Unknown message action")

                        method(message, **kwargs)
                        message.action_done()

            except (EdiException, NotImplementedError, UserError) as e:
                buff = io.StringIO()
                traceback.print_exc(file=buff)

                message.action_error(
                    exc_info=buff.getvalue(),
                    exc_name=e.__class__.__name__,
                    msg=str(e),
                )

    def _read_message(self, **kwargs):
        self.action_process(**kwargs)
