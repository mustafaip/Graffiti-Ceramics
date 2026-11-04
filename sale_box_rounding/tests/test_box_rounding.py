# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged

from odoo.addons.sale_box_rounding.models import box_math


@tagged('post_install', '-at_install')
class TestBoxRounding(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Customer'})
        cls.tile = cls.env['product.product'].create({
            'name': 'Tile', 'type': 'consu', 'list_price': 10.0,
            'sqm_per_piece': 0.72, 'pieces_per_box': 2,
        })
        cls.plain = cls.env['product.product'].create({
            'name': 'Plain', 'type': 'consu', 'list_price': 10.0,
        })

    def _so(self, product, **line_vals):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, dict(product_id=product.id, **line_vals))],
        })

    def test_math_example(self):
        res = box_math.normalize('qty', 50, 0.72, 2)
        self.assertEqual(res, {'qty': 50.4, 'boxes': 35, 'pieces': 70})

    def test_math_exact_multiple_not_bumped(self):
        self.assertEqual(box_math.normalize('qty', 50.4, 0.72, 2)['boxes'], 35)

    def test_create_rounds_up(self):
        line = self._so(self.tile, product_uom_qty=50).order_line
        self.assertEqual(line.box_qty, 35)
        self.assertEqual(line.piece_qty, 70)
        self.assertAlmostEqual(line.product_uom_qty, 50.4)

    def test_write_qty(self):
        line = self._so(self.tile, product_uom_qty=1.44).order_line
        line.product_uom_qty = 3
        self.assertEqual((line.box_qty, line.piece_qty), (3, 6))
        self.assertAlmostEqual(line.product_uom_qty, 4.32)

    def test_write_boxes_and_pieces(self):
        line = self._so(self.tile, product_uom_qty=1).order_line
        line.box_qty = 10
        self.assertAlmostEqual(line.product_uom_qty, 14.4)
        self.assertEqual(line.piece_qty, 20)
        line.piece_qty = 7  # 7 pieces -> 4 boxes -> 8 pieces
        self.assertEqual(line.box_qty, 4)
        self.assertEqual(line.piece_qty, 8)
        self.assertAlmostEqual(line.product_uom_qty, 5.76)

    def test_product_without_factors_untouched(self):
        line = self._so(self.plain, product_uom_qty=50).order_line
        self.assertEqual(line.product_uom_qty, 50)
        self.assertEqual((line.box_qty, line.piece_qty), (0, 0))

    def test_default_quantity_line(self):
        line = self._so(self.tile).order_line  # no quantity -> Odoo default 1
        self.assertEqual(line.box_qty, 1)
        self.assertAlmostEqual(line.product_uom_qty, 1.44)
