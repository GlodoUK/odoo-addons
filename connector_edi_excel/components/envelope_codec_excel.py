import base64
import io

import pandas as pd

from odoo.addons.component.core import Component


class CodecExcelComponent(Component):
    _name = "edi.envelope.codec.excel"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.excel_file"
    _apply_on = "edi.envelope"

    def open(self, envelope_id, **kwargs):
        with self.env.cr.savepoint():
            attachments = self.env["ir.attachment"].search(
                [("res_model", "=", envelope_id._name), ("res_id", "=", envelope_id.id)]
            )
            for attachment in attachments:
                xls = pd.ExcelFile(io.BytesIO(base64.b64decode(attachment.datas)))
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    m = self.env["edi.message"].create(
                        {
                            "external_id": envelope_id.external_id,
                            "body": df.to_csv(index=False),
                            "direction": "in",
                            "envelope_id": envelope_id.id,
                            "backend_id": self.backend_record.id,
                        }
                    )
                    m.action_pending()
