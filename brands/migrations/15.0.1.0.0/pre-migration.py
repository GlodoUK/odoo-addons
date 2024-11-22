from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "brands.external_layout_background",
            "brands.external_layout_clean",
        ],
    )
