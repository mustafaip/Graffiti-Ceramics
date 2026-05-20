# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    design_image = fields.Image(
        string='Product Design',
        max_width=1024,
        max_height=1024,
        help='Design drawing or technical image shown on quotation PDF when enabled per order line.',
    )
