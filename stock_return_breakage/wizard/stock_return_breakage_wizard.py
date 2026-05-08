from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockReturnBreakageWizardLine(models.TransientModel):
    _name = 'stock.return.breakage.wizard.line'
    _description = 'Return with Breakage Wizard Line'

    wizard_id = fields.Many2one('stock.return.breakage.wizard', required=True, ondelete='cascade')
    move_id = fields.Many2one('stock.move', string='Stock Move', required=True)
    product_id = fields.Many2one('product.product', string='Product', related='move_id.product_id', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit', related='move_id.product_uom', readonly=True)
    quantity = fields.Float(string='Qty to Return', digits='Product Unit of Measure', required=True)
    done_qty = fields.Float(string='Done Qty', related='move_id.quantity', readonly=True)
    unit_cost = fields.Float(string='Unit Cost', digits='Product Price')


class StockReturnBreakageWizard(models.TransientModel):
    _name = 'stock.return.breakage.wizard'
    _description = 'Return with Breakage Wizard'

    picking_id = fields.Many2one(
        'stock.picking', string='Delivery', required=True, readonly=True,
    )
    line_ids = fields.One2many(
        'stock.return.breakage.wizard.line', 'wizard_id', string='Products to Return',
    )
    inventory_journal_id = fields.Many2one(
        'account.journal', string='Inventory Journal',
        domain=[('type', 'in', ['general', 'purchase'])],
        required=True,
        help='Journal for the stock valuation/inventory side of the entry.',
    )
    expense_journal_id = fields.Many2one(
        'account.journal', string='Damage Expense Journal',
        domain=[('type', 'in', ['general', 'purchase'])],
        required=True,
        help='Journal for the damage expense entry.',
    )
    expense_account_id = fields.Many2one(
        'account.account', string='Damage Expense Account',
        domain=[('account_type', 'like', 'expense')],
        required=True,
        help='Account debited for the damaged goods.',
    )
    notes = fields.Text(string='Reason / Notes')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_id = self.env.context.get('default_picking_id')
        if not picking_id:
            return res

        picking = self.env['stock.picking'].browse(picking_id)

        # Load configured journals/accounts from settings
        ICP = self.env['ir.config_parameter'].sudo()
        inv_journal_id = int(ICP.get_param('stock_return_breakage.inventory_journal_id', 0))
        exp_journal_id = int(ICP.get_param('stock_return_breakage.expense_journal_id', 0))
        exp_account_id = int(ICP.get_param('stock_return_breakage.expense_account_id', 0))

        lines = []
        for move in picking.move_ids.filtered(lambda m: m.state == 'done' and m.quantity > 0):
            # Attempt to get the standard cost of the product
            unit_cost = move.product_id.standard_price or 0.0
            lines.append((0, 0, {
                'move_id': move.id,
                'quantity': move.quantity,
                'unit_cost': unit_cost,
            }))

        res.update({
            'line_ids': lines,
            'inventory_journal_id': inv_journal_id or False,
            'expense_journal_id': exp_journal_id or False,
            'expense_account_id': exp_account_id or False,
        })
        return res

    def _get_stock_valuation_account(self, product):
        """Return the stock valuation account for the product's category."""
        categ = product.categ_id
        if not categ.property_stock_valuation_account_id:
            raise UserError(
                _('Product category "%s" has no Stock Valuation Account configured. '
                  'Please set it under Inventory > Configuration > Product Categories.')
                % categ.name
            )
        return categ.property_stock_valuation_account_id

    def action_confirm(self):
        self.ensure_one()
        picking = self.picking_id

        if picking.state != 'done':
            raise UserError(_('You can only create a breakage return for a validated delivery.'))

        lines = self.line_ids.filtered(lambda l: l.quantity > 0)
        if not lines:
            raise UserError(_('Please enter a quantity greater than zero for at least one product.'))

        for line in lines:
            if line.quantity > line.done_qty:
                raise UserError(
                    _('Return quantity (%.2f) for product "%s" exceeds the delivered quantity (%.2f).')
                    % (line.quantity, line.product_id.display_name, line.done_qty)
                )

        # ------------------------------------------------------------------ #
        # 1.  Create the reverse stock picking (return)
        # ------------------------------------------------------------------ #
        return_picking_type = picking.picking_type_id.return_picking_type_id \
            or picking.picking_type_id

        return_picking = self.env['stock.picking'].create({
            'picking_type_id': return_picking_type.id,
            'partner_id': picking.partner_id.id,
            'origin': _('Breakage Return of %s') % picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': picking.location_id.id,
            'breakage_origin_picking_id': picking.id,
            'note': self.notes or '',
            'company_id': picking.company_id.id,
        })

        for line in lines:
            self.env['stock.move'].create({
                'name': _('Return with Breakage: %s') % line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'picking_id': return_picking.id,
                'location_id': return_picking.location_id.id,
                'location_dest_id': return_picking.location_dest_id.id,
                'origin_returned_move_id': line.move_id.id,
                'to_refund': True,
            })

        return_picking.action_confirm()
        return_picking.action_assign()

        # Immediate transfer – set all demand as done and validate
        for move in return_picking.move_ids:
            move.quantity = move.product_uom_qty
        return_picking._action_done()

        # ------------------------------------------------------------------ #
        # 2.  Create the accounting journal entry
        #     DR  Damage Expense Account   (expense_account_id)
        #     CR  Stock Valuation Account  (per product category)
        # ------------------------------------------------------------------ #
        move_lines = []
        total_value = 0.0

        for line in lines:
            amount = line.quantity * line.unit_cost
            if amount == 0.0:
                continue
            total_value += amount
            stock_account = self._get_stock_valuation_account(line.product_id)
            label = _('Breakage: %s x %.2f') % (line.product_id.display_name, line.quantity)

            # Credit stock valuation (reduce inventory value)
            move_lines.append((0, 0, {
                'name': label,
                'account_id': stock_account.id,
                'debit': 0.0,
                'credit': amount,
                'quantity': line.quantity,
                'product_id': line.product_id.id,
            }))

        if not move_lines:
            # No costs to post – still show the return picking
            return self._return_action(return_picking)

        # Single debit line to damage expense account for the total
        move_lines.append((0, 0, {
            'name': _('Damage Expense – Breakage Return of %s') % picking.name,
            'account_id': self.expense_account_id.id,
            'debit': total_value,
            'credit': 0.0,
        }))

        journal_entry = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.expense_journal_id.id,
            'ref': _('Breakage Return: %s → %s') % (picking.name, return_picking.name),
            'narration': self.notes or '',
            'breakage_picking_id': picking.id,
            'line_ids': move_lines,
        })
        journal_entry.action_post()

        return self._return_action(return_picking)

    def _return_action(self, return_picking):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Breakage Return'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': return_picking.id,
        }
