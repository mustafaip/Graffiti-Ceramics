from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    breakage_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Breakage Delivery',
        readonly=True,
        copy=False,
    )
