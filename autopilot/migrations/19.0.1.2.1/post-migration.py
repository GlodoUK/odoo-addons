def migrate(cr, version):
    # Generated cron/automation code left the model name unquoted
    # (env[some.model]), which fails with a NameError. Quote it.
    cr.execute(
        r"""
        UPDATE ir_act_server
           SET code = regexp_replace(code, '^env\[([a-z0-9_.]+)\]', 'env[''\1'']')
         WHERE code ~ '^env\[[a-z0-9_.]+\]'
        """
    )
