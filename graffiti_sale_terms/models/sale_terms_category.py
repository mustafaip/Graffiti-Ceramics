from odoo import fields, models


class SaleTermsCategory(models.Model):
    _name = 'sale.terms.category'
    _description = 'Sale Terms & Conditions Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
