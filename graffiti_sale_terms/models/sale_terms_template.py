from odoo import fields, models


class SaleTermsTemplate(models.Model):
    _name = 'sale.terms.template'
    _description = 'Sale Terms & Conditions Template'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    category_id = fields.Many2one(
        'sale.terms.category', string='Category', required=True,
        ondelete='restrict',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    terms = fields.Html(string='Terms and Conditions', required=True, translate=True)
