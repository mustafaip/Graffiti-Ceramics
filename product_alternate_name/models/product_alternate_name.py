from odoo import fields, models


class ProductAlternateName(models.Model):
    _name = "product.alternate.name"
    _description = "Product Alternate Name"
    _order = "sequence, id"

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

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or ""
