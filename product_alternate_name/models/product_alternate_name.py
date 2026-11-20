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
        "on quotations and invoices when this alternate name is used.",
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

    @api.depends("name", "is_primary", "product_tmpl_id.display_name")
    @api.depends_context("alt_name_only")
    def _compute_display_name(self):
        """Never return an empty name: the web client shows "Unnamed" for it."""
        for rec in self:
<<<<<<< Updated upstream
            name = rec.name or rec.product_tmpl_id.name or ""
            if (
                name
=======
<<<<<<< HEAD
            name = rec.name or rec.product_tmpl_id.display_name or rec.code or ""
            if (
                name
                and rec.name
=======
            name = rec.name or rec.product_tmpl_id.name or ""
            if (
                name
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes
                and rec.product_tmpl_id
                and not rec.is_primary
                and not self.env.context.get("alt_name_only")
            ):
<<<<<<< Updated upstream
                rec.display_name = "%s (%s)" % (name, rec.product_tmpl_id.display_name)
            else:
                rec.display_name = name
=======
<<<<<<< HEAD
                name = "%s (%s)" % (rec.name, rec.product_tmpl_id.display_name)
            rec.display_name = name

    def _get_document_title(self, product=None):
        """Title printed on document lines: ``[code] Alias (variant)``."""
        self.ensure_one()
        product = product or self.product_tmpl_id.product_variant_id
        code = self.code or (product.default_code if product else False)
        title = "[%s] %s" % (code, self.name) if code else self.name
        ptavs = product.product_template_attribute_value_ids if product else False
        if ptavs and hasattr(ptavs, "_get_combination_name"):
            variant = ptavs._get_combination_name()
            if variant:
                title = "%s (%s)" % (title, variant)
        return title
=======
                rec.display_name = "%s (%s)" % (name, rec.product_tmpl_id.display_name)
            else:
                rec.display_name = name
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes
