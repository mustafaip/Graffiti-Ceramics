from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    alternate_name_id = fields.Many2one(
        "product.alternate.name",
        string="Sold As",
        compute="_compute_alternate_name_id",
        store=True,
        readonly=False,
        precompute=True,
        domain="[('product_tmpl_id', '=', product_template_id)] if product_template_id "
        "else [('product_tmpl_id.sale_ok', '=', True)]",
        help="Optional alternate name printed for this line. The line still "
        "points to the original product (stock, price, taxes unchanged). "
        "Leave empty to use the product's regular name.",
    )
    product_has_alternate_names = fields.Boolean(
        compute="_compute_product_has_alternate_names"
    )

    @api.depends("product_id")
    def _compute_product_has_alternate_names(self):
        for line in self:
            line.product_has_alternate_names = bool(
                line.product_id.product_tmpl_id.alternate_name_ids
            )

    @api.depends("product_id", "display_type")
    def _compute_alternate_name_id(self):
        for line in self:
            alt = line.alternate_name_id
            if line.display_type or (
                alt and alt.product_tmpl_id != line.product_id.product_tmpl_id
            ):
                line.alternate_name_id = False

    @api.onchange("alternate_name_id")
    def _onchange_alternate_name_id(self):
        """Choosing an alternate name first fills in the original product."""
        for line in self:
            alt = line.alternate_name_id
            if alt and line.product_id.product_tmpl_id != alt.product_tmpl_id:
                line.product_id = alt.product_tmpl_id.product_variant_id

    @api.depends("alternate_name_id")
    def _compute_name(self):
        # Re-run standard description logic; it calls
        # _get_sale_order_line_multiline_description_sale() below.
        return super()._compute_name()

    def _get_sale_order_line_multiline_description_sale(self):
        description = super()._get_sale_order_line_multiline_description_sale()
        alt = self.alternate_name_id
        if not alt or not self.product_id or self.display_type:
            return description

        product = self.product_id
        code = alt.code or product.default_code
        first_line = "[%s] %s" % (code, alt.name) if code else alt.name
        # The first line of the standard description is the product name.
        # Keep everything else (variant attributes, etc.)
        rest = description.split("\n")[1:]
        if alt.description_sale:
            if product.description_sale:
                product_desc = product.description_sale.split("\n")
                rest = [l for l in rest if l not in product_desc]
            rest.insert(0, alt.description_sale)
        return "\n".join([first_line] + rest)
