from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    intrastat_code_id = fields.Many2one(
        "account.intrastat.code",
        string="HS Code",
        related="product_id.intrastat_code_id",
    )
    intrastat_country_id = fields.Many2one(
        "res.country",
        string="Country of Manufacture",
        related="product_id.intrastat_origin_country_id",
    )
    weight = fields.Float(
        string="Weight",
        related="product_id.weight",
    )
    price_unit = fields.Float(
        string="Unit Price",
        related="sale_line_id.price_unit",
    )


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    intrastat_code_id = fields.Many2one(
        "account.intrastat.code",
        string="HS Code",
        related="product_id.intrastat_code_id",
    )
    intrastat_country_id = fields.Many2one(
        "res.country",
        string="Country of Manufacture",
        related="product_id.intrastat_origin_country_id",
    )
    weight = fields.Float(
        string="Weight",
        related="product_id.weight",
    )
    price_unit = fields.Float(
        string="Unit Price",
        related="move_id.sale_line_id.price_unit",
    )
