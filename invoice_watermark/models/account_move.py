# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_watermark = fields.Selection(
        selection=[
            ('none',   'None'),
            ('cash',   'Cash'),
            ('credit', 'Credit'),
        ],
        string='Payment Watermark',
        default='none',
        help=(
            'Select the watermark that will be printed diagonally across '
            'the background of the invoice PDF.\n'
            '• None   – no watermark (default)\n'
            '• Cash   – stamps "CASH" in green\n'
            '• Credit – stamps "CREDIT" in blue'
        ),
    )
