import fnmatch
import os

from odoo.addons.component.core import Component

from ..ssh import SSHClient


class EdiRouteSftpImporterComponent(Component):
    _name = "edi.route.sftp.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.sftp"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        with SSHClient(
            route_id.ssh_host,
            route_id.ssh_port,
            username=route_id.ssh_username,
            password=route_id.ssh_password,
        ) as client:
            sftp = client.open_sftp()

            dirname = os.path.dirname(route_id.ssh_path_in)
            pattern = route_id.ssh_path_in

            for file in sftp.listdir(dirname):
                abs_file_path = os.path.join(dirname, file)

                if not fnmatch.fnmatch(abs_file_path, pattern):
                    continue

                with self.env.cr.savepoint():
                    with sftp.open(abs_file_path) as f:
                        envelope_id = self.env["edi.envelope"].create(
                            {
                                "backend_id": self.backend_record.id,
                                "external_id": file,
                                "body": f.read().decode(route_id.encoding),
                                "route_id": route_id.id,
                                "direction": "in",
                            }
                        )

                    envelope_id.action_pending()
                    if route_id.ssh_delete:
                        sftp.unlink(abs_file_path)

            sftp.close()
