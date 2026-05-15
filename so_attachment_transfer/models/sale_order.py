# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_design_doc_count = fields.Integer(
        string='Design Documents',
        compute='_compute_so_design_doc_count',
    )

    @api.depends('name')
    def _compute_so_design_doc_count(self):
        for order in self:
            order.so_design_doc_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('is_so_design_doc', '=', True),
            ])

    def action_view_so_design_docs(self):
        self.ensure_one()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
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
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
                'default_is_so_design_doc': True,
            },
        }

    def action_confirm(self):
        result = super().action_confirm()
        for order in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('is_so_design_doc', '=', True),
            ])
            if not attachments:
                continue

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

    def _get_so_design_attachments(self):
        self.ensure_one()
        return self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('is_so_design_doc', '=', True),
        ])

    def _get_attachment_images(self, attachment):
        """
        Return a list of base64-encoded PNG strings for the given attachment.
        - For images: returns a single entry
        - For PDFs: converts each page to a PNG using pdf2image (poppler)
        - For other types: returns empty list
        """
        mimetype = attachment.mimetype or ''
        raw = attachment.datas

        if not raw:
            return []

        raw_bytes = base64.b64decode(raw)

        if 'image' in mimetype:
            return [raw.decode('utf-8') if isinstance(raw, bytes) else raw]

        if 'pdf' in mimetype:
            try:
                from pdf2image import convert_from_bytes
                pages = convert_from_bytes(raw_bytes, dpi=150)
                result = []
                for page in pages:
                    buf = io.BytesIO()
                    page.save(buf, format='PNG')
                    result.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
                return result
            except Exception:
                return []

        return []
