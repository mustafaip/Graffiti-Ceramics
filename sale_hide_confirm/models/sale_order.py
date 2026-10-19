from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError

CONFIRM_GROUP = 'sale_hide_confirm.group_confirm_sale_order'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Restrict every Confirm button in the sale.order views to the group.

        Done on the combined arch so it covers all the Confirm buttons
        (draft and sent states) regardless of how the base view defines them.
        The `groups` attribute is evaluated per user after view caching.
        """
        arch, view = super()._get_view(view_id, view_type, **options)
        for node in arch.xpath("//button[@name='action_confirm']"):
            node.set('groups', CONFIRM_GROUP)
        return arch, view

    def action_confirm(self):
        # sudo() is used by the portal signature / online payment flows;
        # let those through, block direct confirmation by other internal users.
        if not self.env.su and not self.env.user.has_group(CONFIRM_GROUP):
            raise UserError(_("You are not allowed to confirm sales orders. "
                              "You can only create quotations."))
        return super().action_confirm()
