import base64
import io
import logging
import posixpath

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AutopilotSaleOrderFile(models.Model):
    """One inbound order file and the queued job importing it.

    A file is claimed from the backend's connection by the import cron, or
    uploaded by hand (``autopilot_sale.upload.wizard``); either way its bytes
    are kept on the record (``data``) and the dialect reads them through
    :meth:`_open`, so it never cares where the file came from. Its job's
    outcome is kept on the record too (``autopilot_sale.job.mixin``), where a
    sales user can see a failure and retry or cancel it.

    The file's job only *stages*: the dialect splits the file into one
    ``autopilot_sale.order`` binding per order (rows in its ``payload``), and
    the file is done once they exist. Each binding is then its own queued job
    with its own state, so a bad order fails without taking the file with it.
    """

    _name = "autopilot_sale.order.file"
    _inherit = ["autopilot_sale.job.mixin"]
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
    source = fields.Selection(
        [("connection", "Connection"), ("upload", "Upload")],
        default="connection",
        required=True,
        readonly=True,
    )
    path = fields.Char(
        readonly=True,
        help="Where the file was claimed from on the backend's connection. "
        "Empty for an upload.",
    )
    filename = fields.Char(readonly=True)
    data = fields.Binary(
        string="File",
        attachment=True,
        readonly=True,
        copy=False,
        help="The file as imported. Cleared once its import is done and older "
        "than its backend's clean-up period.",
    )

    order_binding_ids = fields.One2many(
        "autopilot_sale.order", "file_id", string="Orders"
    )
    order_count = fields.Integer(compute="_compute_order_count")

    @api.depends("order_binding_ids")
    def _compute_order_count(self):
        for file in self:
            file.order_count = len(file.order_binding_ids)

    @api.depends("backend_id.name", "filename", "path")
    def _compute_display_name(self):
        for file in self:
            name = file.filename or file.path or "?"
            file.display_name = f"{file.backend_id.name or '?'}/{name}"

    def _open(self):
        """A binary handle on the file's content, for the dialect to read:
        ``with file._open() as handle``. Files claimed before content was kept
        on the record are read from the connection instead."""
        self.ensure_one()
        data = self.with_context(bin_size=False).data
        if data:
            return io.BytesIO(base64.b64decode(data))
        if self.path:
            return self.backend_id.connection_id._open(self.path)
        raise UserError(self.env._("%s has no content to import.", self.display_name))

    @api.model
    def _vals_from_connection(self, backend, path):
        """Create values for a file claimed at ``path``, keeping a copy of its
        bytes. The file is already moved aside, so a failed read must not lose
        it: the record is made without the copy and its job reads the path."""
        vals = {
            "backend_id": backend.id,
            "source": "connection",
            "path": path,
            "filename": posixpath.basename(path),
        }
        try:
            with backend.connection_id._open(path) as handle:
                vals["data"] = base64.b64encode(handle.read())
        except Exception:
            _logger.exception(
                "Sale EDI %s: could not copy %s; its job will read it.",
                backend.name,
                path,
            )
        return vals

    def _enqueue(self):
        """Queue this file's import (see ``autopilot_sale.job.mixin``)."""
        self._queue("_import", "order_import_channel")

    def _requeue(self):
        self._enqueue()

    def _import(self):
        """The file job: see :meth:`_stage`."""
        self._run(self._stage)

    def _stage(self):
        """Have the backend's dialect stage this file's orders
        (``_<dialect>_import_order(file)``), then queue each one.

        Runs with ``default_file_id`` in context so any ``autopilot_sale.order``
        the dialect creates is linked back to this file, per Odoo's usual
        ``default_<field>`` convention - which is also how the staged bindings
        are found to queue."""
        self.ensure_one()
        backend = self.backend_id.with_context(default_file_id=self.id)
        method = getattr(backend, f"_{backend.dialect}_import_order", None)
        if not method:
            raise UserError(
                self.env._("Dialect %r does not import orders.", backend.dialect)
            )
        method(self)
        self.order_binding_ids.filtered(
            lambda b: b.state == "pending" and not b.odoo_id
        )._enqueue()

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
