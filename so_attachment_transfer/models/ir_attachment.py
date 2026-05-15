# -*- coding: utf-8 -*-
from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_so_design_doc = fields.Boolean(
        string='SO Design Document',
        default=False,
        help='Marks attachments that were transferred from a Sales Order to an MO or Subcontracting Order.',
    )
