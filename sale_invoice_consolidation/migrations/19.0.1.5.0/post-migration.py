def migrate(cr, version):
    """The settings are now commercial fields: give every contact its commercial
    entity's values, in every company, as Odoo does when the entity is edited."""
    cr.execute(
        """
        UPDATE res_partner p
           SET sale_invoice_consolidation = cp.sale_invoice_consolidation,
               sale_auto_invoice_frequency = cp.sale_auto_invoice_frequency,
               sale_auto_invoice_action = cp.sale_auto_invoice_action,
               sale_auto_invoice_next_date = cp.sale_auto_invoice_next_date
          FROM res_partner cp
         WHERE cp.id = p.commercial_partner_id
           AND p.id != cp.id
           AND (
                p.sale_invoice_consolidation
                    IS DISTINCT FROM cp.sale_invoice_consolidation
                OR p.sale_auto_invoice_frequency
                    IS DISTINCT FROM cp.sale_auto_invoice_frequency
                OR p.sale_auto_invoice_action
                    IS DISTINCT FROM cp.sale_auto_invoice_action
                OR p.sale_auto_invoice_next_date
                    IS DISTINCT FROM cp.sale_auto_invoice_next_date
           )
        """
    )
