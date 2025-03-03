import requests

from odoo.addons.component.core import Component
from odoo.addons.connector.exception import RetryableJobError


class CodecEDINationComponent(Component):
    _name = "edi.envelope.codec.edination"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.edination"
    _apply_on = "edi.envelope"

    def _get_edination_request_headers(self, apikey):
        return {
            "Ocp-Apim-Subscription-Key": apikey,
        }

    def _post_to_edination_api(self, path=None, apikey=None, files=None):
        return requests.post(
            path, headers=self._get_edination_request_headers(apikey), files=None,
        )

    def open(self, envelope_id, **kwargs):
        record = envelope_id
        backend = self.backend_record
        route = record.route_id

        response = self._post_to_edination_api(
            path=route._get_codec_edination_open_url(),
            apikey=route.codec_edination_apikey,
            files={record.external_id: (record.external_id, record.body)},
        )

        if response.status_code == 200:
            message_id = self.env["edi.message"].create(
                {
                    "envelope_id": record.id,
                    "envelope_route_id": record.route_id.id,
                    "backend_id": backend.id,
                    "direction": "in",
                    "body": response.text,
                    "external_id": record.external_id or "blank",
                }
            )
            message_id.action_pending()
            return

        if response.status_code == 400:
            record.action_error(
                "Failed to open envelope using EDINation API: {}".format(response.text)
            )
            return

        raise RetryableJobError(response.text)

    def enclose(self, message_ids, **kwargs):
        with self.env.cr.savepoint():
            for message_id in message_ids:
                route = message_id.envelope_route_id

                response = self._post_to_edination_api(
                    path=route._get_codec_edination_enclose_url(),
                    apikey=route.codec_edination_apikey,
                    files={message_id.id: (message_id.id, message_id.body)},
                )

                if response.status_code == 200:
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
                    return

                if response.status_code == 400:
                    message_id.action_error(
                        "Failed to open envelope using EDINation API: %s"
                        % (response.text,)
                    )
                    return

                raise RetryableJobError(response.text)
