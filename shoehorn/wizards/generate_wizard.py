"""UI front-end for `odoo shoehorn generate` (see ../generate.py).

Available only when the module is installed; the CLI needs neither this model
nor a database. The wizard does no work of its own - it hands a directory and
a `name.ext` to generate(), so naming, validation and templates stay identical
to the CLI.
"""

from odoo import fields, models
from odoo.exceptions import UserError

from ..generate import generate
from ..migration import EXTENSIONS


class ShoehornGenerateWizard(models.TransientModel):
    _name = "shoehorn.generate.wizard"
    _description = "Generate a shoehorn migration file"

    path = fields.Char(
        string="Directory",
        required=True,
        help="Directory of shoehorn files, on the Odoo server's filesystem."
        " Its basename is the migration namespace.",
    )
    file_type = fields.Selection(
        selection=[(ext, ext) for ext in EXTENSIONS],
        required=True,
        default="py",
    )
    name = fields.Char(
        required=True,
        help="Migration name (the part after the timestamp). For .csv it must"
        " be the target model name, e.g. res.partner.",
    )
    generated_path = fields.Char(string="Generated file", readonly=True)

    def action_generate(self):
        self.ensure_one()
        # generate() does all the filtering/validation; let it own the rules
        # and surface its complaints to the user rather than re-implementing.
        try:
            path = generate(self.path, f"{self.name}.{self.file_type}")
        except (ValueError, OSError) as exc:
            raise UserError(str(exc)) from exc
        self.generated_path = path
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Migration generated"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
