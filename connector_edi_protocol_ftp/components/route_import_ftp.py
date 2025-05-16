import fnmatch
import io
import os

from odoo.addons.component.core import Component

from .. import ftp


class EdiRouteFtpImporterComponent(Component):
    _name = "edi.route.ftp.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.ftp"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        with ftp.Client(
            route_id._get_ftp_url(),
            route_id.ftp_username,
            route_id.ftp_password,
            use_ssl=route_id._get_ftp_use_ssl(),
        ) as conn:
            dirname = os.path.dirname(route_id.ftp_path_in)
            pattern = route_id.ftp_path_in
            if route_id.ftp_list_method == "mlsd":
                files = conn.mlsd(dirname)
            elif route_id.ftp_list_method == "list":
                files = conn.list(dirname)
            for file, info in files:
                if info and info.get("type", "file") != "file":
                    continue
                if not fnmatch.fnmatch(file, pattern):
                    continue

                path = os.path.join(dirname, file)
                buff = io.BytesIO()
                conn.download(os.path.join(dirname, file), buff)
                with self.env.cr.savepoint():
                    envelope_id = self.env["edi.envelope"].create(
                        {
                            "backend_id": self.backend_record.id,
                            "external_id": os.path.basename(file),
                            "body": buff.getvalue().decode(route_id.encoding),
                            "route_id": route_id.id,
                            "direction": "in",
                        }
                    )
                    envelope_id.action_pending()
                    if route_id.ftp_delete:
                        conn.delete(path)
