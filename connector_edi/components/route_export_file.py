import io
import traceback

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
            except OSError as e:
                buff = io.StringIO()
                traceback.print_exc(file=buff)
                envelope_id.action_error(
                    exc_info=buff.getvalue(),
                    exc_name=e.__class__.__name__,
                    msg=str(e),
                )

    def _run(self, route_id, envelope_id, file):
        args = {"mode": "w", "encoding": route_id.encoding}

        with io.open(file, **args) as f:
            f.write(envelope_id.body)

        if route_id.file_path_out_use_done_mode == "suffix":
            # TODO: refactor this
            done_file = "{}.DONE".format(file)
            io.open(done_file, "wb").close()

        job = self._job_from_ctx()
        if job:
            msg = _(
                "Job <a href=# data-oe-model=queue.job"
                " data-oe-id=%(job_id)d>%(job_uuid)s</a> wrote %(file)s"
            ) % {
                "job_id": job.id,
                "job_uuid": job.uuid,
                "file": file,
            }
        else:
            msg = _("Wrote file %(file)s") % {"file": file}

        envelope_id.action_done(msg)
