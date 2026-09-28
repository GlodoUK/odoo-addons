import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AutopilotSalePicking(models.Model):
    """Per-(backend, picking) binding: one picking's dispatch note.

    The engine's ASN cron creates this for each eligible picking then calls
    ``_export``; existence is the "already sent" marker. ``_export`` delegates
    the render + place to the dialect's ``_<dialect>_export`` on this model, so
    a dispatch note is the picking binding's own job. ``sent_date`` /
    ``attachment_id`` are audit the dialect fills.
    """

    _name = "autopilot_sale.picking"
    _description = "Sale EDI Dispatch Note Binding"
    _inherit = ["mail.thread"]
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_sale.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    odoo_id = fields.Many2one(
        "stock.picking",
        string="Picking",
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
        "This picking is already bound to this backend.",
    )

    @api.depends("backend_id.name", "odoo_id.name")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = (
                f"{binding.backend_id.name or '?'}/{binding.odoo_id.name or '?'}"
            )

    def _export(self):
        """Send each dispatch note via its dialect's ``_<dialect>_export``
        (a no-op, logged, if the dialect defines none)."""
        for binding in self:
            method = getattr(binding, f"_{binding.backend_id.dialect}_export", None)
            if not method:
                _logger.info(
                    "Sale EDI: dialect %r exports no dispatch note; skipping %s.",
                    binding.backend_id.dialect,
                    binding.display_name,
                )
                continue
            method()
