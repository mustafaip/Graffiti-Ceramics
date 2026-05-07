# -*- coding: utf-8 -*-
from odoo import models, fields


class IntercompanyFlowLog(models.Model):
    _name = 'intercompany.flow.log'
    _description = 'Intercompany Auto Flow Log'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, copy=False, index=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft', required=True, index=True)

    error_message = fields.Text(string='Error Detail')

    # ── Source ───────────────────────────────────────────────────────────────
    origin_sale_id = fields.Many2one(
        'sale.order', string='Origin Sale Order',
        help='The customer SO that triggered the intercompany flow.',
        ondelete='set null',
    )
    buying_company_id = fields.Many2one(
        'res.company', string='Buying Company',
        help='Company that needs the product (has no local stock).',
        required=True,
    )
    supplying_company_id = fields.Many2one(
        'res.company', string='Supplying Company',
        help='Company that has the product in stock.',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
    )
    product_qty = fields.Float(string='Quantity', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM')

    # ── Generated documents ──────────────────────────────────────────────────
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order (Buying Co.)',
        help='PO raised in the buying company towards the supplying company.',
        ondelete='set null',
    )
    intercompany_sale_id = fields.Many2one(
        'sale.order', string='Intercompany Sale Order (Supplying Co.)',
        help='SO raised in the supplying company to fulfil the PO.',
        ondelete='set null',
    )
    customer_invoice_id = fields.Many2one(
        'account.move', string='Customer Invoice (Supplying Co.)',
        help='Customer invoice posted in the supplying company.',
        ondelete='set null',
    )
    vendor_bill_id = fields.Many2one(
        'account.move', string='Vendor Bill (Buying Co.)',
        help='Vendor bill posted in the buying company.',
        ondelete='set null',
    )

    # ── Traceability ─────────────────────────────────────────────────────────
    # We store move counts rather than Many2many relations to avoid custom
    # SQL relation tables that conflict on reinstall after a failed attempt.
    stock_picking_out_count = fields.Integer(
        string='Outgoing Pickings', default=0,
        help='Number of stock pickings generated in the supplying company.',
    )
    stock_picking_in_count = fields.Integer(
        string='Incoming Pickings', default=0,
        help='Number of stock pickings generated in the buying company.',
    )

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or f'ICF-{rec.id}'

    def action_view_out_pickings(self):
        """Open outgoing pickings from the supplying company's SO."""
        self.ensure_one()
        if not self.intercompany_sale_id:
            return
        picking_ids = self.intercompany_sale_id.picking_ids.ids
        return {
            'name': 'Outgoing Pickings (Supplying Co.)',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids)],
        }

    def action_view_in_pickings(self):
        """Open incoming pickings from the buying company's PO."""
        self.ensure_one()
        if not self.purchase_order_id:
            return
        picking_ids = self.purchase_order_id.picking_ids.ids
        return {
            'name': 'Incoming Pickings (Buying Co.)',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids)],
        }
