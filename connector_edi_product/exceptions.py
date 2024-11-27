from odoo.addons.connector_edi.exceptions import EdiException


class EdiProductDuplicate(EdiException):
    """
    Duplicate product
    """
