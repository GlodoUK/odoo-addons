from odoo.addons.connector_edi.exceptions import EdiException


class EdiSaleDuplicate(EdiException):
    """
    Duplicate sales order
    """


class EdiSaleUnknownProduct(EdiException):
    """
    Unknown product
    """
