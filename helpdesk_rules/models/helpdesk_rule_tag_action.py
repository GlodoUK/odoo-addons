from odoo import fields, models


class HelpdeskRuleTagAction(models.Model):
    _name = "helpdesk.rule.tag.action"
    _description = "Helpdesk Rule Tag Action"
    _order = "sequence"

    sequence = fields.Integer()
    tag_id = fields.Many2one("helpdesk.tag")
    action = fields.Selection(
        [("add", "Add"), ("remove", "Remove"), ("clear", "Clear")],
        default="add",
        required=True,
    )
    rule_id = fields.Many2one("helpdesk.rule", required=True)
