def migrate(cr, _version):
    cr.execute(
        """
    UPDATE
        edi_envelope_route
    SET
        queue_enclose_messages_priority = queue_priority,
        queue_enclose_messages_identity_exact = queue_identity_exact,
        queue_enclose_messages_channel = queue_channel,

        queue_open_messages_priority = queue_priority,
        queue_open_messages_identity_exact = queue_identity_exact,
        queue_open_messages_channel = queue_channel
    """
    )
