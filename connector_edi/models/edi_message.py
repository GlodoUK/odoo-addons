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
    Record that might have related EDI messages
    """

    _name = "edi.message.mixin"
    _description = "Abstract record where EDI messages can be assigned"

    edi_message_ids = fields.One2many(
        "edi.message", compute="_compute_edi_message_ids", string="EDI Messages"
    )
    edi_message_count = fields.Integer(compute="_compute_edi_message_ids")

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
        action["domain"] = [("id", "in", self.mapped("edi_message_ids").ids)]
        return action


class EdiMessage(models.Model):
    """
    Group of messages + optional header and footer
    """

    _name = "edi.message"
    _description = "EDI Message"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    message_route_id = fields.Many2one("edi.route", index=True)
    backend_id = fields.Many2one("edi.backend", index=True)
    direction = fields.Selection(
        [("in", "In"), ("out", "Out")], required=True, index=True
    )
    partner_id = fields.Many2one(
        related="backend_id.partner_id", store=True, index=True
    )
    envelope_id = fields.Many2one(
        "edi.envelope",
        required=False,
        index=True,
        ondelete="cascade",
    )
    envelope_route_id = fields.Many2one(
        related="envelope_id.route_id", index=True, store=True
    )
    external_id = fields.Char(required=True)
    content = fields.Binary(attachment=True)
    content_filename = fields.Char()
    legacy_body = fields.Text()
    use_legacy_body = fields.Boolean(default=False, index=True)
    body = fields.Text(compute="_compute_body", inverse="_inverse_body", store=False)
    type = fields.Char(help="Optional message type")
    metadata = fields.Serialized(
        help="Optional message metadata", string="Message Metadata"
    )
    # XXX: Temporary workaround to display serialized field on frontend
    metadata_string = fields.Char(
        compute="_compute_metadata_string",
        string="Metadata",
    )
    active = fields.Boolean(default=True)
    vacuum_date = fields.Datetime(default=False)

    def _get_content(self):
        self.ensure_one()
        if self.content:
            return base64.b64decode(self.with_context(bin_size=False).content)
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
        self._set_content(self.legacy_body)
        self.legacy_body = False

    def _compute_metadata_string(self):
        for record in self:
            record.metadata_string = json.dumps(record.metadata)

    test = fields.Boolean(default=False, help="Indicates a test message", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    acknowledged = fields.Boolean(compute="_compute_acknowledged", store=True)
    exc_info = fields.Text(string="Full Exception Information", readonly=True)
    exc_name = fields.Char(string="Exception Name", readonly=True)

    @api.depends("acknowledgement_message_id")
    def _compute_acknowledged(self):
        for record in self:
            record.acknowledged = bool(record.acknowledgement_message_id)

    acknowledgement_message_id = fields.Many2one("edi.message", index=True)
    acknowledgement_for_message_ids = fields.One2many(
        "edi.message", "acknowledgement_message_id"
    )
    model = fields.Char(
        index=True,
        required=False,
        readonly=True,
        string="Related Document",
    )
    res_id = fields.Integer("Related Document ID", index=True)
    related = fields.Char(
        string="Reference", compute="_compute_reference", readonly=True, store=False
    )

    @api.depends("model", "res_id")
    def _compute_reference(self):
        for res in self:
            res.related = "{},{}".format(res.model, res.res_id)

    done_date = fields.Datetime(index=True)

    @property
    def record(self):
        if self.model and self.res_id:
            return self.env[self.model].browse(self.res_id)

    def action_read(self):
        self._read_message()

    def action_send(self):
        for record in self:
            if not record.envelope_route_id:
                record._assign_envelope_route()

            opts = record.envelope_route_id._with_delay_options(
                usage="enclose_messages"
            )

            self.env["edi.envelope"].with_delay(**opts)._enclose_messages(
                record.envelope_route_id,
                record,
            )

    def _associate_with(self, record):
        self.ensure_one()
        self.write({"model": record._name, "res_id": record.id})

        message_post = getattr(record, "message_post", None)

        if message_post and callable(message_post):
            message_post(
                body=_(
                    "Created from <a href=# data-oe-model=edi.message"
                    " data-oe-id=%(id)d>%(name)s</a>"
                )
                % {"id": self.id, "name": self.display_name}
            )

        self.message_post(
            body=_(
                "Associated with <a href=# data-oe-model=%(model)s"
                " data-oe-id=%(id)d>%(name)s</a>"
            )
            % {
                "model": record._name,
                "id": record.id,
                "name": record.display_name,
            }
        )

    def _assign_message_route_domain(self):
        self.ensure_one()

        return [
            ("envelope_route_id", "=", self.envelope_route_id.id),
            ("direction", "=", self.direction),
        ]

    def _assign_envelope_route(self):
        self.ensure_one()
        if self.envelope_route_id:
            return

        self.envelope_route_id = self.message_route_id.envelope_route_id

    def _assign_message_route(self):
        self.ensure_one()
        if self.message_route_id:
            return

        route_ids = self.env["edi.route"].search(self._assign_message_route_domain())

        for route_id in route_ids:
            domain = [("id", "=", self.id)]

            if route_id.domain:
                domain += safe_eval(route_id.domain)

            # TODO in 13+ we should use the filtered_domain method
            if self.search_count(domain) > 0:
                self.message_route_id = route_id
                return

        raise EdiException("Could not assign a message route")

    def action_pending(self):
        for record in self:
            if record.state == "done":
                raise UserError(_("You cannot re-process a done message"))

            try:
                if not record.message_route_id and record.direction == "in":
                    record._assign_message_route()
                if not record.envelope_route_id and record.direction == "out":
                    record._assign_envelope_route()

                record.state = "pending"
                record._event("on_pending").notify(record)
            except EdiException as e:
                buff = io.StringIO()
                traceback.print_exc(file=buff)
                self.action_error(
                    exc_info=buff.getvalue(),
                    exc_name=e.__class__.__name__,
                    msg=str(e),
                )

    def action_done(self, msg=None):
        for record in self:
            if record.state == "done":
                raise UserError(_("You cannot mark as a done message as done!"))

            record.done_date = fields.Datetime.now()
            record.state = "done"
            record.exc_name = False
            record.exc_info = False
            if msg:
                record.message_post(body=msg)

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

    def action_process(self, **kwargs):
        for record in self:
            try:
                with self.env.cr.savepoint():
                    if record.state == "done":
                        raise UserError(_("You cannot re-process a done message"))

                    if not record.message_route_id:
                        raise UserError(
                            _("No assigned message action. Do not know how to process.")
                        )

                    with record.backend_id.work_on(record._name) as work:
                        exporter = work.component(
                            usage=record.message_route_id._component_usage()
                        )

                        method_name = "run_{direction}".format(
                            direction=LOOKUP_DICT.get(record.direction)
                        )
                        method = getattr(exporter, method_name, None)
                        if not method:
                            raise NotImplementedError("Unknown message action")

                        method(record, **kwargs)
                        record.action_done()

            except (EdiException, UserError, NotImplementedError) as e:
                buff = io.StringIO()
                traceback.print_exc(file=buff)
                record.action_error(
                    exc_info=buff.getvalue(),
                    exc_name=e.__class__.__name__,
                    msg=str(e),
                )

    def _read_message(self, **kwargs):
        self.action_process(**kwargs)
