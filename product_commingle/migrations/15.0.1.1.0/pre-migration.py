from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "product_product", "commingled_ok"):
        return

    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE product_product
        ADD COLUMN commingled_ok boolean
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE
            product_product
        SET commingled_ok = true
        WHERE id IN (
            SELECT
                p.id
            FROM product_product AS p
            INNER JOIN product_template AS t on t.id = p.product_tmpl_id
            WHERE
                t.commingled_ok is true
        )
        """,
    )
