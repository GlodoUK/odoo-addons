Recipe: inbound email
=====================

Triggers belong to the concrete integration, not to pipeline - so there is no
"email tool". Instead, here is the idiomatic way to start a pipeline when a mail
arrives, using Odoo's standard mail-alias gateway.

The principle is simple: **do the least possible in the mail gateway, then hand
off to a queued pipeline.** ``message_new`` runs inside the incoming-mail
request, so it should not parse attachments or touch external systems. It starts
a pipeline and passes a lightweight reference - the message id, never the raw
email - and the real work happens in ordinary stages, off the request thread::

    import io

    from odoo import SUPERUSER_ID, api, fields, models
    from odoo.addons.pipeline import tools


    class SupplierFeed(models.Model):
        _name = "supplier.feed"
        _inherit = ["pipeline.mixin", "mail.alias.mixin"]

        name = fields.Char(required=True)

        # - Alias plumbing: route this feed's alias back to it ---------------
        def _alias_get_creation_values(self):
            values = super()._alias_get_creation_values()
            values["alias_model_id"] = self.env["ir.model"]._get(self._name).id
            if self.id:
                values["alias_defaults"] = {"feed_id": self.id}
            return values

        # - The trigger: a mail arrives, a pipeline starts -------------------
        @api.model
        def message_new(self, msg_dict, custom_values=None):
            feed = self.browse((custom_values or {}).get("feed_id"))
            if not feed:
                raise ValueError("Inbound mail could not be routed to a feed.")
            # Hand off immediately, passing only the message id. sudo() as
            # SUPERUSER keeps the sender from being treated as the acting
            # partner (e.g. auto-assigned to their sales).
            feed.sudo().with_user(SUPERUSER_ID).ingest_mail().run(
                {"message_id": msg_dict.get("message_id")}
            )
            # Return the record the mail threads onto. Odoo persists the message
            # and its attachments here next, so by the time the queued job runs
            # (on commit) they exist and a stage can read them.
            return feed

        # - The work: ordinary stages, off the request thread ---------------
        def ingest_mail(self):
            pipeline = self.pipeline()
            return pipeline.path(
                pipeline.with_delay()._collect_attachments().expand(),
                pipeline.with_delay()._handle_attachment(),
            )

        def _collect_attachments(self, message):
            self.ensure_one()
            mail = self.env["mail.message"].search(
                [("message_id", "=", message["message_id"])], limit=1
            )
            # One successor job per attachment we recognise.
            return [
                {"attachment_id": attachment.id}
                for attachment in mail.attachment_ids
                if attachment.name.lower().endswith((".csv", ".xls", ".xlsx"))
            ]

        def _handle_attachment(self, message):
            self.ensure_one()
            attachment = self.env["ir.attachment"].browse(message["attachment_id"])
            codec = tools.codec_for(attachment.name)
            rows = codec.read_rows(io.BytesIO(attachment.raw))
            self._ingest(rows)

The concrete addon depends on ``mail`` and configures the alias; pipeline core does
not. Everything past ``message_new`` is just stages and tools - the same
pieces every other pipeline uses.

If this wiring turns out to repeat across integrations, it is worth lifting the
alias plumbing into a small optional ``pipeline_mail`` mixin. Until then, a few
lines in the addon that owns the mail are clearer than a framework.
