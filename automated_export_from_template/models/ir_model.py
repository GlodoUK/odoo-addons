import base64
import csv
import io
import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _get_export_template(self, export_template: str | int):
        if isinstance(export_template, int):
            export_id = self.env["ir.exports"].browse(export_template)
            if not export_id:
                raise UserError(
                    self.env._(
                        "No saved export template with ID %(id)d found for %(model)s.",
                        id=export_template,
                        model=self._name,
                    )
                )
            return export_id
        export_id = self.env["ir.exports"].search(
            [("name", "=", export_template), ("resource", "=", self._name)], limit=1
        )
        if not export_id:
            raise UserError(
                self.env._(
                    "No saved export template named '%(name)s' found for %(model)s.",
                    name=export_template,
                    model=self._name,
                )
            )
        return export_id

    def _get_export_field_info(self, field_path):
        parts = field_path.split("/")
        model = self
        labels = []
        field_type = "char"
        for index, part in enumerate(parts):
            field_data = model.fields_get(
                [part], attributes=["string", "type", "relation"]
            ).get(part)
            if not field_data:
                labels.append(part)
                continue
            labels.append(field_data["string"])
            field_type = field_data["type"]
            if index < len(parts) - 1 and field_data.get("relation"):
                model = self.env[field_data["relation"]]
        return "/".join(labels), field_type

    def _export_from_template(self, export_template):
        field_names = [line.name for line in export_template.export_fields]

        export_data = self.export_data(field_names).get("datas", [])

        headers = []
        for field_name in field_names:
            label, _field_type = self._get_export_field_info(field_name)
            headers.append(label)

        return self._generate_csv_export(headers, export_data)

    def _generate_csv_export(self, headers, export_data):
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in export_data:
            writer.writerow(row)
        return output.getvalue().encode("utf-8")

    def _cron_export_and_email(
        self,
        export_template,
        email_to,
        domain=None,
        email_subject=None,
    ):
        export_template_id = self._get_export_template(export_template)
        export_name = export_template_id.name

        if not domain:
            domain = []

        records = self.search(domain)
        if not records:
            _logger.info(
                "Auto Export '%r': no records matched domain %r, skipping.",
                export_name,
                domain,
            )
            return

        export_data = records._export_from_template(export_template_id)

        attachment = self.env["ir.attachment"].create(
            {
                "name": f"{export_name}.csv",
                "type": "binary",
                "datas": base64.b64encode(export_data),
                "mimetype": "text/csv",
            }
        )

        self.env["mail.mail"].create(
            {
                "subject": email_subject or f"{export_template_id.name}",
                "body_html": self.env._(
                    "<p>Please find attached the '%(name)s' export "
                    "(%(count)s records).</p>",
                    name=export_template_id.name,
                    count=len(records),
                ),
                "email_to": email_to,
                "attachment_ids": [(6, 0, [attachment.id])],
            }
        ).send()
