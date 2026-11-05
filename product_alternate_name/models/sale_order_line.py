from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    alt_product_tmpl_id = fields.Many2one(
        "product.template",
        related="product_id.product_tmpl_id",
        string="Alternate Product Template",
    )
    alternate_name_id = fields.Many2one(
        "product.alternate.name",
        string="Sold As",
        compute="_compute_alternate_name_id",
        store=True,
        readonly=False,
        precompute=True,
        domain="[('product_tmpl_id', '=', alt_product_tmpl_id)] if alt_product_tmpl_id else [('product_tmpl_id.sale_ok', '=', True)]",
        help="Alternate name used for this line. The line still points to the "
        "original product (stock, price, taxes unchanged).",
    )

    @api.depends("product_id")
    def _compute_alternate_name_id(self):
        for line in self:
            alt = line.alternate_name_id
            if alt and alt.product_tmpl_id != line.product_id.product_tmpl_id:
                line.alternate_name_id = False

    @api.onchange("alternate_name_id")
    def _onchange_alternate_name_id(self):
        """Choosing an alternate name fills in the original product."""
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
        if not alt or alt.is_primary or not self.product_id:
            return description

        lines = description.split("\n")
        product = self.product_id
        code = alt.code or product.default_code
        first_line = "[%s] %s" % (code, alt.name) if code else alt.name
        # The first line of the standard description is the product name.
        # Keep everything else (variant attributes, etc.)
        rest = lines[1:]
        if alt.description_sale and product.description_sale:
            # swap the product sales description for the alternate one
            rest = [
                l for l in rest if l not in product.description_sale.split("\n")
            ]
            rest.insert(0, alt.description_sale)
        elif alt.description_sale:
            rest.insert(0, alt.description_sale)
        return "\n".join([first_line] + rest)
