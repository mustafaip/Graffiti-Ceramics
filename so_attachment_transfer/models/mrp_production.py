# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    so_design_doc_count = fields.Integer(
        string='Design Documents',
        compute='_compute_so_design_doc_count',
    )

    def _compute_so_design_doc_count(self):
        for production in self:
            production.so_design_doc_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'mrp.production'),
                ('res_id', '=', production.id),
                ('is_so_design_doc', '=', True),
            ])

    def action_view_so_design_docs(self):
        """Open the list of transferred SO design documents."""
        self.ensure_one()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'mrp.production'),
            ('res_id', '=', self.id),
            ('is_so_design_doc', '=', True),
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Design Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', attachments.ids)],
            'context': {
                'default_res_model': 'mrp.production',
                'default_res_id': self.id,
            },
        }
