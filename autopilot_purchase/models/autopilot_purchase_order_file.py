import base64
import posixpath

from odoo import api, fields, models
from odoo.exceptions import UserError


class AutopilotPurchaseOrderFile(models.Model):
    """One outbound file of one or more orders, and the job sending it.

    The dialect renders it in the job, not when it is made. So a Retry after
    fixing an order sends the order as it is now.
    """

    _name = "autopilot_purchase.order.file"
    _inherit = ["autopilot_purchase.job.mixin"]
    _description = "Purchase EDI Order File"
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_purchase.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    order_binding_ids = fields.Many2many(
        "autopilot_purchase.order",
        "autopilot_purchase_order_file_rel",
        "file_id",
        "order_binding_id",
        string="Orders",
        required=True,
        readonly=True,
    )
    purchase_order_ids = fields.Many2many(
        "purchase.order",
        string="Purchase Orders",
        compute="_compute_purchase_order_ids",
    )
    path = fields.Char(
        readonly=True, copy=False, help="Where the file was written on the connection."
    )
    filename = fields.Char(readonly=True, copy=False)
    data = fields.Binary(string="File", attachment=True, readonly=True, copy=False)
    sent_date = fields.Datetime(string="Sent On", readonly=True, copy=False)

    @api.depends("order_binding_ids.odoo_id")
    def _compute_purchase_order_ids(self):
        for file in self:
            file.purchase_order_ids = file.order_binding_ids.odoo_id

    @api.depends("backend_id.name", "filename")
    def _compute_display_name(self):
        for file in self:
            name = file.filename or str(file.id or "?")
            file.display_name = f"{file.backend_id.name or '?'}/{name}"

    def _enqueue(self):
        self._queue("_export", "order_export_channel")

    def _requeue(self):
        self._enqueue()

    def _export(self):
        self._run(self._write)

    def _write(self):
        self.ensure_one()
        backend = self.backend_id
        method = getattr(self, f"_{backend.dialect}_render", None)
        if not method:
            raise UserError(
                self.env._("Dialect %r does not export orders.", backend.dialect)
            )
        raw = method()
        with backend._place(backend.order_export_path, record=self) as (
            handle,
            target,
        ):
            handle.write(raw)
        filename = posixpath.basename(target)
        self.write(
            {
                "path": target,
                "filename": filename,
                "data": base64.b64encode(raw),
                "sent_date": fields.Datetime.now(),
            }
        )
        for order in self.purchase_order_ids:
            order.message_post(
                body=self.env._(
                    "Order sent to %(backend)s as %(file)s.",
                    backend=backend.name,
                    file=filename,
                )
            )
