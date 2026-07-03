Automated Export
================

Scheduled export of a model's records to XLSX/CSV using a saved
("Favorites > Save current export") export template, emailed as an
attachment.

The included example scheduled action is disabled by default - set the
export template name, recipient email address and domain to match
your needs, then activate it.

Here is an example ir.cron record to use as a template for creating your own scheduled
action.

.. code-block:: xml

    <record id="cron_example_weekly_export" model="ir.cron">
        <field name="name">Example: Weekly Invoice Export</field>
        <field name="model_id" ref="account.model_account_move" />
        <field name="state">code</field>
        <field name="code">
    # Example weekly invoice export cron job.
    # Modify to your requirements, then set 'Active' to True.

    domain = [
        ("payment_state", "in", ["paid", "in_payment"]),
        ("invoice_date", ">=", datetime.date.today() - datetime.timedelta(weeks=1)),
        ("invoice_date", "<=", datetime.date.today()),
    ]
    model._cron_export_and_email(
        export_template="Weekly Invoice Export", # Required. Can be the name or database ID of the export template
        email_to="text@example.com", # Required
        file_format="xlsx", # Optional. Can be "xlsx" or "csv". Default is "xlsx"
        domain=domain, # Not required, [] (All records of model) by default
        email_subject="Weekly Invoice Export", # If not defined, the export template name will be used
    )</field>
        <field name="interval_number" eval="1" />
        <field name="interval_type">weeks</field>
        <field name="active" eval="False" />
    </record>

.. code-block::
