# noqa

attachment_ids = env["ir.attachment"].search(
    [("res_model", "=", record._name), ("res_id", "=", record.id),]
)

for attachment_id in attachment_ids.filtered(lambda a: a.mimetype == "text/csv"):
    # assumes 1 csv per order
    message_id = env["edi.message"].create(
        {
            "envelope_id": record.id,
            "envelope_route_id": record.route_id.id,
            "backend_id": backend.id,
            "direction": "in",
            "body": base64.b64decode(attachment_id.datas).decode("utf-8"),
            "external_id": "{}/{}".format(record.external_id, attachment_id.name),
        }
    )
    message_id.action_pending()
