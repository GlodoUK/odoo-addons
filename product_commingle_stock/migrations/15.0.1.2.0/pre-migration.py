from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(
        env.cr, "product_product", "commingled_policy"
    ) and openupgrade.column_exists(env.cr, "product_template", "commingled_policy"):

        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE product_product
            ADD COLUMN commingled_policy varchar,
            ADD COLUMN commingled_prefer_homogenous boolean
            """,
        )

        openupgrade.logged_query(
            env.cr,
            """
            UPDATE
                product_product
            SET
                commingled_policy = product_template.commingled_policy,
                commingled_prefer_homogenous = product_template.commingled_prefer_homogenous
            FROM product_template
            WHERE
                product_template.id = product_product.product_tmpl_id
            """,
        )
