# -*- coding: utf-8 -*-
from odoo import fields, models


class BaselinkerSyncLog(models.Model):
    _name = 'impl.baselinker.sync.log'
    _description = 'BaseLinker Sync Log'
    _order = 'create_date desc'

    backend_id = fields.Many2one(
        'impl.baselinker.backend', string="Backend",
        required=True, ondelete='cascade', index=True,
    )
    sync_type = fields.Selection([
        ('orders', 'Orders'),
        ('products', 'Products'),
    ], string="Type", required=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('error', 'Error'),
    ], string="Status", required=True)
    records_synced = fields.Integer(string="Synced")
    records_failed = fields.Integer(string="Failed")
    error_message = fields.Text(string="Error Details")
    duration = fields.Float(string="Duration (s)")
