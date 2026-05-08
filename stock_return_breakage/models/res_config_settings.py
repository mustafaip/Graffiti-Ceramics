from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Journal used to reduce inventory value (Stock Valuation Journal)
    breakage_inventory_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Breakage Inventory Journal',
        config_parameter='stock_return_breakage.inventory_journal_id',
        domain=[('type', 'in', ['general', 'purchase'])],
        help='Journal used for the inventory (stock valuation) side of the breakage entry.',
    )

    # Journal used to book the damage / expense
    breakage_expense_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Breakage Expense / Damage Journal',
        config_parameter='stock_return_breakage.expense_journal_id',
        domain=[('type', 'in', ['general', 'purchase'])],
        help='Journal used for the damage expense side of the breakage entry.',
    )

    # Expense account to debit for damage
    breakage_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Damage Expense Account',
        config_parameter='stock_return_breakage.expense_account_id',
        domain=[('account_type', 'like', 'expense')],
        help='Account that will be debited when goods are returned as damaged.',
    )
