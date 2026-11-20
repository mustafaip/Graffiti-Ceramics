from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    alternate_name_id = fields.Many2one(
        "product.alternate.name",
        string="Sold As",
        copy=True,
        index="btree_not_null",
        ondelete="set null",
        help="Alternate name this product was sold under (set from the sales order).",
    )

    def _get_alternate_title(self):
        """Printed title of the line when it uses an alternate name, else False."""
        self.ensure_one()
        alt = self.sudo().alternate_name_id
        if (
            alt
            and not alt.is_primary
            and self.product_id
            and alt.product_tmpl_id == self.product_id.product_tmpl_id
        ):
            return (
                alt.with_context(lang=self.move_id._get_lang())
                ._get_document_title(self.product_id)
            )
        return False

    @api.depends(
        "alternate_name_id",
        "alternate_name_id.name",
        "alternate_name_id.code",
    )
    def _compute_label(self):
        super()._compute_label()
        for line in self:
            title = line._get_alternate_title()
            if not title:
                continue
            product_name = line.product_id.with_context(
                lang=line.move_id._get_lang()
            ).display_name
            description = line.name or ""
            parts = description.split("\n")
            if parts and parts[0] == product_name:
                # description already holds the product name: replace it
                description = "\n".join(parts[1:])
            line.label = "%s\n%s" % (title, description) if description else title

    def _inverse_label(self):
        alias_lines = self.filtered(
            lambda line: line.product_id and line.label and line._get_alternate_title()
        )
        for line in alias_lines:
            title = line._get_alternate_title()
            line.name = line.label.removeprefix(title).removeprefix("\n")
        super(AccountMoveLine, self - alias_lines)._inverse_label()
