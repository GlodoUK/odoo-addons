import logging

from odoo import api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class AutopilotSaleInvoice(models.Model):
    """An invoice sent to the partner. Its existence is the sent marker; the
    dialect fills ``sent_date`` and ``attachment_id``."""

    _name = "autopilot_sale.invoice"
    _description = "Sale EDI Invoice Binding"
    _inherit = ["mail.thread"]
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_sale.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    odoo_id = fields.Many2one(
        "account.move",
        string="Invoice",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    external_values = fields.Serialized()
    sent_date = fields.Datetime(string="Sent On", readonly=True, copy=False)
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Sent File",
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    _unique_binding = models.Constraint(
        "unique(backend_id, odoo_id)",
        "This invoice is already bound to this backend.",
    )

    @api.depends("backend_id.name", "odoo_id.name")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = (
                f"{binding.backend_id.name or '?'}/{binding.odoo_id.name or '?'}"
            )

    def _export(self):
        for binding in self:
            method = getattr(binding, f"_{binding.backend_id.dialect}_export", None)
            if not method:
                _logger.info(
                    "Sale EDI: dialect %r exports no invoice; skipping %s.",
                    binding.backend_id.dialect,
                    binding.display_name,
                )
                continue
            method()

    @api.model
    def _autopilot_activity_query(self):
        return self.env["autopilot.activity"]._source_select(
            self,
            backend="backend_id",
            company="company_id",
            state=SQL("CASE WHEN src.sent_date IS NULL THEN 'to_send' ELSE 'sent' END"),
            status={"to_send": "pending", "sent": "done"},
        )

    def _autopilot_activity_state_labels(self):
        return {"to_send": self.env._("To Send"), "sent": self.env._("Sent")}
