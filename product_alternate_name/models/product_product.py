from odoo import api, models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if value and operator in ("ilike", "like", "=", "=ilike", "=like"):
            alt = Domain(
                "product_tmpl_id.alternate_name_ids.name", operator, value
            ) | Domain("product_tmpl_id.alternate_name_ids.code", operator, value)
            return Domain(domain) | alt
        return domain
