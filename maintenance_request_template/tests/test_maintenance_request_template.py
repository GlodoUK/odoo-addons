from odoo.tests import Form

from .common import MaintenanceRequestTemplateCommon


class TestMaintenanceRequestTemplate(MaintenanceRequestTemplateCommon):
    def test_template_onchange(self):
        request_id = self.Request.create(
            {
                "name": "Request",
                "stage_id": self.env.ref("maintenance.stage_0").id,
            }
        )

        with Form(request_id) as request_form:
            request_form.equipment_id = self.equipmentA
            request_form.save()

            self.assertEqual(
                request_form.description,
                self.equipmentA.template_id.description,
            )

            request_form.equipment_id = self.equipmentB
            request_form.save()

            self.assertEqual(
                request_form.description,
                self.equipmentB.category_id.template_id.description,
            )

    def test_template_category(self):
        request_id = self.Request.create(
            {
                "name": "Request",
                "equipment_id": self.equipmentB.id,
                "stage_id": self.env.ref("maintenance.stage_0").id,
                "description": "ABC",
            }
        ).copy()

        self.assertEqual(
            request_id.description,
            self.equipmentB.category_id.template_id.description,
        )

    def test_template_equipment(self):
        request_id = self.Request.create(
            {
                "name": "Request",
                "equipment_id": self.equipmentA.id,
                "stage_id": self.env.ref("maintenance.stage_0").id,
                "description": "ABC",
            }
        ).copy()

        self.assertEqual(
            request_id.description,
            self.equipmentA.template_id.description,
        )

    def test_template_none(self):
        self.equipmentA.template_id.description = False
        self.equipmentA.category_id.template_id.description = False
        self.equipmentA.note = "equipmentA Note"

        request_id = self.Request.create(
            {
                "name": "Request",
                "equipment_id": self.equipmentA.id,
                "stage_id": self.env.ref("maintenance.stage_0").id,
                "description": "ABC",
            }
        ).copy()

        self.assertEqual(
            request_id.description,
            self.equipmentA.note,
        )
