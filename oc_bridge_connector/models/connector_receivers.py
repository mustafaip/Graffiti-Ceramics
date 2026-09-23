# -*- coding: utf-8 -*-
from odoo import models


class OcConnectorReceivers(models.AbstractModel):
    """One handler per synced model. Called by the /oc_connector/receive
    controller. Method naming convention: _oc_receive_<model_with_underscores>.
    """
    _inherit = 'oc.connector.mixin'

    # ---- ping (used by the Test Connection button - touches no real data) --
    def _oc_receive_ping(self, operation, data, remote_id):
        return 0

    # ---- res.partner (Enterprise -> Community) --------------------------
    def _oc_receive_res_partner(self, operation, data, remote_id):
        if operation == 'unlink':
            return self._oc_unlink_by_remote('res.partner', remote_id)

        match = data.get('_match_key', {})
        if match.get('vat'):
            domain = [('vat', '=', match['vat'])]
        elif match.get('email'):
            domain = [('email', '=', match['email'])]
        else:
            domain = [('name', '=', match.get('name'))]

        country = self.env['res.country'].sudo().search([('code', '=', data.get('country_code'))], limit=1)
        state = self.env['res.country.state'].sudo().search([('name', '=', data.get('state_name'))], limit=1)

        vals = {
            'name': data.get('name'),
            'is_company': data.get('is_company', False),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'street': data.get('street'),
            'street2': data.get('street2'),
            'city': data.get('city'),
            'zip': data.get('zip'),
            'country_id': country.id if country else False,
            'state_id': state.id if state else False,
            'vat': data.get('vat'),
            'ref': data.get('ref'),
        }
        return self.with_context(oc_connector_sync=True)._oc_find_or_create(
            'res.partner', domain, vals, remote_id)

    # ---- uom.uom (Enterprise -> Community) -------------------------------
    def _oc_receive_uom_uom(self, operation, data, remote_id):
        if operation == 'unlink':
            return self._oc_unlink_by_remote('uom.uom', remote_id)

        category = self.env['uom.category'].sudo().search([('name', '=', data.get('category_name'))], limit=1)
        if not category:
            category = self.env['uom.category'].sudo().create({'name': data.get('category_name')})

        domain = [('name', '=', data.get('name')), ('category_id', '=', category.id)]
        vals = {
            'name': data.get('name'),
            'category_id': category.id,
            'uom_type': data.get('uom_type') or 'reference',
            'factor': data.get('factor') or 1.0,
            'rounding': data.get('rounding') or 0.01,
            'active': data.get('active', True),
        }
        return self.with_context(oc_connector_sync=True)._oc_find_or_create(
            'uom.uom', domain, vals, remote_id)

    # ---- product.template (Enterprise -> Community) ----------------------
    def _oc_receive_product_template(self, operation, data, remote_id):
        if operation == 'unlink':
            return self._oc_unlink_by_remote('product.template', remote_id)

        uom = self.env['uom.uom'].sudo().search([('name', '=', data.get('uom_name'))], limit=1)
        domain = [('default_code', '=', data.get('default_code'))] if data.get('default_code') \
            else [('name', '=', data.get('name'))]

        vals = {
            'name': data.get('name'),
            'default_code': data.get('default_code'),
            'barcode': data.get('barcode'),
            'type': data.get('type') or 'consu',
            'list_price': data.get('list_price') or 0.0,
            'standard_price': data.get('standard_price') or 0.0,
            'sale_ok': data.get('sale_ok', True),
            'active': data.get('active', True),
        }
        if uom:
            vals['uom_id'] = uom.id
            vals['uom_po_id'] = uom.id

        return self.with_context(oc_connector_sync=True)._oc_find_or_create(
            'product.template', domain, vals, remote_id)

    # ---- product.pricelist (Enterprise -> Community) ----------------------
    def _oc_receive_product_pricelist(self, operation, data, remote_id):
        if operation == 'unlink':
            return self._oc_unlink_by_remote('product.pricelist', remote_id)

        currency = self.env['res.currency'].sudo().search([('name', '=', data.get('currency_name'))], limit=1)
        domain = [('name', '=', data.get('name'))]
        vals = {'name': data.get('name'), 'active': data.get('active', True)}
        if currency:
            vals['currency_id'] = currency.id

        local_id = self.with_context(oc_connector_sync=True)._oc_find_or_create(
            'product.pricelist', domain, vals, remote_id)

        pricelist = self.env['product.pricelist'].sudo().browse(local_id)
        pricelist.item_ids.unlink()
        Item = self.env['product.pricelist.item'].sudo()
        for item in data.get('items', []):
            product_tmpl = False
            if item.get('default_code'):
                product_tmpl = self.env['product.template'].sudo().search(
                    [('default_code', '=', item['default_code'])], limit=1)
            Item.create({
                'pricelist_id': pricelist.id,
                'applied_on': item.get('applied_on') or '3_global',
                'product_tmpl_id': product_tmpl.id if product_tmpl else False,
                'compute_price': item.get('compute_price') or 'fixed',
                'fixed_price': item.get('fixed_price') or 0.0,
                'percent_price': item.get('percent_price') or 0.0,
                'min_quantity': item.get('min_quantity') or 0,
            })
        return local_id

    # ---- sale.order (Community -> Enterprise) -----------------------------
    def _oc_receive_sale_order(self, operation, data, remote_id):
        match = data.get('partner_match', {})
        if match.get('vat'):
            partner_domain = [('vat', '=', match['vat'])]
        elif match.get('email'):
            partner_domain = [('email', '=', match['email'])]
        else:
            partner_domain = [('name', '=', match.get('name'))]

        partner = self.env['res.partner'].sudo().search(partner_domain, limit=1)
        if not partner:
            partner = self.env['res.partner'].sudo().create(
                {'name': match.get('name') or 'Unknown (from Community)'})

        vals = {
            'partner_id': partner.id,
            'client_order_ref': data.get('source_reference'),  # keeps Community's SO number visible
            'note': data.get('note'),
        }

        Order = self.env['sale.order'].sudo()
        local_id = self.env['oc.connector.mapping'].sudo().get_local_id('sale.order', remote_id)
        order = Order.browse(local_id) if local_id else Order.browse()
        if not order.exists():
            order = Order.search([('client_order_ref', '=', data.get('source_reference'))], limit=1)

        order_ctx = Order.with_context(oc_connector_sync=True)
        if order.exists():
            order = order_ctx.browse(order.id)
            order.write(vals)
            order.order_line.unlink()
        else:
            order = order_ctx.create(vals)

        Line = self.env['sale.order.line'].sudo().with_context(oc_connector_sync=True)
        for line in data.get('lines', []):
            product = False
            if line.get('default_code'):
                product = self.env['product.product'].sudo().search(
                    [('default_code', '=', line['default_code'])], limit=1)
            Line.create({
                'order_id': order.id,
                'product_id': product.id if product else False,
                'name': line.get('name'),
                'product_uom_qty': line.get('product_uom_qty') or 0.0,
                'price_unit': line.get('price_unit') or 0.0,
                'discount': line.get('discount') or 0.0,
            })

        self.env['oc.connector.mapping'].sudo().set_mapping(
            'sale.order', order.id, remote_id, direction='pull')
        return order.id

    # ---- shared helper ----------------------------------------------------
    def _oc_unlink_by_remote(self, model_name, remote_id):
        local_id = self.env['oc.connector.mapping'].sudo().get_local_id(model_name, remote_id)
        if local_id:
            self.env[model_name].sudo().browse(local_id).unlink()
        return False
