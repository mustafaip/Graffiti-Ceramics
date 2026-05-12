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
            'Watermark printed on the invoice PDF.\n'
            'Auto-detected from payment journal when the invoice is paid.\n'
            'Can be overridden manually at any time.\n\n'
            '  Cash   = all payments made via a Cash journal\n'
            '  Credit = any non-cash or mixed payment\n'
            '  None   = invoice not yet paid (default)'
        ),
    )

    @api.depends(
        'payment_state',
        'line_ids.matched_debit_ids.debit_move_id.move_id.journal_id.type',
        'line_ids.matched_credit_ids.credit_move_id.move_id.journal_id.type',
    )
    def _compute_payment_watermark(self):
        for move in self:
            # Only auto-detect on customer invoices
            if move.move_type != 'out_invoice':
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # If not paid at all, do not overwrite a manual selection
            if move.payment_state in ('not_paid', 'reversed', 'cancelled'):
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # Gather all journals from matched payments
            journal_types = set()

            for line in move.line_ids:
                # Payments that came IN to this invoice (credits matched)
                for matched in line.matched_credit_ids:
                    journal = matched.credit_move_id.move_id.journal_id
                    if journal:
                        journal_types.add(journal.type)
                # Payments that went OUT (debits matched — e.g. refunds)
                for matched in line.matched_debit_ids:
                    journal = matched.debit_move_id.move_id.journal_id
                    if journal:
                        journal_types.add(journal.type)

            if not journal_types:
                # Paid state but no matched lines found — keep existing value
                if not move.payment_watermark:
                    move.payment_watermark = 'none'
                continue

            # All journals are cash → CASH, anything else → CREDIT
            if journal_types == {'cash'}:
                move.payment_watermark = 'cash'
            else:
                move.payment_watermark = 'credit'
