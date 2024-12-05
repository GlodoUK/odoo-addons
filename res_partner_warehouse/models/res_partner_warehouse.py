from ast import literal_eval

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartnerWarehouse(models.Model):
    _name = "res.partner.warehouse"
    _description = "Partner Virtual Warehouse"
    _check_company_auto = True

    name = fields.Char(required=True)
    code = fields.Char()
    partner_id = fields.Many2one("res.partner", index=True, required=True)
    partner_address_id = fields.Many2one(
        "res.partner",
        index=True,
        string="Address",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        readonly=True,
        required=True,
        help="The company is automatically set from your user preferences.",
    )

    @api.depends("name", "code")
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.partner_id.display_name} - {record.code}] {name}"
            else:
                name = f"[{record.partner_id.display_name}] {name}"
            res.append((record.id, name))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )

    def action_view_quants(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "res_partner_warehouse.actions_res_partner_warehouse_quant_act_window"
        )
        action["domain"] = [("warehouse_id", "=", self.id)]
        action["context"] = literal_eval(action.get("context"))
        action["context"]["default_warehouse_id"] = self.id

        return action

    def _get_available_quantity(self, product_id, uom_id=False):
        self.ensure_one()
        product_id.ensure_one()

        return self.env["res.partner.warehouse.quant"]._get_available_quantity(
            self, product_id, uom_id
        )

    _sql_constraints = [
        (
            "warehouse_name_uniq",
            "unique(name, company_id)",
            "The name of the warehouse must be unique per company!",
        ),
        (
            "warehouse_code_uniq",
            "unique(code, company_id)",
            "The short name of the warehouse must be unique per company!",
        ),
    ]


class ResPartnerWarehouseStockQuant(models.Model):
    _name = "res.partner.warehouse.quant"
    _description = "Partner Virtual Warehouse Quant"

    @api.model
    def _get_available_quantities(self, product_ids, warehouse_ids=False):
        domain = [("product_id", "in", product_ids.ids)]

        if warehouse_ids:
            domain += [("warehouse_id", "in", warehouse_ids.ids)]

        res = {}

        for quant_id in self.search(domain):
            product_id = quant_id.product_id
            if product_id.id not in res:
                res[product_id.id] = []

            res[product_id.id].append(
                quant_id.uom_id._compute_quantity(
                    quant_id.quantity,
                    product_id.uom_id,
                )
            )

        return {k: sum(v) for k, v in res.items()}

    @api.model
    def _get_available_quantity(self, warehouse_id, product_id, uom_id=False):
        warehouse_id.ensure_one()
        product_id.ensure_one()

        if not uom_id:
            uom_id = product_id.uom_id

        quant_ids = self.search(
            [
                ("warehouse_id", "=", warehouse_id.id),
                ("product_id", "=", product_id.id),
            ]
        )

        res = []

        for quant_id in quant_ids:
            res.append(
                quant_id.uom_id._compute_quantity(
                    quant_id.quantity,
                    uom_id,
                )
            )

        return sum(res)

    @tools.ormcache()
    def _get_default_uom_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref("uom.product_uom_unit")

    partner_id = fields.Many2one(
        related="warehouse_id.partner_id", index=True, store=True
    )
    warehouse_id = fields.Many2one("res.partner.warehouse", required=True, index=True)
    company_id = fields.Many2one(
        related="warehouse_id.company_id", string="Company", store=True, readonly=True
    )
    product_id = fields.Many2one("product.product", required=True, index=True)
    uom_id = fields.Many2one("uom.uom", required=True, default=_get_default_uom_id)
    quantity = fields.Float(
        required=True,
        string="Quantity on Hand",
    )
    quantity_date = fields.Date()
    forecast_quantity = fields.Float()
    forecast_date = fields.Date()

    _sql_constraints = [
        (
            "warehouse_product_uniq",
            "unique(warehouse_id, product_id)",
            "Product and warehouse must be unique!",
        ),
    ]

    @api.constrains("uom_id", "product_id.uom_id", "product_id.uom_po_id")
    def _check_uom(self):
        if any(
            (
                quant.uom_id
                and quant.product_id.uom_id
                and quant.uom_id.category_id != quant.product_id.uom_id.category_id
            )
            or (
                quant.uom_id
                and quant.product_id.uom_po_id
                and quant.uom_id.category_id != quant.product_id.uom_po_id.category_id
            )
            for quant in self
        ):
            raise ValidationError(
                _(
                    "The product and quant Unit of Measure must be in the same"
                    " category."
                )
            )
