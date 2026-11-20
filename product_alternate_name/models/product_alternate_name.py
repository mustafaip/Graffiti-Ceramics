from odoo import api, fields, models


class ProductAlternateName(models.Model):
    _name = "product.alternate.name"
    _description = "Product Alternate Name"
    _order = "sequence, id"
    _rec_names_search = ["name", "code", "product_tmpl_id"]

    _name_uniq = models.Constraint(
        "UNIQUE(product_tmpl_id, name)",
        "This alternate name already exists for this product.",
    )

    sequence = fields.Integer(default=10)
    name = fields.Char(string="Alternate Name", required=True, translate=True)
    code = fields.Char(
        string="Alternate Code",
        help="Optional alternate reference / customer code for this name.",
    )
    description_sale = fields.Text(
        string="Sales Description",
        translate=True,
        help="Optional. If set, replaces the product's sales description "
        "on quotations when this alternate name is used.",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product",
        required=True,
        index=True,
        ondelete="cascade",
    )
    active = fields.Boolean(default=True)
    is_primary = fields.Boolean(
        string="Regular Name",
        default=False,
        help="Technical entry carrying the product's regular name so regular "
        "products and aliases can be picked from the same list.",
    )

    @api.depends("name", "product_tmpl_id.display_name")
    def _compute_display_name(self):
        for rec in self:
            if (
                rec.name
                and rec.product_tmpl_id
                and not self.env.context.get("alt_name_only")
            ):
                rec.display_name = "%s (%s)" % (
                    rec.name,
                    rec.product_tmpl_id.display_name,
                )
            else:
                rec.display_name = rec.name or ""
