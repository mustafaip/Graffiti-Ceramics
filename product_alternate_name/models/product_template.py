from odoo import api, fields, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternate_name_ids = fields.One2many(
        "product.alternate.name",
        "product_tmpl_id",
        string="Alternate Names",
        copy=True,
    )
    alternate_name_count = fields.Integer(compute="_compute_alternate_name_count")

    @api.depends("alternate_name_ids")
    def _compute_alternate_name_count(self):
        for tmpl in self:
            tmpl.alternate_name_count = len(tmpl.alternate_name_ids)

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if value and operator in ("ilike", "like", "=", "=ilike", "=like"):
            alt = Domain("alternate_name_ids.name", operator, value) | Domain(
                "alternate_name_ids.code", operator, value
            )
            return Domain(domain) | alt
        return domain
