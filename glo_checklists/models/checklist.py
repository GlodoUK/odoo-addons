import ast
import re

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

DANGEROUS_MODELS = [
    "res.bank",
    "res.company",
    "res.currency",
    "res.lang",
    "report.layout",
    "report.paperformat",
    "res.config.settings",
    "glo_checklist.template",
    "glo_checklist.template.line",
    "glo_checklist.item",
]


class ChecklistTemplate(models.Model):
    _name = "glo_checklist.template"
    _description = "Checklist Template"
    _order = "sequence, name"

    name = fields.Char(required=True)
    res_model_id = fields.Many2one(
        "ir.model",
        string="Apply on Model",
        help="Which model should this checklist be applied to?",
        required=True,
        ondelete="cascade",
        domain=lambda r: [
            ("model", "not in", DANGEROUS_MODELS),
            "!",
            ("model", "=ilike", "ir.%"),
            "!",
            ("model", "=ilike", "base%"),
        ],
    )
    res_model = fields.Char(
        related="res_model_id.model", store=True, index=True, readonly=True
    )
    auto_add_view = fields.Selection(
        [
            ("all", "All Forms"),
            ("specific", "Specific Forms"),
            ("no", "No"),
        ],
        string="Auto-add to Views",
        default="all",
        required=True,
        help="""Automatically add the checklist to all forms or specific forms.
        If you choose 'No', forms will need to be manually modified to include
        the checklist.""",
    )
    view_ids = fields.Many2many(
        "ir.ui.view", string="Apply to Views", help="Leave blank for all form views"
    )
    line_ids = fields.One2many(
        "glo_checklist.template.line", "checklist_template_id", string="Checklist Tasks"
    )
    active = fields.Boolean(default=True)
    domain = fields.Char(
        help="Optional domain to apply the checklist to specific records",
        default="[]",
    )
    block_domain = fields.Char(
        help="""Records that enter this domain without first completing the checklist
        will raise and exception""",
        default="[]",
    )
    block_type = fields.Selection(
        [
            ("none", "Never"),
            ("required", "Required Tasks Incomplete"),
            ("full", "Any Task Incomplete"),
        ],
        default="required",
        help="Which tasks must be completed to unblock the record?",
        required=True,
        string="Block Update If...",
    )
    block_portal = fields.Boolean(
        string="Block Portal Users",
        help="Block portal users from updating records until the checklist is complete",
        default=False,
    )
    show_checklist_on_portal = fields.Boolean(
        help="Show the checklist on the portal view of the record",
        default=False,
    )
    sequence = fields.Integer(default=10)

    def action_open_checklist_items(self):
        self.ensure_one()
        return {
            "name": "Checklist Items",
            "type": "ir.actions.act_window",
            "res_model": "glo_checklist.item",
            "view_mode": "tree,form",
            "domain": [("checklist_template_id", "=", self.id)],
        }

    def create(self, vals):
        res = super().create(vals)
        matching_records = self.env[res.res_model].search(ast.literal_eval(res.domain))
        for record in matching_records:
            record.update_checklist_items()
        return res

    def write(self, vals):
        before_matching_records = self.env[self.res_model].search(
            ast.literal_eval(vals.get("domain", "[]"))
        )
        res = super().write(vals)
        matching_records = self.env[res.res_model].search(ast.literal_eval(res.domain))
        no_longer_matching_records = before_matching_records - matching_records
        no_longer_matching_records.with_context(
            skip_checklist_block=True
        ).checklist_item_ids.unlink()
        for record in matching_records:
            record.update_checklist_items()
        return res


class ChecklistTemplateLine(models.Model):
    _name = "glo_checklist.template.line"
    _description = "Checklist Template Line"
    _order = "sequence, name"

    name = fields.Html(required=True)
    description = fields.Text(
        help="Used as a help text for the user completing the task"
    )
    checklist_template_id = fields.Many2one(
        "glo_checklist.template", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    required = fields.Boolean(default=False)
    prevent_uncomplete = fields.Boolean(
        help="If checked, completed tasks cannot be unchecked",
        default=True,
    )


class CheckListItem(models.Model):
    _name = "glo_checklist.item"
    _description = "Checklist Item"
    _order = "sequence asc, id asc"

    _inherit = ["mail.thread"]

    checklist_line_id = fields.Many2one(
        "glo_checklist.template.line", required=True, ondelete="cascade"
    )
    res_id = fields.Integer(string="Record ID", required=True, index=True)
    res_model = fields.Char(
        related="checklist_line_id.checklist_template_id.res_model",
        store=True,
        index=True,
    )
    checklist_template_id = fields.Many2one(
        "glo_checklist.template",
        related="checklist_line_id.checklist_template_id",
        ondelete="cascade",
    )
    name = fields.Html(related="checklist_line_id.name")
    description = fields.Text(related="checklist_line_id.description")
    required = fields.Boolean(related="checklist_line_id.required")
    completed = fields.Boolean(default=False, tracking=True)
    completion_note = fields.Text(tracking=True)
    completed_date = fields.Datetime(readonly=True, tracking=True)
    completed_by = fields.Many2one("res.users", readonly=True, tracking=True)
    prevent_uncomplete = fields.Boolean(
        related="checklist_line_id.prevent_uncomplete", readonly=True
    )
    sequence = fields.Integer(related="checklist_line_id.sequence", store=True)

    def _compute_display_name(self):
        for record in self:
            record.display_name = re.sub(r"<.*?>", "", record.name)

    def write(self, vals):
        res = super().write(vals)
        if "completed" in vals:
            if vals["completed"]:
                self.completed_by = self.env.user.id
                self.completed_date = fields.Datetime.now()
            else:
                self.completed_by = False
                self.completed_date = False
        return res

    def action_checklist_help(self):
        self.ensure_one()
        return {
            "name": "Checklist Help",
            "type": "ir.actions.act_window",
            "res_model": "glo_checklist.help_popup",
            "view_mode": "form",
            "view_id": self.env.ref("glo_checklists.view_checklist_help_popup_form").id,
            "context": {"default_description": self.description},
            "target": "new",
        }

    def action_complete(self):
        self.write({"completed": True})

    def action_uncomplete(self):
        if self.prevent_uncomplete and not self.env.user.has_group(
            "glo_checklists.group_checklist_manager"
        ):
            raise ValidationError(_("This task cannot be uncompleted!"))
        self.write({"completed": False})


class ChecklistBase(models.AbstractModel):
    _inherit = "base"

    checklist_item_ids = fields.One2many(
        "glo_checklist.item",
        "res_id",
        copy=False,
        domain=lambda self: [("res_model", "=", self._name)],
    )

    def _compute_related_record(self):
        for record in self:
            record.related_record = self.env[self._name].browse(record.id)

    def action_open_related_record(self):
        self.ensure_one()
        return {
            "name": "Related Record",
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
        }

    def get_checklist_template(self):
        return self.env["glo_checklist.template"].search(
            [("res_model", "=", self._name)], limit=1
        )

    def check_checklist_fully_completed(self):
        checklist_id = self.get_checklist_template()
        if not checklist_id and not self.checklist_item_ids:
            return
        for record in self:
            if checklist_id and not record.checklist_item_ids:
                record.update_checklist_items()
            if any(not item.completed for item in record.checklist_item_ids):
                raise ValidationError(_("Checklist is not completed!"))

    def check_checklist_required_completed(self):
        checklist_id = self.get_checklist_template()
        if not checklist_id and not self.checklist_item_ids:
            return
        for record in self:
            if checklist_id and not record.checklist_item_ids:
                record.update_checklist_items()
            if any(
                item.required and not item.completed
                for item in record.checklist_item_ids
            ):
                raise ValidationError(
                    _("Please complete all required checklist items!")
                )

    def update_checklist_items(self):
        for record in self:
            checklists = self.env["glo_checklist.template"].search(
                [("res_model", "=", record._name)]
            )
            for checklist in checklists:
                if record.filtered_domain(ast.literal_eval(checklist.domain)):
                    checklist_items = record.checklist_item_ids
                    for line in checklist.line_ids:
                        if line.id not in checklist_items.checklist_line_id.ids:
                            item = self.env["glo_checklist.item"].create(
                                {"checklist_line_id": line.id, "res_id": record.id}
                            )
                            checklist_items += item
                    record.checklist_item_ids = checklist_items
                    break
        self.invalidate_recordset(["checklist_item_ids"])
        return self

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        if not self._name.startswith("ir.") or self._name not in DANGEROUS_MODELS:
            # Safety catch to prevent modifying dangerous models
            res = res.with_context(prevent_checklist_loop=True).update_checklist_items()
        return res

    def write(self, vals):
        if self._name.startswith("ir.") or self._name in DANGEROUS_MODELS:
            # Safety catch to prevent modifying dangerous models
            return super().write(vals)

        checklist = self.get_checklist_template()
        if not checklist:
            return super().write(vals)

        # Note records that do not already match the block domain
        block_domain_check = None
        if checklist and checklist.block_domain and checklist.block_type != "none":
            block_domain_check = self.filtered_domain(
                ast.literal_eval(checklist.domain)
            )
            block_domain_check -= self.filtered_domain(
                ast.literal_eval(checklist.block_domain)
            )

        res = super().write(vals)
        if not self.env.context.get("prevent_checklist_loop", False):
            self.with_context(prevent_checklist_loop=True).update_checklist_items()

        # Check if the block domain has been met
        if (
            checklist
            and checklist.block_domain
            and block_domain_check
            and not self.env.context.get("skip_checklist_block", False)
            and checklist.block_type != "none"
        ):
            block_domain_confirm = block_domain_check.filtered_domain(
                ast.literal_eval(checklist.block_domain)
            )
            if block_domain_confirm:
                for record in block_domain_confirm:
                    if checklist.block_type == "required":
                        record.check_checklist_required_completed()
                    else:
                        record.check_checklist_fully_completed()
        return res

    def _get_injected_view_contents(self):
        return """<field name="checklist_item_ids">
                <tree create="False" delete="False" editable="bottom"
                    decoration-warning="required and not completed"
                    decoration-muted="not required or completed">
                    <field name="sequence" column_invisible="True"/>
                    <field name="description" column_invisible="True"/>
                    <field name="completed" widget="boolean_toggle" readonly="True"/>
                    <field name="name"/>
                    <button name="action_checklist_help" type="object"
                        title="Help" icon="fa-question"
                        invisible="not description"
                    />
                    <field name="required"/>
                    <field name="prevent_uncomplete"
                        column_invisible="True"/>
                    <field name="completion_note"/>
                    <field name="completed_date"/>
                    <field name="completed_by"/>
                    <button icon="fa-external-link" name="action_details" type="object"
                        title="Details/History"/>
                    <button name="action_complete" type="object" title="Complete"
                        icon="fa-check" invisible="completed" string="Complete"
                        class="btn btn-primary"/>
                    <button name="action_uncomplete" type="object" title="Uncomplete"
                        icon="fa-undo" invisible="not completed or prevent_uncomplete"
                        string="Uncomplete" class="btn btn-secondary"/>
                    <button name="action_uncomplete" type="object"
                        groups="glo_checklists.group_checklist_manager"
                        title="Uncomplete" icon="fa-undo" string="Admin Uncomplete"
                        invisible="not completed or prevent_uncomplete == False"
                        class="btn btn-secondary"/>
                </tree>
            </field>"""

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        checklist = self.get_checklist_template()
        if not checklist:
            return arch, view
        if view_type == "form":
            if checklist.auto_add_view != "no":
                # Skip if the view is not in the list of views to skip
                if (
                    checklist.auto_add_view == "selected"
                    and view.id not in checklist.view_ids.ids
                ):
                    return arch, view

                notebook = arch.find(".//notebook")
                if notebook is not None:
                    page = f"""
                        <page string="{checklist.name}" name="glo_checklist"
                            invisible="not checklist_item_ids">
                            {self._get_injected_view_contents()}
                        </page>"""
                    notebook.append(etree.fromstring(page))
                else:
                    sheet = arch.find(".//sheet")
                    if sheet is not None:
                        page = f"""
                            <group string="{checklist.name}" name="glo_checklist"
                                invisible="not checklist_item_ids">
                            {self._get_injected_view_contents()}
                            </group>"""
                        sheet.append(etree.fromstring(page))

        return arch, view

    def action_details(self):
        self.ensure_one()
        return {
            "name": "Checklist Details",
            "type": "ir.actions.act_window",
            "res_model": "glo_checklist.item",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }
