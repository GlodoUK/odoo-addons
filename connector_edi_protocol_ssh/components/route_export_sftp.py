import io
import traceback

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_edi.mixins import MixinSafeFormatPath

from ..ssh import SSHClient


class EdiRouteSftpExporterComponent(Component, MixinSafeFormatPath):
    _name = "edi.route.sftp.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.sftp"
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

        with SSHClient(
            route_id.ssh_host,
            route_id.ssh_port,
            username=route_id.ssh_username,
            password=route_id.ssh_password,
        ) as client:

            sftp = client.open_sftp()

            for envelope_id in envelope_ids:
                try:
                    with self.env.cr.savepoint():
                        abs_file_path = self._safe_format_path(
                            route_id.ssh_path_out, route=route_id, record=envelope_id
                        )

                        with sftp.file(abs_file_path, mode="w+b") as f:
                            f.write(envelope_id.body.encode(route_id.encoding))

                        envelope_id.message_post(body=_("Wrote %s") % abs_file_path)
                        envelope_id.action_done()

                except Exception as e:
                    buff = io.StringIO()
                    traceback.print_exc(file=buff)
                    envelope_id.action_error(
                        exc_info=buff.getvalue(),
                        exc_name=e.__class__.__name__,
                        msg=str(e),
                    )

            sftp.close()
