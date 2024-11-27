import io

from odoo import _

from odoo.addons.component.core import Component

from ..mixins import MixinJobFromCtx, MixinSafeFormatPath


class EdiRouteFileExporterComponent(Component, MixinSafeFormatPath, MixinJobFromCtx):
    _name = "edi.route.file.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.file"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        envelope_ids = kwargs.get("envelope_ids", None)
        if not envelope_ids:
            envelope_ids = self.env["edi.envelope"].search(
                [
                    ("route_id", "=", route_id.id),
                    ("direction", "=", "out"),
                    ("state", "=", "pending"),
                ]
            )

        for envelope_id in envelope_ids:
            try:
                file = self._safe_format_path(
                    route_id.file_path_out, route=route_id, record=envelope_id
                )

                self._run(route_id, envelope_id, file)
            except (FileNotFoundError, FileExistsError, PermissionError, OSError) as e:
                envelope_id.action_error(str(e))

    def _run(self, route_id, envelope_id, file):
        with io.open(file, "w", encoding=route_id.encoding) as f:
            f.write(envelope_id.body)

        if route_id.file_path_out_use_done_mode == "suffix":
            # TODO: refactor this
            done_file = "{}.DONE".format(file)
            io.open(done_file, "w", encoding=route_id.encoding).close()

        job = self._job_from_ctx()
        if job:
            msg = _(
                "Job <a href=# data-oe-model=queue.job data-oe-id=%d>%s</a>" " wrote %s"
            ) % (job.id, job.uuid, file)
        else:
            msg = _("Wrote file %s") % (file,)

        envelope_id.action_done(msg)
