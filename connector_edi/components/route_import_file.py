import glob
import io
import logging
import os

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component

from ..mixins import MixinJobFromCtx, MixinSafeFormatPath

_logger = logging.getLogger(__name__)


class EdiRouteFileImporterComponent(
    Component,
    MixinSafeFormatPath,
    MixinJobFromCtx,
):
    _name = "edi.route.file.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.file"
    _apply_on = "edi.envelope"

    def _run_file(self, route_id, file):
        if route_id.encoding == "binary":
            args = {"mode": "rb"}
        else:
            args = {"mode": "r", "encoding": route_id.encoding}

        with io.open(file, **args) as f:
            vals = {
                "backend_id": self.backend_record.id,
                "external_id": os.path.basename(file),
                "content_filename": os.path.basename(file),
                "route_id": route_id.id,
                "direction": "in",
            }

            if route_id.encoding != "binary":
                vals.update({"body": f.read()})

            envelope_id = self.env["edi.envelope"].create(vals)

            if route_id.encoding == "binary":
                envelope_id._set_content(f.read(), encoding=False)

            job = self._job_from_ctx()
            if job:
                msg = _(
                    "Job <a href=# data-oe-model=queue.job"
                    " data-oe-id=%(job_id)d>%(job_uuid)s</a> read %(file)s"
                ) % {"job_id": job.id, "job_uuid": job.uuid, "file": file}
            else:
                msg = _("Read file %s") % (file,)

            envelope_id.message_post(body=msg)
            return envelope_id

    def run(self, route_id, **kwargs):
        if not route_id.file_path_in or not route_id.file_path_archive:
            raise UserError(_("Missing file_path_in or file_path_archive"))

        in_path = self._safe_format_path(route_id.file_path_in, route=route_id)
        archive_path = self._safe_format_path(
            route_id.file_path_archive, route=route_id
        )

        files = self._file_glob_scan(
            in_path, archive_path, done_file_mode=route_id.file_path_in_use_done_mode
        )

        if not files:
            return

        envelope_ids = self.env["edi.envelope"]

        with self.env.cr.savepoint():
            for file in files:
                envelope_ids |= self._run_file(route_id, file)

            envelope_ids.action_pending()

    def _file_glob_scan(
        self,
        process_path,
        archive_path,
        done_file_mode=None,
    ):
        result = []

        create_path = not os.path.exists(archive_path)

        for current_file in glob.glob(process_path):
            # TODO: refactor this
            current_done_file = None
            if done_file_mode == "suffix":
                current_done_file = "{}.DONE".format(current_file)

            if current_done_file and not os.path.exists(current_done_file):
                # waiting on current done file
                continue

            if create_path:
                os.makedirs(archive_path, exist_ok=True)
                create_path = False

            # rename file
            basename = os.path.basename(current_file)
            process_file = os.path.join(archive_path, basename)

            try:
                os.rename(current_file, process_file)
                result.append(process_file)

                if current_done_file:
                    os.remove(current_done_file)
            except Exception as exc:
                _logger.exception(
                    "Error while moving file %s to %s: %s",
                    current_file,
                    process_file,
                    exc,
                )

        return result
