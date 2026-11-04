from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    terms_template_ids = fields.Many2many(
        'sale.terms.template',
        string='T&C Templates',
        domain="[('company_id', 'in', (False, company_id))]",
        copy=True,
    )

    @api.onchange('terms_template_ids')
    def _onchange_terms_template_ids(self):
        """Rebuild the printed Terms and Conditions from the selected templates,
        ordered by category then template sequence. The result stays editable."""
        templates = self.terms_template_ids.sorted(
            key=lambda t: (t.category_id.sequence, t.category_id.id, t.sequence, t.id)
        )
        self.note = ''.join(t.terms for t in templates if t.terms) or False
