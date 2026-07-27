import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AutopilotSaleOrder(models.Model):
    """Per-(backend, sale order) binding: plain storage for the external
    references of one imported order, and the home of the acknowledgement.

    The engine creates none of this - the dialect does, during import - but the
    acknowledgement lives here (not on the backend) because it is per-order: the
    binding already knows its ``backend_id`` (hence the provider and ack path via
    ``backend_id._place``). ``_acknowledge`` just delegates to the dialect's
    ``_<dialect>_acknowledge`` on this model. Generic references live in
    ``external_values`` (a ``fields.Serialized`` catch-all); a bridge adds a
    typed column by ``_inherit`` for anything it lists/searches on.
    """

    _name = "autopilot_sale.order"
    _description = "Sale EDI Order Binding"
    _inherit = ["mail.thread"]
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_sale.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    odoo_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    line_ids = fields.One2many(
        "autopilot_sale.order.line", "order_binding_id", string="Lines"
    )

    external_ref = fields.Char(
        string="External Reference",
        index=True,
        help="The trading partner's identifier for this order.",
    )
    external_values = fields.Serialized(
        help="Dialect-specific captured values that have no dedicated column.",
    )

    _unique_binding = models.Constraint(
        "unique(backend_id, odoo_id)",
        "This order is already bound to this backend.",
    )

    @api.depends("backend_id.name", "odoo_id.name")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = (
                f"{binding.backend_id.name or '?'}/{binding.odoo_id.name or '?'}"
            )

    def _acknowledge(self):
        """Acknowledge each order via its dialect's ``_<dialect>_acknowledge``
        (a no-op, logged, for a dialect that does not acknowledge - e.g. a pure
        importer). The dialect renders and places the file, reaching the ack
        path through ``self.backend_id._place(backend.ack_export_path, ...)``."""
        for binding in self:
            method = getattr(
                binding, f"_{binding.backend_id.dialect}_acknowledge", None
            )
            if not method:
                _logger.info(
                    "Sale EDI: dialect %r does not acknowledge; skipping %s.",
                    binding.backend_id.dialect,
                    binding.display_name,
                )
                continue
            method()
