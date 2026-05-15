# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Design Documents',
        compute='_compute_so_attachment_ids',
    )

    @api.depends('name')
    def _compute_so_attachment_ids(self):
        """Fetch all ir.attachment records linked to this SO."""
        for order in self:
            order.so_attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
            ])

    def action_confirm(self):
        result = super().action_confirm()

        for order in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
            ])

            if not attachments:
                continue

            # Find MOs linked to this SO — try sale_id first, fallback to origin
            productions = self.env['mrp.production'].search([
                ('sale_id', '=', order.id),
            ])
            if not productions:
                productions = self.env['mrp.production'].search([
                    ('origin', 'like', order.name),
                ])

            for production in productions:
                copied = order._copy_attachments_to(
                    attachments=attachments,
                    res_model='mrp.production',
                    res_id=production.id,
                )
                if copied:
                    file_list = ''.join('<li>%s</li>' % a.name for a in copied)
                    production.message_post(
                        body=_(
                            '<b>%(count)d design document(s) transferred from '
                            '<a href="/odoo/sales/%(so_id)d">%(so_name)s</a></b>'
                            '<br/>Files attached:<ul>%(file_list)s</ul>'
                        ) % {
                            'count': len(copied),
                            'so_id': order.id,
                            'so_name': order.name,
                            'file_list': file_list,
                        },
                        subtype_id=self.env.ref('mail.mt_note').id,
                    )

        return result

    def _copy_attachments_to(self, attachments, res_model, res_id):
        """Copy attachments to target model/id, tagging each as is_so_design_doc."""
        created = self.env['ir.attachment']
        for att in attachments:
            new_att = self.env['ir.attachment'].create({
                'name': att.name,
                'datas': att.datas,
                'res_model': res_model,
                'res_id': res_id,
                'mimetype': att.mimetype,
                'description': att.description,
                'is_so_design_doc': True,
            })
            created |= new_att
        return created
