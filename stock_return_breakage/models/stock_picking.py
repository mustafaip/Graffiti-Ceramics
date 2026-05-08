from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Track breakage returns created from this picking
    breakage_return_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='breakage_origin_picking_id',
        string='Breakage Returns',
    )
    breakage_origin_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Breakage Origin Delivery',
        readonly=True,
        copy=False,
    )
    breakage_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='breakage_picking_id',
        string='Breakage Journal Entries',
    )
    breakage_count = fields.Integer(
        string='Breakage Returns Count',
        compute='_compute_breakage_count',
    )
    breakage_journal_count = fields.Integer(
        string='Breakage Journal Count',
        compute='_compute_breakage_journal_count',
    )

    def _compute_breakage_count(self):
        for rec in self:
            rec.breakage_count = len(rec.breakage_return_ids)

    def _compute_breakage_journal_count(self):
        for rec in self:
            rec.breakage_journal_count = len(rec.breakage_move_ids)

    def action_open_breakage_wizard(self):
        """Open the Return with Breakage wizard."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return with Breakage',
            'res_model': 'stock.return.breakage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            },
        }

    def action_view_breakage_returns(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Breakage Returns',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.breakage_return_ids.ids)],
        }

    def action_view_breakage_journal_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Breakage Journal Entries',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.breakage_move_ids.ids)],
        }
