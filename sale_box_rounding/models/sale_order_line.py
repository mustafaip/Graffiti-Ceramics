# -*- coding: utf-8 -*-
from odoo import api, fields, models

from . import box_math

# Writing any of these can change the box maths.
BOX_TRIGGER_FIELDS = {'product_uom_qty', 'box_qty', 'piece_qty', 'product_id', 'product_uom_id'}
# Which field the user actually typed -> which driver the maths starts from.
DRIVERS = (('product_uom_qty', 'qty'), ('box_qty', 'boxes'), ('piece_qty', 'pieces'))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    piece_qty = fields.Integer(
        string='Pieces', copy=True,
        help='Boxes x Pieces per Box. You can type it: it is rounded up '
             'to whole boxes.')
    box_qty = fields.Integer(
        string='Boxes', copy=True,
        help='Whole boxes. The quantity (SQM) is always rounded up to '
             'Boxes x SQM per Box. You can type it directly.')
    box_conversion_active = fields.Boolean(compute='_compute_box_conversion_active')

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @api.model
    def _box_is_active(self, product, uom):
        """Rounding applies only to a real product line that has both
        factors AND is sold in the product's own unit (SQM)."""
        return bool(
            product
            and product.sqm_per_piece > 0
            and product.pieces_per_box > 0
            and (not uom or uom == product.uom_id)
        )

    @api.model
    def _box_values(self, product, uom, driver, value):
        """{'product_uom_qty', 'box_qty', 'piece_qty'} or {} (nothing to do)."""
        if not self._box_is_active(product, uom):
            return {}
        res = box_math.normalize(
            driver, value, product.sqm_per_piece, product.pieces_per_box,
            qty_digits=self.env['decimal.precision'].precision_get('Product Unit'))
        if not res:
            return {}
        return {
            'product_uom_qty': res['qty'],
            'box_qty': res['boxes'],
            'piece_qty': res['pieces'],
        }

    def _box_sync_from_qty(self):
        """Re-round saved lines from their current quantity (used after a
        product / unit change or when a line was created without a quantity)."""
        for line in self:
            if line.display_type:
                continue
            if line._box_is_active(line.product_id, line.product_uom_id):
                vals = line._box_values(
                    line.product_id, line.product_uom_id, 'qty', line.product_uom_qty)
            else:
                vals = {'box_qty': 0, 'piece_qty': 0}
            vals = {k: v for k, v in vals.items() if line[k] != v}
            if vals:
                line.with_context(skip_box_rounding=True).write(vals)

    # ------------------------------------------------------------------
    # computes / onchanges (live feedback in the form)
    # ------------------------------------------------------------------
    @api.depends('product_id', 'product_uom_id', 'display_type')
    def _compute_box_conversion_active(self):
        for line in self:
            line.box_conversion_active = (
                not line.display_type
                and line._box_is_active(line.product_id, line.product_uom_id))

    def _box_apply_onchange(self, driver, value):
        for line in self:
            if line.box_conversion_active:
                vals = line._box_values(line.product_id, line.product_uom_id, driver, value)
            else:
                vals = {'box_qty': 0, 'piece_qty': 0} if (line.box_qty or line.piece_qty) else {}
            changed = {k: v for k, v in vals.items() if line[k] != v}
            if changed:
                line.update(changed)

    @api.onchange('product_id', 'product_uom_id', 'product_uom_qty')
    def _onchange_box_from_qty(self):
        for line in self:
            line._box_apply_onchange('qty', line.product_uom_qty)

    @api.onchange('box_qty')
    def _onchange_box_qty(self):
        for line in self:
            line._box_apply_onchange('boxes', line.box_qty)

    @api.onchange('piece_qty')
    def _onchange_piece_qty(self):
        for line in self:
            line._box_apply_onchange('pieces', line.piece_qty)

    # ------------------------------------------------------------------
    # server side (API, imports, quotation templates, copies...)
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        skip = self.env.context.get('skip_box_rounding')
        needs_sync = []
        for vals in vals_list:
            if skip or vals.get('display_type') or not vals.get('product_id'):
                needs_sync.append(False)
                continue
            product = self.env['product.product'].browse(vals['product_id'])
            uom = (self.env['uom.uom'].browse(vals['product_uom_id'])
                   if vals.get('product_uom_id') else product.uom_id)
            driver = next(((d, vals[f]) for f, d in DRIVERS if f in vals), None)
            if driver:
                vals.update(self._box_values(product, uom, *driver))
                needs_sync.append(False)
            else:
                needs_sync.append(True)  # quantity comes from Odoo's default
        lines = super().create(vals_list)
        lines.filtered(lambda l: needs_sync[lines.ids.index(l.id)])._box_sync_from_qty()
        return lines

    def write(self, vals):
        if self.env.context.get('skip_box_rounding') or not BOX_TRIGGER_FIELDS & vals.keys():
            return super().write(vals)
        driver = next(((d, vals[f]) for f, d in DRIVERS if f in vals), None)
        if not driver:
            # product / unit changed only: let Odoo recompute, then re-round.
            res = super().write(vals)
            self._box_sync_from_qty()
            return res
        res = True
        for line in self:
            product = (self.env['product.product'].browse(vals['product_id'])
                       if vals.get('product_id') else line.product_id)
            uom = (self.env['uom.uom'].browse(vals['product_uom_id'])
                   if vals.get('product_uom_id') else line.product_uom_id)
            line_vals = dict(vals, **self._box_values(product, uom, *driver))
            res &= super(SaleOrderLine, line).write(line_vals)
        return res
