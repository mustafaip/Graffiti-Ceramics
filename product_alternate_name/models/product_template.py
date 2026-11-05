from odoo import api, fields, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternate_name_ids = fields.One2many(
        "product.alternate.name",
        "product_tmpl_id",
        string="Alternate Names",
        copy=False,
        domain=[("is_primary", "=", False)],
    )
    alternate_name_count = fields.Integer(compute="_compute_alternate_name_count")

    def _sync_primary_alternate_name(self):
        Alt = self.env["product.alternate.name"].sudo().with_context(active_test=False)
        for tmpl in self:
            primary = Alt.search(
                [("product_tmpl_id", "=", tmpl.id), ("is_primary", "=", True)], limit=1
            )
            if primary:
                if primary.name != tmpl.name:
                    primary.name = tmpl.name
            elif tmpl.name:
                Alt.create(
                    {
                        "product_tmpl_id": tmpl.id,
                        "name": tmpl.name,
                        "is_primary": True,
                        "sequence": -1,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._sync_primary_alternate_name()
        return templates

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            self._sync_primary_alternate_name()
        return res

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
