from odoo.addons.connector_edi.exceptions import EdiException


class EdiSaleDuplicate(EdiException):
    """
    Duplicate sale order
    """


class EdiSaleUnknownProduct(EdiException):
    """
    Unknown product
    """
