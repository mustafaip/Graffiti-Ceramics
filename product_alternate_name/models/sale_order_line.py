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
        help="Name used for this line: either the regular product name or one "
        "of its alternate names. The line still points to the original "
        "product (stock, price, taxes unchanged).",
    )

    @api.depends("product_id")
    def _compute_alternate_name_id(self):
        """Keep the picked name consistent with the product.

        Default to the regular-name entry, so the line always shows either the
        product name or the alias, never an empty value.
        """
        Alt = self.env["product.alternate.name"].with_context(active_test=False)
        for line in self:
            tmpl = line.product_id.product_tmpl_id
            alt = line.alternate_name_id
            if not tmpl:
                line.alternate_name_id = False
            elif not alt or alt.product_tmpl_id != tmpl:
                line.alternate_name_id = Alt.search(
                    [("product_tmpl_id", "=", tmpl.id), ("is_primary", "=", True)],
                    limit=1,
                )

    @api.onchange("alternate_name_id")
    def _onchange_alternate_name_id(self):
        """Choosing an alternate name fills in the original product."""
        for line in self:
            alt = line.alternate_name_id
            if alt and line.product_id.product_tmpl_id != alt.product_tmpl_id:
                line.product_id = alt.product_tmpl_id.product_variant_id

    def _get_alternate_name(self):
        """Return the alias record to print, or an empty recordset."""
        self.ensure_one()
        alt = self.alternate_name_id
        if alt and not alt.is_primary and alt.product_tmpl_id == self.product_id.product_tmpl_id:
            return alt
        return self.env["product.alternate.name"]

    # Odoo 20: the line text shown/printed is `label` = product display name
    # + "\n" + description (`name`). Swap the product display name for the
    # alias, and the sales description when the alias defines its own.

    @api.depends("alternate_name_id")
    def _compute_label(self):
        return super()._compute_label()

    @api.depends("alternate_name_id")
    def _compute_name(self):
        return super()._compute_name()

    def _get_product_display_name(self):
        display_name = super()._get_product_display_name()
        alt = self._get_alternate_name()
        if not alt:
            return display_name
        product = self.product_id
        # Keep variant attributes: "Name (Glossy)" -> "Alias (Glossy)"
        base = product.with_context(display_default_code=False).display_name
        tmpl_name = product.product_tmpl_id.name
        if tmpl_name and base.startswith(tmpl_name):
            base = alt.name + base[len(tmpl_name):]
        else:
            base = alt.name
        code = alt.code or product.default_code
        return "[%s] %s" % (code, base) if code else base

    def _get_sale_order_line_multiline_description_sale(self):
        description = super()._get_sale_order_line_multiline_description_sale()
        alt = self._get_alternate_name()
        if not alt or not alt.description_sale:
            return description
        product_desc = self.product_id.description_sale
        if product_desc and product_desc in description:
            return description.replace(product_desc, alt.description_sale, 1)
        return "\n".join(filter(None, [alt.description_sale, description]))
