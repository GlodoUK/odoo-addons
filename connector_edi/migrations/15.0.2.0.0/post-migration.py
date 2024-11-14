def migrate(cr, _version):
    cr.execute("UPDATE edi_envelope SET use_legacy_body = true")
    cr.execute("UPDATE edi_message SET use_legacy_body = true")
