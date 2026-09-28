import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job import identity_exact

_logger = logging.getLogger(__name__)


class AutopilotSaleOrderFile(models.Model):
    """One claimed inbound order file: a business-facing proxy for the queued
    job that imports it.

    The import cron used to delay straight off the backend, discarding the
    :class:`~odoo.addons.queue_job.job.Job` handle ``with_delay`` returns. This
    model IS that job's origin record instead - created first, then delaying
    ``_import`` on itself - so the job's state/error land here via stored
    related fields. That matters because ``queue.job`` itself is only
    readable by the technical Job Queue group; this gives a sales user
    somewhere to see a failed import and pull it out of the queue, without
    widening ``queue.job`` access. ``_import`` does the same
    ``_<dialect>_import_order`` dispatch the backend used to.
    """

    _name = "autopilot_sale.order.file"
    _description = "Sale EDI Order File"
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_sale.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    path = fields.Char(
        required=True,
        readonly=True,
        help="The claimed file's path on the backend's provider, handed to "
        "the dialect's _<dialect>_import_order(path).",
    )

    job_id = fields.Many2one(
        "queue.job",
        readonly=True,
        copy=False,
        ondelete="set null",
        help="The queued job importing this file. queue.job is only "
        "readable by the technical Job Queue group; use the actions here "
        "instead of opening it directly.",
    )
    job_state = fields.Selection(related="job_id.state", store=True, string="Status")
    job_exc_message = fields.Char(
        related="job_id.exc_message", store=True, string="Error"
    )
    job_exc_info = fields.Text(
        related="job_id.exc_info", store=True, string="Error Detail"
    )

    order_binding_ids = fields.One2many(
        "autopilot_sale.order", "file_id", string="Orders"
    )
    order_count = fields.Integer(compute="_compute_order_count")

    @api.depends("order_binding_ids")
    def _compute_order_count(self):
        for file in self:
            file.order_count = len(file.order_binding_ids)

    @api.depends("backend_id.name", "path")
    def _compute_display_name(self):
        for file in self:
            file.display_name = f"{file.backend_id.name or '?'}/{file.path or '?'}"

    def _enqueue(self):
        """Queue this file's import, keeping the resulting job's handle so its
        state/error can be surfaced here."""
        self.ensure_one()
        job = self.with_delay(identity_key=identity_exact)._import()
        self.job_id = job.db_record()

    def _import(self):
        """Dispatch to the backend's dialect, mirroring the getattr dispatch
        every other binding uses (e.g. ``autopilot_sale.picking._export``).

        Runs with ``default_file_id`` in context so any ``autopilot_sale.order``
        the dialect creates (via plain ``create({...})``, no dialect change
        needed) is linked back to this file automatically, per Odoo's usual
        ``default_<field>`` convention."""
        self.ensure_one()
        backend = self.backend_id.with_context(default_file_id=self.id)
        method = getattr(backend, f"_{backend.dialect}_import_order", None)
        if not method:
            _logger.info(
                "Sale EDI %s: dialect %r imports no orders; skipping %s.",
                backend.name,
                backend.dialect,
                self.path,
            )
            return
        return method(self.path)

    def action_view_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Orders"),
            "res_model": "autopilot_sale.order",
            "view_mode": "list,form",
            "domain": [("file_id", "=", self.id)],
            "context": {"default_file_id": self.id},
        }

    def action_requeue(self):
        for file in self:
            if not file.job_id:
                raise UserError(self.env._("%s has no queued job.", file.display_name))
            file.job_id.sudo().requeue()

    def action_remove_from_queue(self):
        for file in self:
            if not file.job_id:
                raise UserError(self.env._("%s has no queued job.", file.display_name))
            file.job_id.sudo().button_cancelled()
