# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_watermark = fields.Selection(
        selection=[
            ('none',   'None'),
            ('cash',   'Cash'),
            ('credit', 'Credit'),
        ],
        string='PDF Watermark',
        compute='_compute_payment_watermark',
        store=True,
        readonly=False,
        copy=False,
        help=(
            'Watermark printed diagonally on the invoice PDF.\n\n'
            'Auto-detected from payment:\n'
            '  Cash journal                    -> CASH\n'
            '  Bank + Manual Payment           -> CASH\n'
            '  Bank + Credit/PDC               -> CREDIT\n'
            '  Mixed (any Credit/PDC present)  -> CREDIT\n\n'
            'Can be overridden manually at any time.'
        ),
    )

    @api.depends(
        'payment_state',
        'line_ids.matched_debit_ids.debit_move_id.move_id',
        'line_ids.matched_credit_ids.credit_move_id.move_id',
    )
    def _compute_payment_watermark(self):
        for move in self:

            # Only auto-detect on customer invoices
            if move.move_type != 'out_invoice':
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # If unpaid/cancelled, don't overwrite a manual selection
            if move.payment_state in ('not_paid', 'reversed', 'cancelled'):
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # Collect all payment moves linked to this invoice
            payment_moves = self.env['account.move']

            for line in move.line_ids:
                for matched in line.matched_credit_ids:
                    payment_moves |= matched.credit_move_id.move_id
                for matched in line.matched_debit_ids:
                    payment_moves |= matched.debit_move_id.move_id

            # Remove the invoice itself from the set
            payment_moves = payment_moves - move

            if not payment_moves:
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # Find account.payment records linked to those moves
            payments = self.env['account.payment'].search([
                ('move_id', 'in', payment_moves.ids)
            ])

            if not payments:
                # Fallback: judge by journal type alone if no payment record found
                journal_types = payment_moves.mapped('journal_id.type')
                if set(journal_types) == {'cash'}:
                    move.payment_watermark = 'cash'
                else:
                    move.payment_watermark = 'credit'
                continue

            # Vote on each payment
            votes = [self._vote_from_payment(p) for p in payments]

            # Any credit/PDC vote → CREDIT; all cash → CASH
            if 'credit' in votes:
                move.payment_watermark = 'credit'
            else:
                move.payment_watermark = 'cash'

    def _vote_from_payment(self, payment):
        """
        Determine CASH or CREDIT from a single account.payment record.

        Cash journal (any method)    → 'cash'
        Bank + Manual Payment        → 'cash'
        Bank + Credit/PDC            → 'credit'
        Bank + anything else         → 'cash'  (safe default)
        """
        journal = payment.journal_id
        if not journal:
            return 'cash'

        if journal.type == 'cash':
            return 'cash'

        if journal.type == 'bank':
            method_name = (payment.payment_method_id.name or '').lower()
            if 'credit' in method_name or 'pdc' in method_name:
                return 'credit'
            return 'cash'

        return 'cash'
