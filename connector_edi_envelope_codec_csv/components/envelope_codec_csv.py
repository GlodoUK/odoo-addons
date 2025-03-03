import csv
import io

from odoo.addons.component.core import Component


class CodecCSVComponent(Component):
    _name = "edi.envelope.codec.csv"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.csv"
    _apply_on = "edi.envelope"

    def open(self, envelope_id, **kwargs):
        record = envelope_id
        backend = self.backend_record
        route = envelope_id.route_id

        with self.env.cr.savepoint():
            # split the inbound envelopes into multiple messages using the a given field in the file
            reader = csv.reader(
                io.StringIO(record.body),
                quoting=int(route.codec_csv_quoting),  # Odoo stores 0 as False
                delimiter=route.codec_csv_delimiter or ',',
            )
            unique = {}

            for line in reader:
                # use a given field index to split this file
                ref = line[route.codec_csv_field]
                if ref not in unique:
                    unique[ref] = []
                unique[ref].append(line)

            for key, lines in unique.items():
                if len(lines) <= 0:
                    continue

                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

                for line in lines:
                    writer.writerow(line)

                message_id = self.env['edi.message'].create({
                    'envelope_id': record.id,
                    "envelope_route_id": record.route_id.id,
                    'backend_id': backend.id,
                    'direction': 'in',
                    'body': output.getvalue(),
                    'external_id': key or "blank",
                })
                message_id.action_pending()

    def enclose(self, message_ids, **kwargs):
        with self.env.cr.savepoint():
            for message_id in message_ids:
                envelope_id = self.env["edi.envelope"].create(
                    {
                        "route_id": message_id.envelope_route_id.id,
                        "body": message_id.body,
                        "external_id": message_id.external_id or "blank",
                        "direction": "out",
                        "backend_id": self.backend_record.id,
                    }
                )

                message_id.envelope_id = envelope_id
                envelope_id.action_pending()
