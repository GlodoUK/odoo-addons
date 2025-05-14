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
            attachment_ids = self.env["ir.attachment"].search(
                [
                    ("res_id", "=", envelope_id.id),
                    ("res_model", "=", envelope_id._name),
                ]
            )

            for attachment in attachment_ids:
                file_data = io.BytesIO(base64.b64decode(attachment.datas))

                xls = None

                if (
                    attachment.mimetype
                    == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # noqa: E501
                ):
                    xls = pd.ExcelFile(file_data, engine="openpyxl")
                elif (
                    attachment.mimetype
                    == "application/vnd.ms-excel.sheet.binary.macroEnabled.12"
                ):
                    xls = pd.ExcelFile(file_data, engine="pyxlsb")
                elif attachment.mimetype == "application/vnd.ms-excel":
                    xls = pd.ExcelFile(file_data, engine="xlrd")

                if not xls:
                    # Skip unsupported file types
                    continue

                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)

                    message_id = self.env["edi.message"].create(
                        {
                            "backend_id": self.backend_record.id,
                            "envelope_id": envelope_id.id,
                            "body": df.to_csv(index=False),
                            "direction": "in",
                            "external_id": envelope_id.external_id,
                        }
                    )

                    message_id.action_pending()
