from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta, date


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    pdc_id = fields.Many2one('pdc.wizard')


# ---------------------------------------------------------------------------
# PDC Invoice Allocation Line
# ---------------------------------------------------------------------------
class PDCInvoiceAllocation(models.Model):
    """
    One row per invoice linked to a PDC cheque.
    Stores the amount the user wants to allocate from the cheque to that invoice.
    """
    _name = 'pdc.invoice.allocation'
    _description = 'PDC Invoice Allocation'

    pdc_id = fields.Many2one('pdc.wizard', string='PDC', ondelete='cascade', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice / Bill', required=True)
    invoice_date = fields.Date(related='invoice_id.invoice_date', string='Invoice Date', readonly=True, store=True)
    invoice_date_due = fields.Date(related='invoice_id.invoice_date_due', string='Due Date', readonly=True, store=True)
    amount_total = fields.Monetary(related='invoice_id.amount_total', string='Invoice Total', readonly=True)
    amount_residual = fields.Monetary(related='invoice_id.amount_residual', string='Outstanding', readonly=True)
    currency_id = fields.Many2one(related='pdc_id.currency_id', readonly=True)
    allocated_amount = fields.Monetary(string='Allocated Amount', default=0.0)

    @api.constrains('allocated_amount', 'invoice_id')
    def _check_allocated_amount(self):
        for rec in self:
            if rec.allocated_amount < 0:
                raise UserError("Allocated amount cannot be negative.")
            if rec.invoice_id and rec.allocated_amount > rec.invoice_id.amount_residual + 0.001:
                raise UserError(
                    "Allocated amount (%.2f) exceeds the outstanding balance (%.2f) "
                    "for invoice %s." % (
                        rec.allocated_amount,
                        rec.invoice_id.amount_residual,
                        rec.invoice_id.name,
                    )
                )

    @api.onchange('allocated_amount')
    def _onchange_allocated_amount(self):
        if self.allocated_amount < 0:
            self.allocated_amount = 0.0
            return {'warning': {'title': 'Invalid Amount', 'message': 'Allocated amount cannot be negative.'}}
        if self.invoice_id and self.amount_residual and self.allocated_amount > self.amount_residual:
            self.allocated_amount = self.amount_residual
            return {'warning': {
                'title': 'Amount Exceeds Outstanding',
                'message': 'Allocated amount has been capped to the invoice outstanding balance.',
            }}


# ---------------------------------------------------------------------------
# PDC Wizard (main cheque model)
# ---------------------------------------------------------------------------
class PDC_wizard(models.Model):
    _name = "pdc.wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PDC Wizard"

    # ------------------------------------------------------------------ #
    # Unlink guard                                                         #
    # ------------------------------------------------------------------ #
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("You can only delete a PDC in Draft state.")
        return super().unlink()

    # ------------------------------------------------------------------ #
    # Action: open PDC wizard from invoice list                           #
    # ------------------------------------------------------------------ #
    def action_register_check(self):
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        account_move_model = self.env[active_model].browse(active_id)
        if account_move_model.move_type not in ('out_invoice', 'in_invoice'):
            raise UserError("Only Customer Invoices and Vendor Bills are supported for PDC!")

        if not active_ids:
            raise UserError("No invoices selected.")

        account_moves = self.env[active_model].browse(active_ids)
        partners = account_moves.mapped('partner_id')
        if len(set(partners.ids)) != 1:
            raise UserError('All selected invoices must belong to the same partner.')

        states = account_moves.mapped('state')
        if set(states) != {'posted'}:
            raise UserError('Only posted invoices/bills can be paid by PDC.')

        move_list = []
        payment_amount = 0.0
        for move in account_moves:
            if move.payment_state != 'paid' and move.amount_residual != 0.0:
                payment_amount += move.amount_residual
                move_list.append(move.id)

        if not move_list:
            raise UserError("All selected invoices/bills are already fully paid.")

        payment_type = 'send_money' if account_moves[0].move_type == 'in_invoice' else 'receive_money'

        return {
            'name': 'PDC Payment',
            'res_model': 'pdc.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jm_pdc.sh_pdc_wizard_form_wizard').id,
            'context': {
                'default_invoice_ids': [(6, 0, move_list)],
                'default_partner_id': account_move_model.partner_id.id,
                'default_payment_amount': payment_amount,
                'default_payment_type': payment_type,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    # ------------------------------------------------------------------ #
    # Smart buttons                                                        #
    # ------------------------------------------------------------------ #
    def open_attachments(self):
        action = self.env.ref('base.action_attachment').read()[0]
        action['domain'] = [('id', 'in', self.attachment_ids.ids)]
        return action

    def open_journal_items(self):
        action = self.env.ref('account.action_account_moves_all').read()[0]
        ids = self.env['account.move.line'].search([('pdc_id', '=', self.id)]).ids
        action['domain'] = [('id', 'in', ids)] if ids else [('id', '=', False)]
        return action

    def open_journal_entry(self):
        action = self.env.ref('jm_pdc.sh_pdc_action_move_journal_line').read()[0]
        ids = self.env['account.move'].search([('pdc_id', '=', self.id)]).ids
        action['domain'] = [('id', 'in', ids)]
        return action

    # ------------------------------------------------------------------ #
    # default_get                                                          #
    # ------------------------------------------------------------------ #
    @api.model
    def default_get(self, fields_list):
        rec = super().default_get(fields_list)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids)
        if invoices and len(invoices) == 1:
            invoice = invoices[0]
            if invoice.move_type in ('out_invoice', 'out_refund'):
                rec['payment_type'] = 'receive_money'
            elif invoice.move_type in ('in_invoice', 'in_refund'):
                rec['payment_type'] = 'send_money'
            rec.update({
                'partner_id': invoice.partner_id.id,
                'payment_amount': invoice.amount_residual,
                'invoice_id': invoice.id,
                'due_date': invoice.invoice_date_due,
                'memo': invoice.name,
            })
        return rec

    # ------------------------------------------------------------------ #
    # Fields                                                               #
    # ------------------------------------------------------------------ #
    name = fields.Char("Name", default='New', readonly=True, tracking=True)
    payment_type = fields.Selection(
        [('receive_money', 'Receive Money'), ('send_money', 'Send Money')],
        string="Payment Type", default='receive_money', tracking=True)
    partner_id = fields.Many2one('res.partner', string="Partner", tracking=True)
    payment_amount = fields.Monetary("Total Amount", tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.company.currency_id, tracking=True)
    reference = fields.Char("Cheque Reference", tracking=True)
    journal_id = fields.Many2one(
        'account.journal', string="Journal",
        domain=[('type', '=', 'bank')], required=True, tracking=True)
    cheque_status = fields.Selection(
        [('draft', 'Draft'), ('deposit', 'Deposit'), ('paid', 'Paid')],
        string="Cheque Status", default='draft', tracking=True)
    payment_date = fields.Date("Date", default=fields.Date.today(), required=True, tracking=True)
    due_date = fields.Date("Due Date", required=True, tracking=True)
    memo = fields.Char("Memo", tracking=True)
    agent = fields.Char("Agent", tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank", tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', 'pdc_attachment_rel', string='Cheque Image')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, tracking=True)
    invoice_id = fields.Many2one('account.move', string="Invoice/Bill", tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
         ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'), ('cancel', 'Cancelled')],
        string="State", default='draft', tracking=True)

    deposited_debit = fields.Many2one('account.move.line')
    deposited_credit = fields.Many2one('account.move.line')

    invoice_ids = fields.Many2many('account.move', string='Invoices / Bills')
    account_move_ids = fields.Many2many(
        'account.move', compute='compute_account_moves',
        string='Available Invoices')
    done_date = fields.Date(string="Done Date", readonly=True, tracking=True)

    # NEW: per-invoice allocation lines
    allocation_ids = fields.One2many(
        'pdc.invoice.allocation', 'pdc_id', string='Invoice Allocations')
    total_allocated = fields.Monetary(
        string='Total Allocated', compute='_compute_total_allocated', store=True)

    # ------------------------------------------------------------------ #
    # Computed fields                                                      #
    # ------------------------------------------------------------------ #
    @api.depends('allocation_ids.allocated_amount')
    def _compute_total_allocated(self):
        for rec in self:
            rec.total_allocated = sum(rec.allocation_ids.mapped('allocated_amount'))

    @api.constrains('total_allocated', 'payment_amount')
    def _check_total_allocated(self):
        for rec in self:
            if rec.total_allocated and rec.payment_amount and rec.total_allocated > rec.payment_amount + 0.001:
                raise UserError(
                    "Total allocated amount (%.2f) exceeds the cheque amount (%.2f). "
                    "Please reduce the allocated amounts." % (rec.total_allocated, rec.payment_amount)
                )

    @api.depends('payment_type', 'partner_id')
    def compute_account_moves(self):
        for rec in self:
            rec.account_move_ids = False
            if not rec.partner_id:
                continue
            domain = [
                ('partner_id', '=', rec.partner_id.id),
                ('payment_state', '!=', 'paid'),
                ('amount_residual', '!=', 0.0),
                ('state', '=', 'posted'),
            ]
            if rec.payment_type == 'receive_money':
                domain.append(('move_type', '=', 'out_invoice'))
            else:
                domain.append(('move_type', '=', 'in_invoice'))
            rec.account_move_ids = self.env['account.move'].search(domain)

    # ------------------------------------------------------------------ #
    # Onchange: partner → auto-fill invoices + allocation lines           #
    # ------------------------------------------------------------------ #
    @api.onchange('partner_id', 'payment_type')
    def _onchange_partner(self):
        # Only update the invoice_ids widget domain/selection — do NOT build
        # allocation lines here. allocation lines are built from real DB IDs
        # inside _sync_allocation_lines(), called from create() and write().
        if not self.partner_id:
            self.invoice_ids = [(5, 0, 0)]
            return

        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '!=', 0.0),
            ('state', '=', 'posted'),
        ]
        if self.payment_type == 'receive_money':
            domain.append(('move_type', '=', 'out_invoice'))
        else:
            domain.append(('move_type', '=', 'in_invoice'))

        moves = self.env['account.move'].search(domain)
        if self.env.company.auto_fill_open_invoice:
            self.invoice_ids = [(6, 0, moves.ids)]

    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        # Intentionally left empty — allocation lines are built from real DB IDs
        # inside _sync_allocation_lines() after the record is saved.
        # Building them here from virtual NewIds causes blank invoice_id columns.
        pass

    # ------------------------------------------------------------------ #
    # button_register (popup)                                              #
    # ------------------------------------------------------------------ #
    def button_register(self):
        for rec in self:
            # ── Step 1: Merge invoice_id + invoice_ids into one deduplicated set ──
            all_ids = set()
            if rec.invoice_id:
                all_ids.add(rec.invoice_id.id)
            all_ids.update(rec.invoice_ids.ids)
            if all_ids != set(rec.invoice_ids.ids):
                rec.write({'invoice_ids': [(6, 0, list(all_ids))]})
                # write() will trigger _sync_allocation_lines via the write override

            # ── Step 2: Validate total allocated does not exceed cheque amount ──
            total_alloc = sum(rec.allocation_ids.mapped('allocated_amount'))
            if total_alloc > rec.payment_amount + 0.001:
                raise UserError(
                    "Total allocated amount (%.2f) exceeds the cheque amount (%.2f). "
                    "Please adjust the Invoice Allocation tab." % (total_alloc, rec.payment_amount)
                )

            # ── Step 3: Execute state transitions ─────────────────────────────
            if rec.cheque_status == 'draft':
                rec.action_register()
            elif rec.cheque_status == 'deposit':
                rec.action_register()
                rec.action_deposited()
            elif rec.cheque_status == 'paid':
                rec.action_register()
                rec.action_deposited()
                rec.action_done()

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #
    def check_payment_amount(self):
        if self.payment_amount <= 0.0:
            raise UserError("Amount must be greater than zero!")

    def check_pdc_account(self):
        if self.payment_type == 'receive_money':
            if not self.env.company.pdc_customer:
                raise UserError("Please set the PDC payment account for Customer in settings!")
            return self.env.company.pdc_customer.id
        else:
            if not self.env.company.pdc_vendor:
                raise UserError("Please set the PDC payment account for Supplier in settings!")
            return self.env.company.pdc_vendor.id

    def get_partner_account(self):
        if self.payment_type == 'receive_money':
            return self.partner_id.property_account_receivable_id.id
        return self.partner_id.property_account_payable_id.id

    def get_credit_move_line(self, account):
        return {
            'pdc_id': self.id,
            'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_debit_move_line(self, account):
        return {
            'pdc_id': self.id,
            'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_move_vals(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id,
            'ref': self.memo,
            'move_type': 'entry',
            'line_ids': [(0, 0, debit_line), (0, 0, credit_line)],
        }

    # ------------------------------------------------------------------ #
    # _build_alloc_map                                                     #
    # Returns {invoice_id: allocated_amount} from allocation_ids,         #
    # falling back to proportional split if no lines exist.               #
    # ------------------------------------------------------------------ #
    def _build_alloc_map(self):
        """
        Returns {invoice_id (int): allocated_amount (float)}.
        Reads from allocation_ids if populated; falls back to proportional split.
        """
        alloc_map = {}
        if self.allocation_ids:
            for line in self.allocation_ids:
                if line.invoice_id and line.allocated_amount > 0:
                    alloc_map[line.invoice_id.id] = line.allocated_amount
        if not alloc_map:
            remaining = self.payment_amount
            for invoice in self.invoice_ids:
                amt = min(invoice.amount_residual, remaining)
                alloc_map[invoice.id] = amt
                remaining -= amt
                if remaining <= 0:
                    break
        return alloc_map

    # ------------------------------------------------------------------ #
    # action_register                                                      #
    # Creates ONE PDC entry for the full cheque amount, then uses         #
    # account.partial.reconcile to allocate exactly the right amount      #
    # per invoice. Field names confirmed against live Odoo 19 instance.   #
    # ------------------------------------------------------------------ #
    def action_register(self):
        self.check_payment_amount()

        if self.invoice_ids:
            total_residual = self.currency_id.round(
                sum(self.invoice_ids.mapped('amount_residual'))
            ) if self.currency_id else round(sum(self.invoice_ids.mapped('amount_residual')), 2)
            if total_residual != 0 and self.payment_amount > total_residual:
                raise UserError(
                    "Payment amount is greater than the total outstanding balance of the linked invoices!"
                )

        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        if self.payment_type == 'receive_money':
            debit_vals = self.get_debit_move_line(pdc_account)
            credit_vals = self.get_credit_move_line(partner_account)
        else:
            debit_vals = self.get_debit_move_line(partner_account)
            credit_vals = self.get_credit_move_line(pdc_account)

        move_vals = self.get_move_vals(debit_vals, credit_vals)
        move_id = self.env['account.move'].create(move_vals)
        move_id.action_post()

        deposited_debit = move_id.line_ids.filtered(lambda x: x.debit > 0)[:1]
        deposited_credit = move_id.line_ids.filtered(lambda x: x.credit > 0)[:1]

        # PDC AR/AP line — this is the line we partially reconcile against each invoice
        pdc_ar_line = move_id.line_ids.filtered(
            lambda l: l.account_id.id == partner_account
        )[:1]

        alloc_map = self._build_alloc_map()
        move_currency = self.currency_id or self.env.company.currency_id

        for invoice in self.invoice_ids:
            allocated = alloc_map.get(invoice.id, 0.0)
            if allocated <= 0 or not pdc_ar_line:
                continue

            inv_ar_line = invoice.line_ids.filtered(
                lambda l: l.account_id.id == partner_account and not l.reconciled
            )[:1]
            if not inv_ar_line:
                continue

            if self.payment_type == 'receive_money':
                debit_line = inv_ar_line   # invoice AR is debit
                credit_line = pdc_ar_line  # PDC AR is credit
            else:
                debit_line = pdc_ar_line   # PDC AP is debit
                credit_line = inv_ar_line  # invoice AP is credit

            # Confirmed Odoo 19 fields: debit_move_id, credit_move_id, amount,
            # debit_amount_currency, credit_amount_currency,
            # debit_currency_id, credit_currency_id
            self.env['account.partial.reconcile'].create({
                'debit_move_id': debit_line.id,
                'credit_move_id': credit_line.id,
                'amount': allocated,
                'debit_amount_currency': allocated,
                'credit_amount_currency': allocated,
                'debit_currency_id': move_currency.id,
                'credit_currency_id': move_currency.id,
            })

        self.write({
            'state': 'registered',
            'deposited_debit': deposited_debit.id,
            'deposited_credit': deposited_credit.id,
        })

    # ------------------------------------------------------------------ #
    # action_returned                                                      #
    # ------------------------------------------------------------------ #
    def action_returned(self):
        self.check_payment_amount()
        self.write({'state': 'returned'})

    # ------------------------------------------------------------------ #
    # action_deposited                                                     #
    # ------------------------------------------------------------------ #
    def action_deposited(self):
        self.write({'state': 'deposited'})

    # ------------------------------------------------------------------ #
    # action_bounced                                                       #
    # FIX #5: unreconcile invoice lines before creating the reverse entry #
    # ------------------------------------------------------------------ #
    def action_bounced(self):
        self.check_payment_amount()
        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        # --- Unreconcile any lines that were reconciled during action_register ---
        for invoice in self.invoice_ids:
            lines_to_unreconcile = invoice.line_ids.filtered(
                lambda l: l.account_id.id == partner_account and l.reconciled
            )
            lines_to_unreconcile.remove_move_reconcile()

        if self.payment_type == 'receive_money':
            debit_vals = self.get_debit_move_line(partner_account)
            credit_vals = self.get_credit_move_line(pdc_account)
        else:
            debit_vals = self.get_debit_move_line(pdc_account)
            credit_vals = self.get_credit_move_line(partner_account)

        label = 'PDC Payment :' + self.memo if self.memo else 'PDC Payment'
        debit_vals['name'] = label
        credit_vals['name'] = label

        move_vals = self.get_move_vals(debit_vals, credit_vals)

        total_residual = sum(self.invoice_ids.mapped('amount_residual'))
        if self.invoice_ids and total_residual != 0:
            move_id = self.env['account.move'].create(move_vals)
            move_id.action_post()

        self.write({'state': 'bounced'})

    # ------------------------------------------------------------------ #
    # action_done                                                          #
    # Creates: Dr Bank / Cr PDC Receivable (full cheque amount)           #
    # Reconciles PDC account line from action_register with this entry.   #
    # ------------------------------------------------------------------ #
    def action_done(self):
        self.check_payment_amount()
        pdc_account = self.check_pdc_account()

        bank_account = (
            self.journal_id.default_account_id.id
            if self.journal_id.default_account_id
            else False
        )

        if self.payment_type == 'receive_money':
            debit_vals = self.get_debit_move_line(bank_account)
            credit_vals = self.get_credit_move_line(pdc_account)
        else:
            debit_vals = self.get_debit_move_line(pdc_account)
            credit_vals = self.get_credit_move_line(bank_account)

        label = 'PDC Payment :' + self.memo if self.memo else 'PDC Payment'
        debit_vals.update({'name': label, 'partner_id': self.partner_id.id})
        credit_vals.update({'name': label, 'partner_id': self.partner_id.id})

        move_vals = self.get_move_vals(debit_vals, credit_vals)
        move_id = self.env['account.move'].create(move_vals)
        move_id.action_post()

        # Reconcile PDC account lines: register entry ↔ done entry
        if self.deposited_debit and self.deposited_credit:
            dep_pdc_line = (
                self.deposited_debit
                if self.deposited_debit.account_id.id == pdc_account
                else self.deposited_credit
            )
            done_pdc_line = move_id.line_ids.filtered(
                lambda l: l.account_id.id == pdc_account and not l.reconciled
            )[:1]
            if done_pdc_line and not dep_pdc_line.reconciled:
                (dep_pdc_line + done_pdc_line).reconcile()
        else:
            # No linked invoices — PDC account lines still need clearing
            pass

        self.write({'state': 'done', 'done_date': date.today()})

    # ------------------------------------------------------------------ #
    # action_cancel                                                        #
    # ------------------------------------------------------------------ #
    def action_cancel(self):
        self.action_delete_related_moves()
        op = self.company_id.pdc_operation_type
        if op == 'cancel':
            self.write({'state': 'cancel'})
        elif op == 'cancel_draft':
            self.write({'state': 'draft'})
        elif op == 'cancel_delete':
            self.write({'state': 'draft'})
            self.unlink()

    # Multi-action helpers
    def action_pdc_cancel(self):
        self.action_delete_related_moves()
        self.write({'state': 'cancel'})

    def action_pdc_cancel_draft(self):
        self.action_delete_related_moves()
        self.write({'state': 'draft'})

    def action_pdc_cancel_delete(self):
        self.action_delete_related_moves()
        self.write({'state': 'draft'})
        self.unlink()

    # ------------------------------------------------------------------ #
    # _sync_allocation_lines                                               #
    # Builds / reconciles allocation lines from real persisted invoice_ids #
    # ------------------------------------------------------------------ #
    def _sync_allocation_lines(self):
        """
        Called after create() and write() once invoice_ids have real DB IDs.
        - Removes lines whose invoice is no longer in invoice_ids.
        - Adds lines for newly added invoices (pre-filled from outstanding balance,
          capped at the remaining cheque amount).
        - Never touches amounts the user already saved.
        """
        for rec in self:
            invoice_ids_set = set(rec.invoice_ids.ids)
            existing = {line.invoice_id.id: line for line in rec.allocation_ids if line.invoice_id}

            # Remove stale lines
            stale = rec.allocation_ids.filtered(
                lambda l: l.invoice_id and l.invoice_id.id not in invoice_ids_set
            )
            if stale:
                stale.unlink()

            # Compute how much is already spoken for by existing lines
            already = sum(
                l.allocated_amount for l in rec.allocation_ids
                if l.invoice_id and l.invoice_id.id in invoice_ids_set
            )
            remaining = max((rec.payment_amount or 0.0) - already, 0.0)

            # Add missing lines
            for inv in rec.invoice_ids:
                if inv.id not in existing:
                    alloc = min(inv.amount_residual, remaining)
                    remaining -= alloc
                    self.env['pdc.invoice.allocation'].create({
                        'pdc_id': rec.id,
                        'invoice_id': inv.id,
                        'allocated_amount': alloc,
                    })

    # ------------------------------------------------------------------ #
    # create override                                                      #
    # ------------------------------------------------------------------ #
    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            payment_type = vals.get('payment_type')
            if payment_type == 'receive_money':
                vals['name'] = self.env['ir.sequence'].next_by_code('pdc.payment.customer')
            elif payment_type == 'send_money':
                vals['name'] = self.env['ir.sequence'].next_by_code('pdc.payment.vendor')

        records = super().create(vals_list)

        for rec in records:
            if rec.attachment_ids:
                rec.attachment_ids.write({'res_id': rec.id})

        # Build allocation lines now that invoice_ids have real DB IDs
        records._sync_allocation_lines()

        return records

    def write(self, vals):
        result = super().write(vals)
        # Re-sync allocation lines whenever invoice_ids changes
        if 'invoice_ids' in vals:
            self._sync_allocation_lines()
        return result

    # ------------------------------------------------------------------ #
    # action_delete_related_moves                                          #
    # FIX #9: use ORM unlink() — no raw SQL                               #
    # ------------------------------------------------------------------ #
    def action_delete_related_moves(self):
        for rec in self:
            move_ids = self.env['account.move'].search([('pdc_id', '=', rec.id)])
            for move in move_ids:
                if move.state == 'posted':
                    move.button_draft()
                move.line_ids.remove_move_reconcile()
                move.line_ids.unlink()
            move_ids.unlink()   # FIX #9: ORM unlink, no raw SQL
            rec.sudo().write({'done_date': False})

    def action_set_draft(self):
        self.sudo().write({'state': 'draft'})

    # ------------------------------------------------------------------ #
    # Multi-action state transitions (from list view)                     #
    # ------------------------------------------------------------------ #
    def _get_active_models(self):
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')
        if not active_ids:
            raise UserError("No records selected.")
        return self.env[active_model].browse(active_ids)

    def action_state_register(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if states != {'draft'}:
            raise UserError("Only Draft state PDC cheques can be moved to Registered.")
        records.action_register()

    def action_state_return(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if states != {'registered'}:
            raise UserError("Only Registered state PDC cheques can be returned.")
        records.action_returned()

    def action_state_deposit(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if not states.issubset({'registered', 'returned', 'bounced'}):
            raise UserError("Only Registered, Returned and Bounced cheques can be Deposited.")
        records.action_deposited()

    def action_state_bounce(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if states != {'deposited'}:
            raise UserError("Only Deposited state PDC cheques can be Bounced.")
        records.action_bounced()

    def action_state_done(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if states != {'deposited'}:
            raise UserError("Only Deposited state PDC cheques can be moved to Done.")
        records.action_done()

    def action_state_cancel(self):
        records = self._get_active_models()
        states = set(records.mapped('state'))
        if not states.issubset({'registered', 'returned', 'bounced'}):
            raise UserError("Only Registered, Returned and Bounced cheques can be Cancelled.")
        records.action_cancel()

    # ------------------------------------------------------------------ #
    # CRON: Customer due-date notifications                               #
    # FIX #8: use self.env instead of request (request is None in crons)  #
    # ------------------------------------------------------------------ #
    @api.model
    def notify_customer_due_date(self):
        if not self.env.company.is_cust_due_notify:
            return

        company = self.env.company
        notify_dates = set()
        for attr in ('notify_on_1', 'notify_on_2', 'notify_on_3', 'notify_on_4', 'notify_on_5'):
            days = getattr(company, attr)
            if days:
                notify_dates.add(fields.Date.today() + timedelta(days=-int(days)))

        if not notify_dates:
            return

        emails = [
            u.partner_id.email
            for u in company.sh_user_ids
            if u.partner_id and u.partner_id.email
        ]
        email_values = {'email_to': ','.join(emails)}

        # FIX #8: use self.env to get base_url — no request object
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        view = self.env.ref("jm_pdc.sh_pdc_payment_form_view", raise_if_not_found=False)
        view_id = view.id if view else 0

        records = self.search([('payment_type', '=', 'receive_money')])
        for record in records:
            if record.due_date not in notify_dates:
                continue

            if company.is_notify_to_customer:
                tmpl = self.env.ref('jm_pdc.sh_pdc_company_to_customer_notification_1')
                tmpl.send_mail(record.id, notif_layout='mail.mail_notification_light', force_send=True)

            if company.is_notify_to_user and company.sh_user_ids:
                url = "{}/web#id={}&model=pdc.wizard&view_type=form&view_id={}".format(
                    base_url, record.id, view_id)
                ctx = {'customer_url': url}
                tmpl = self.env.ref('jm_pdc.sh_pdc_company_to_int_user_notification_1')
                tmpl.with_context(ctx).send_mail(
                    record.id, email_values=email_values,
                    notif_layout='mail.mail_notification_light', force_send=True)

    # ------------------------------------------------------------------ #
    # CRON: Vendor due-date notifications                                 #
    # FIX #7: use the correct vendor notification template                #
    # FIX #8: use self.env instead of request                             #
    # ------------------------------------------------------------------ #
    @api.model
    def notify_vendor_due_date(self):
        if not self.env.company.is_vendor_due_notify:
            return

        company = self.env.company
        notify_dates = set()
        for attr in ('notify_on_1_vendor', 'notify_on_2_vendor', 'notify_on_3_vendor',
                     'notify_on_4_vendor', 'notify_on_5_vendor'):
            days = getattr(company, attr)
            if days:
                notify_dates.add(fields.Date.today() + timedelta(days=-int(days)))

        if not notify_dates:
            return

        emails = [
            u.partner_id.email
            for u in company.sh_user_ids_vendor
            if u.partner_id and u.partner_id.email
        ]
        email_values = {'email_to': ','.join(emails)}

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        view = self.env.ref("jm_pdc.sh_pdc_payment_form_view", raise_if_not_found=False)
        view_id = view.id if view else 0

        records = self.search([('payment_type', '=', 'send_money')])
        for record in records:
            if record.due_date not in notify_dates:
                continue

            if company.is_notify_to_vendor:
                # FIX #7: use the vendor-specific template
                tmpl = self.env.ref('jm_pdc.sh_pdc_company_to_vendor_notification_1')
                tmpl.send_mail(record.id, notif_layout='mail.mail_notification_light', force_send=True)

            if company.is_notify_to_user_vendor and company.sh_user_ids_vendor:
                url = "{}/web#id={}&model=pdc.wizard&view_type=form&view_id={}".format(
                    base_url, record.id, view_id)
                ctx = {'customer_url': url}
                tmpl = self.env.ref('jm_pdc.sh_pdc_company_to_int_user_notification_1')
                tmpl.with_context(ctx).send_mail(
                    record.id, email_values=email_values,
                    notif_layout='mail.mail_notification_light', force_send=True)
