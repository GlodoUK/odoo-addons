from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EdiEnvelopeRoute(models.Model):
    _name = "edi.envelope.route"
    _inherit = ["mail.thread", "mail.alias.mixin", "edi.envelope.route"]

    protocol = fields.Selection(
        selection_add=[("mail", "Email")], ondelete={"mail": "cascade"}
    )

    def _alias_get_creation_values(self):
        vals = super(EdiEnvelopeRoute, self)._alias_get_creation_values()
        vals["alias_model_id"] = self.env["ir.model"]._get(self._name).id
        if self.id:
            vals["alias_defaults"] = {"edi_route_id": self.id}
        return vals

    @api.model
    def message_update(self, msg_dict, update_vals=None):
        raise NotImplementedError(
            _("Updating an existing message attached to an edi.route is not supported.")
        )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Overrides mail_thread message_new(), called by the mailgateway through
        message_process, to manually process this mail.
        """
        if not custom_values:
            custom_values = {}

        route_id = custom_values.get("edi_route_id")

        if not route_id:
            raise UserWarning("Could not determine the edi.route to use")

        if "message" not in custom_values:
            raise UserWarning("Raw message missing")

        envelope_route_id = self.env["edi.envelope.route"].browse(route_id)

        if envelope_route_id.protocol != "mail":
            raise UserWarning(
                "Can only handle message_new for envelope routes of type 'mail'"
            )

        envelope_id = self.env["edi.envelope"].create(
            {
                "backend_id": envelope_route_id.backend_id.id,
                "external_id": msg_dict.get("message_id", ""),
                "body": custom_values.get("message").as_string(),
                "route_id": envelope_route_id.id,
                "direction": "in",
            }
        )

        post_params = dict(subtype_xmlid="mail.mt_comment", partner_ids=[], **msg_dict)
        envelope_id.message_post(**post_params)
        envelope_id.action_pending()

        # return nothing so that upstream stops
        return envelope_id

    @api.constrains("protocol", "direction", "protocol_in_trigger")
    def _constrains_mail_protocol(self):
        for record in self.filtered(lambda r: r.protocol == "mail"):
            if record.direction != "in":
                raise ValidationError(
                    _(
                        "connector_edi_protocol_mail only supports inbound"
                        " mail at this time"
                    )
                )

            if record.protocol_in_trigger != "none":
                raise ValidationError(
                    _(
                        "connector_edi_protocol_mail only supports"
                        " protocol_in_trigger of 'none'"
                    )
                )
