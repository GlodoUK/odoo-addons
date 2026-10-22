def migrate(cr, version):
    """The settings view is gone with its fields. Left until the end of the
    update, it breaks every later module that extends the settings form."""
    cr.execute(
        """
        DELETE FROM ir_ui_view
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'account_tax_plastic'
            AND name = 'res_config_settings_view_form'
            AND model = 'ir.ui.view'
        )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'account_tax_plastic'
        AND name = 'res_config_settings_view_form'
        AND model = 'ir.ui.view'
        """
    )
