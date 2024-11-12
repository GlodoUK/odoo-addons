import mimetypes
import re
import unicodedata

from odoo import api, fields, models


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    if not value:
        return ""
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = str(re.sub(r"[^\w\s-]", "-", value).strip())
    return re.sub(r"[-\s]+", "-", value)


class StockPickingTrackingSignature(models.Model):
    _name = "stock.picking.tracking.signature"
    _description = "Stock picking Delivery Tracking Signature"

    picking_id = fields.Many2one("stock.picking", required=True, index=True)
    date_signed = fields.Datetime(required=False)
    attachment = fields.Binary(attachment=True)
    attachment_name = fields.Char(compute="_compute_attachment_name")
    signee = fields.Char()
    external_id = fields.Char(index=True)

    @api.depends("attachment")
    def _compute_attachment_name(self):
        if not self.ids:
            return

        self.env.cr.execute(
            """
            SELECT
                mimetype, res_id
            FROM ir_attachment
            WHERE
                res_id in %s
                AND
                res_model = %s
            """,
            [
                tuple(self.ids),
                self._name,
            ],
        )

        res_dict = {row[1]: row[0] for row in self.env.cr.fetchall()}

        for rec in self:
            if not res_dict.get(rec.id):
                rec.attachment_name = False
                continue

            ext = mimetypes.guess_extension(res_dict.get(rec.id))
            if not ext:
                ext = ".bin"

            rec.attachment_name = "{}_{}{}".format(
                slugify(rec.picking_id.display_name),
                rec.id,
                ext,
            )


class StockPickingTrackingEvent(models.Model):
    _name = "stock.picking.tracking.history"
    _description = "Stock Picking Delivery Tracking History"
    _order = "date_event desc"

    picking_id = fields.Many2one("stock.picking", required=True, index=True)
    date_event = fields.Datetime(required=False)
    description = fields.Text()
    external_id = fields.Char(index=True)
