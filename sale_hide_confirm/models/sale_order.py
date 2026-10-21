from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Remove every Confirm button from the sale.order views, for all users."""
        arch, view = super()._get_view(view_id, view_type, **options)
        for node in arch.xpath("//button[@name='action_confirm']"):
            node.getparent().remove(node)
        return arch, view

    def action_confirm(self):
        # sudo() is used by the portal signature / online payment flows;
        # let those through, block direct confirmation by any internal user.
        if not self.env.su:
            raise UserError(_("Sales orders cannot be confirmed here. "
                              "You can only create quotations."))
        return super().action_confirm()
