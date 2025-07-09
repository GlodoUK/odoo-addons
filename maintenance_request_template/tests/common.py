from odoo.tests import TransactionCase


class MaintenanceRequestTemplateCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Equipment = cls.env["maintenance.equipment"]
        cls.EquipmentCateg = cls.env["maintenance.equipment.category"]
        cls.EquipmentTemplate = cls.env["maintenance.equipment.template"]
        cls.Request = cls.env["maintenance.request"]

        cls.templateA = cls.EquipmentTemplate.create(
            {
                "name": "Template A",
                "description": "Equipment Description",
            }
        )

        cls.templateB = cls.EquipmentTemplate.create(
            {
                "name": "Template B",
                "description": "Categ Description",
            }
        )

        cls.categA = cls.EquipmentCateg.create(
            {
                "name": "CategA",
                "template_id": cls.templateB.id,
            }
        )

        cls.equipmentA = cls.Equipment.create(
            {
                "name": "EquipmentA",
                "category_id": cls.categA.id,
                "template_id": cls.templateA.id,
            }
        )

        cls.equipmentB = cls.Equipment.create(
            {
                "name": "EquipmentB",
                "category_id": cls.categA.id,
            }
        )
