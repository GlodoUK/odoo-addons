import io
import traceback

import pycurl

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_edi.mixins import MixinSafeFormatPath

from .. import ftp


class EdiRouteFtpExporterComponent(Component, MixinSafeFormatPath):
    _name = "edi.route.ftp.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.ftp"
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

        with ftp.Client(
            route_id._get_ftp_url(),
            route_id.ftp_username,
            route_id.ftp_password,
            use_ssl=route_id._get_ftp_use_ssl(),
        ) as conn:
            for envelope_id in envelope_ids:
                try:
                    with self.env.cr.savepoint():
                        file = self._safe_format_path(
                            route_id.ftp_path_out, route=route_id, record=envelope_id
                        )

                        conn.upload(
                            io.BytesIO(envelope_id.body.encode(route_id.encoding)), file
                        )
                        envelope_id.message_post(body=_("Wrote %s") % file)
                        envelope_id.action_done()

                except pycurl.error as e:
                    buff = io.StringIO()
                    traceback.print_exc(file=buff)
                    envelope_id.action_error(
                        exc_info=buff.getvalue(),
                        exc_name=e.__class__.__name__,
                        msg=str(e),
                    )
