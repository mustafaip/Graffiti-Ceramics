# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    include_images = fields.Boolean(
        string='Include Images',
        default=False,
        help='When ticked, Product Image and Product Design will appear in the quotation PDF for this line.',
    )
