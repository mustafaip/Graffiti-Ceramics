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
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
        index="btree_not_null",
        domain="[('product_tmpl_id', '=', alt_product_tmpl_id)] if alt_product_tmpl_id else [('product_tmpl_id.sale_ok', '=', True)]",
        help="Name this product is sold under on this line. The line still "
        "points to the original product (stock, price, taxes unchanged).",
=======
>>>>>>> Stashed changes
        domain="[('product_tmpl_id', '=', product_template_id)] if product_template_id else [('product_tmpl_id.sale_ok', '=', True)]",
        help="Name used for this line: either the regular product name or one "
        "of its alternate names. The line still points to the original "
        "product (stock, price, taxes unchanged).",
<<<<<<< Updated upstream
=======
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_active_alternate_name(self):
        """Return the alias to print for this line, or an empty recordset.

        The regular-name entry and entries that belong to another product are
        ignored, so the standard Odoo naming applies to them.
        """
        self.ensure_one()
        alt = self.sudo().alternate_name_id
        if (
            alt
            and not alt.is_primary
            and self.product_id
            and alt.product_tmpl_id == self.product_id.product_tmpl_id
        ):
            return alt
        return alt.browse()

    # ------------------------------------------------------------------
    # Computes / onchanges
    # ------------------------------------------------------------------
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
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
            else:
                line.alternate_name_id = alt
=======
>>>>>>> Stashed changes
            elif not alt or alt.product_tmpl_id != tmpl:
                line.alternate_name_id = Alt.search(
                    [("product_tmpl_id", "=", tmpl.id), ("is_primary", "=", True)],
                    limit=1,
                )
<<<<<<< Updated upstream
=======
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes

    @api.onchange("alternate_name_id")
    def _onchange_alternate_name_id(self):
        """Choosing an alternate name fills in the original product."""
        for line in self:
            alt = line.alternate_name_id
            if alt and line.product_id.product_tmpl_id != alt.product_tmpl_id:
                line.product_id = alt.product_tmpl_id.product_variant_id

<<<<<<< Updated upstream
=======
<<<<<<< HEAD
    # In Odoo 20 the line text is split in two:
    #   * ``name``  = description only (no product name)
    #   * ``label`` = "<product title>\n<description>", what is shown in the
    #                 Description cell and printed on quotations / invoices.
    # The product title comes from ``_get_product_display_name``: overriding
    # it is all that is needed for the alias to show everywhere.
    def _get_product_display_name(self):
        alt = self._get_active_alternate_name()
        if alt:
            return alt._get_document_title(self.product_id)
        return super()._get_product_display_name()

    @api.depends(
        "alternate_name_id",
        "alternate_name_id.name",
        "alternate_name_id.code",
    )
    def _compute_label(self):
        return super()._compute_label()

    @api.depends("alternate_name_id", "alternate_name_id.description_sale")
=======
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
    @api.depends("alternate_name_id")
    def _compute_label(self):
        return super()._compute_label()

=======
>>>>>>> Stashed changes
    @api.depends("alternate_name_id")
    def _compute_label(self):
        return super()._compute_label()

    @api.depends("alternate_name_id")
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
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
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
        alt = self._get_active_alternate_name()
        if alt and alt.description_sale:
            product_description = self.product_id.description_sale
            if product_description and product_description in description:
                description = description.replace(
                    product_description, alt.description_sale, 1
                )
            else:
                description = "\n".join(
                    part for part in (alt.description_sale, description) if part
                )
        return description

    # ------------------------------------------------------------------
    # Invoicing
    # ------------------------------------------------------------------
    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if res.get("product_id"):
            alt = self._get_active_alternate_name()
            if alt:
                res["alternate_name_id"] = alt.id
        return res
=======
>>>>>>> Stashed changes
        alt = self._get_alternate_name()
        if not alt or not alt.description_sale:
            return description
        product_desc = self.product_id.description_sale
        if product_desc and product_desc in description:
            return description.replace(product_desc, alt.description_sale, 1)
        return "\n".join(filter(None, [alt.description_sale, description]))
<<<<<<< Updated upstream
=======
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes
