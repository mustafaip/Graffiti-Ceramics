# -*- coding: utf-8 -*-
import base64
from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Override action_confirm to transfer all SO attachments to linked
        Manufacturing Orders and Subcontracting Orders upon confirmation.
        """
        result = super().action_confirm()

        for order in self:
            # Fetch all attachments on this SO
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
            ])

            if not attachments:
                continue

            # Find all MOs linked to this SO via procurement/stock moves
            productions = self.env['mrp.production'].search([
                ('sale_id', '=', order.id),
            ])

            # If sale_id field doesn't exist on mrp.production in this version,
            # fall back to searching via move origin
            if not productions:
                productions = self.env['mrp.production'].search([
                    ('origin', 'like', order.name),
                ])

            for production in productions:
                copied = self._copy_attachments_to(
                    attachments=attachments,
                    res_model='mrp.production',
                    res_id=production.id,
                )
                if copied:
                    production.message_post(
                        body=_(
                            '<b>%(count)d design document(s) transferred from '
                            '<a href="/odoo/sales/%(so_id)d">%(so_name)s</a></b><br/>'
                            'The following files were automatically attached from the Sales Order:<br/>'
                            '%(file_list)s'
                        ) % {
                            'count': len(copied),
                            'so_id': order.id,
                            'so_name': order.name,
                            'file_list': ''.join(
                                '<li>%s</li>' % a.name for a in copied
                            ),
                        },
                        subtype_id=self.env.ref('mail.mt_note').id,
                    )

        return result

    def _copy_attachments_to(self, attachments, res_model, res_id):
        """
        Copy a recordset of ir.attachment to a new res_model/res_id.
        Tags each copy with is_so_design_doc = True.
        Returns the newly created attachment records.
        """
        created = self.env['ir.attachment']

        for attachment in attachments:
            # Read raw binary data
            attachment_data = base64.b64decode(attachment.datas) if attachment.datas else b''

            new_attachment = self.env['ir.attachment'].create({
                'name': attachment.name,
                'datas': base64.b64encode(attachment_data).decode() if attachment_data else False,
                'res_model': res_model,
                'res_id': res_id,
                'mimetype': attachment.mimetype,
                'description': attachment.description,
                'is_so_design_doc': True,
            })
            created |= new_attachment

        return created
