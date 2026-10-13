def migrate(cr, version):
    """Explosion is now a manual button: the BoM mode and the template flag
    are gone."""
    cr.execute("ALTER TABLE mrp_bom DROP COLUMN IF EXISTS sale_explode")
    cr.execute(
        "ALTER TABLE product_template DROP COLUMN IF EXISTS sale_mrp_phantom_explode_ok"
    )
