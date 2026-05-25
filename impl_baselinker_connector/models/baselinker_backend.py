# -*- coding: utf-8 -*-
import json
import logging
import time

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

BL_API_URL = 'https://api.baselinker.com/connector.php'
BL_API_TIMEOUT = 60
BL_ORDERS_PAGE_SIZE = 100  # BaseLinker returns max 100 orders per call


class BaselinkerBackend(models.Model):
    _name = 'impl.baselinker.backend'
    _description = 'BaseLinker Backend'

    name = fields.Char(default='BaseLinker', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company, required=True,
    )
    api_token = fields.Char(
        string="API Token",
        help="BaseLinker API token (My Account \u2192 API).",
        groups='base.group_system',
    )

    # --- Sync settings ---
    sync_orders = fields.Boolean(string="Sync Orders", default=True)
    sync_products = fields.Boolean(string="Sync Products", default=False)
    use_net_price = fields.Boolean(
        string="Use Net Prices", default=True,
        help="Import net (excl. tax) prices calculated from gross price and "
             "tax rate. If disabled, gross prices are used and taxes are "
             "cleared on order lines to prevent double-taxation.",
    )
    auto_confirm_orders = fields.Boolean(
        string="Auto-confirm Sales Orders", default=False,
        help="Automatically confirm imported sales orders.",
    )
    default_currency_code = fields.Char(
        string="Default Currency", default='EUR',
        help="Fallback currency code when order currency is not recognized.",
    )
    shipping_product_code = fields.Char(
        string="Shipping Product Code", default='SHIPPING',
        help="Internal reference of the service product for shipping charges.",
    )
    default_tax_id = fields.Many2one(
        'account.tax', string="Default Tax",
        domain=[('type_tax_use', '=', 'sale')],
        help="Fallback sale tax applied to imported order lines when "
             "importing net prices.  Leave empty to use product defaults.",
    )

    # --- State ---
    last_order_sync_ts = fields.Integer(
        string="Last Order Sync Timestamp",
        default=0, readonly=True, copy=False,
    )
    last_order_sync_date = fields.Datetime(
        string="Last Order Sync", readonly=True, copy=False,
    )
    last_product_sync_date = fields.Datetime(
        string="Last Product Sync", readonly=True, copy=False,
    )
    total_orders_synced = fields.Integer(
        string="Total Orders Synced", readonly=True, copy=False,
    )
    total_products_synced = fields.Integer(
        string="Total Products Synced", readonly=True, copy=False,
    )

    # --- Logs ---
    sync_log_ids = fields.One2many(
        'impl.baselinker.sync.log', 'backend_id', string="Sync Logs",
    )

    # =========================================================================
    # BaseLinker API
    # =========================================================================

    def _bl_call(self, method, params=None):
        """Call the BaseLinker REST API."""
        self.ensure_one()
        token = self.api_token
        if not token:
            raise UserError(_("BaseLinker API token is not configured."))
        try:
            resp = requests.post(
                BL_API_URL,
                headers={'X-BLToken': token},
                data={
                    'method': method,
                    'parameters': json.dumps(params or {}),
                },
                timeout=BL_API_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise UserError(
                _("BaseLinker API request failed: %s") % str(e)
            ) from e

        data = resp.json()
        if data.get('status') != 'SUCCESS':
            error_msg = (
                data.get('error_message')
                or data.get('error_code')
                or str(data)
            )
            raise UserError(_("BaseLinker API error: %s") % error_msg)
        return data

    # =========================================================================
    # UI Actions
    # =========================================================================

    def action_test_connection(self):
        """Test the BaseLinker API connection."""
        self.ensure_one()
        # Lightweight call: date far in future = empty result, validates token
        self._bl_call('getOrders', {'date_from': int(time.time())})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Connection successful"),
                'message': _("Successfully connected to BaseLinker API."),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_sync_orders_manual(self):
        """Manual order sync triggered from the UI."""
        self.ensure_one()
        self._sync_orders_impl()
        return self._notification_from_last_log(_("Order Sync"))

    def action_sync_products_manual(self):
        """Manual product sync triggered from the UI."""
        self.ensure_one()
        self._sync_products_impl()
        return self._notification_from_last_log(_("Product Sync"))

    def _notification_from_last_log(self, title):
        """Return a display_notification action reflecting the latest log."""
        latest = self.sync_log_ids[:1]
        if latest and latest.status == 'error':
            ntype = 'danger'
            msg = _("Sync failed. Check the sync logs for details.")
        elif latest and latest.status == 'partial':
            ntype = 'warning'
            msg = _("Sync completed with errors. Check the sync logs.")
        else:
            ntype = 'success'
            msg = _("Sync completed successfully.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': msg,
                'type': ntype,
                'sticky': ntype == 'danger',
            },
        }

    # =========================================================================
    # Cron entry points
    # =========================================================================

    @api.model
    def _cron_sync_orders(self):
        """Cron: sync orders for all active backends with sync_orders enabled."""
        backends = self.search([
            ('active', '=', True),
            ('sync_orders', '=', True),
        ])
        for backend in backends:
            try:
                backend._sync_orders_impl()
            except Exception:
                _logger.exception(
                    "BaseLinker order sync failed for backend %s",
                    backend.id,
                )

    @api.model
    def _cron_sync_products(self):
        """Cron: sync products for all active backends with sync_products enabled."""
        backends = self.search([
            ('active', '=', True),
            ('sync_products', '=', True),
        ])
        for backend in backends:
            try:
                backend._sync_products_impl()
            except Exception:
                _logger.exception(
                    "BaseLinker product sync failed for backend %s",
                    backend.id,
                )

    # =========================================================================
    # Order sync
    # =========================================================================

    def _sync_orders_impl(self):
        """Fetch new orders from BaseLinker and create Odoo sale.orders.

        Paginates automatically (BL returns max 100 per call).
        Never raises — all errors are captured into the sync log.
        """
        self.ensure_one()
        start_time = time.time()
        synced = 0
        failed = 0
        errors = []
        max_ts = self.last_order_sync_ts or 0

        try:
            date_from = max_ts

            while True:
                data = self._bl_call('getOrders', {
                    'date_from': date_from,
                })
                page_orders = data.get('orders', [])
                if not page_orders:
                    break

                for order_data in page_orders:
                    try:
                        self._import_single_order(order_data)
                        synced += 1
                        _logger.info(
                            "Imported BL order %s",
                            order_data.get('order_id'),
                        )
                    except _OrderSkipped:
                        pass  # dedup — already imported
                    except Exception as e:
                        failed += 1
                        msg = "Order %s: %s" % (
                            order_data.get('order_id', '?'), e,
                        )
                        errors.append(msg)
                        _logger.exception(
                            "Failed to import BL order: %s", msg,
                        )

                    # Track max timestamp regardless of outcome
                    for ts_key in ('date_confirmed', 'date_add',
                                   'last_change'):
                        ts_val = order_data.get(ts_key)
                        if ts_val:
                            max_ts = max(max_ts, int(ts_val))

                # Pagination: full page means there may be more
                if len(page_orders) < BL_ORDERS_PAGE_SIZE:
                    break
                # Advance cursor; guard against infinite loop when all
                # orders in the batch share the same timestamp.
                if max_ts <= date_from:
                    date_from = date_from + 1
                else:
                    date_from = max_ts

            # Persist state
            write_vals = {
                'last_order_sync_date': fields.Datetime.now(),
                'total_orders_synced': self.total_orders_synced + synced,
            }
            if max_ts > (self.last_order_sync_ts or 0):
                write_vals['last_order_sync_ts'] = max_ts
            self.write(write_vals)

        except UserError:
            raise
        except Exception as e:
            errors.append(str(e))
            _logger.exception("BaseLinker order sync error: %s", e)

        duration = time.time() - start_time
        status = (
            'success' if not errors
            else ('partial' if synced > 0 else 'error')
        )
        self._create_sync_log(
            'orders', status, synced, failed,
            '\n'.join(errors) if errors else '',
            duration,
        )

    def _import_single_order(self, order_data):
        """Import one BaseLinker order into Odoo.

        Raises ``_OrderSkipped`` for already-imported orders.
        """
        order_id = order_data.get('order_id')
        origin = "BL%s" % order_id

        # Dedup: check both origin and client_order_ref for safety
        existing = self.env['sale.order'].search([
            '|', ('origin', '=', origin),
                 ('client_order_ref', '=', str(order_id)),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if existing:
            raise _OrderSkipped(origin)

        # Partners
        partner_id = self._ensure_partner(order_data)
        shipping_partner_id = self._ensure_shipping_partner(
            order_data, partner_id,
        )

        so_vals = {
            'partner_id': partner_id,
            'origin': origin,
            'client_order_ref': str(order_id),
            'company_id': self.company_id.id,
        }
        if shipping_partner_id:
            so_vals['partner_shipping_id'] = shipping_partner_id

        # Currency
        currency_code = (
            order_data.get('currency')
            or self.default_currency_code
            or 'EUR'
        )
        currency = self.env['res.currency'].search(
            [('name', '=', currency_code.upper())], limit=1,
        )
        if currency:
            so_vals['currency_id'] = currency.id

        so = self.env['sale.order'].create(so_vals)

        # Order lines
        self._create_order_lines(so, order_data)

        # Shipping line
        delivery_price = float(order_data.get('delivery_price') or 0)
        if delivery_price > 0:
            self._add_shipping_line(so, delivery_price, order_data)

        # Auto-confirm
        if self.auto_confirm_orders:
            so.action_confirm()

    # =========================================================================
    # Product sync
    # =========================================================================

    def _sync_products_impl(self):
        """Fetch products from BaseLinker inventories and sync to Odoo."""
        self.ensure_one()
        start_time = time.time()
        synced = 0
        failed = 0
        errors = []

        try:
            # Step 1: get all inventories
            inv_data = self._bl_call('getInventories')
            inventories = inv_data.get('inventories', [])
            if not inventories:
                self._create_sync_log(
                    'products', 'success', 0, 0,
                    "No inventories found in BaseLinker.",
                    time.time() - start_time,
                )
                return

            for inventory in inventories:
                inv_id = inventory.get('inventory_id')
                if not inv_id:
                    continue

                try:
                    page = 1
                    while True:
                        # Step 2: list product IDs (paginated)
                        prod_list = self._bl_call(
                            'getInventoryProductsList', {
                                'inventory_id': inv_id,
                                'page': page,
                            },
                        )
                        products_map = prod_list.get('products', {})
                        if not products_map:
                            break

                        product_ids = list(products_map.keys())

                        # Step 3: get detailed data
                        prod_detail = self._bl_call(
                            'getInventoryProductsData', {
                                'inventory_id': inv_id,
                                'products': product_ids,
                            },
                        )
                        products_detail = prod_detail.get('products', {})

                        for prod_id, prod_info in products_detail.items():
                            try:
                                self._import_product(prod_info)
                                synced += 1
                            except Exception as e:
                                failed += 1
                                errors.append(
                                    "Product %s: %s" % (prod_id, e),
                                )
                                _logger.warning(
                                    "Failed to import product %s: %s",
                                    prod_id, e,
                                )

                        page += 1

                except Exception as e:
                    errors.append("Inventory %s: %s" % (inv_id, e))
                    _logger.exception(
                        "Failed to sync inventory %s: %s", inv_id, e,
                    )

            self.write({
                'last_product_sync_date': fields.Datetime.now(),
                'total_products_synced': self.total_products_synced + synced,
            })

        except UserError:
            raise
        except Exception as e:
            errors.append(str(e))
            _logger.exception("BaseLinker product sync error: %s", e)

        duration = time.time() - start_time
        status = (
            'success' if not errors
            else ('partial' if synced > 0 else 'error')
        )
        self._create_sync_log(
            'products', status, synced, failed,
            '\n'.join(errors) if errors else '',
            duration,
        )

    # =========================================================================
    # Partner helpers
    # =========================================================================

    def _ensure_partner(self, order_data):
        """Find or create a res.partner for the BaseLinker order
        (invoice / main contact)."""
        self.ensure_one()
        Partner = self.env['res.partner']
        email = (order_data.get('email') or '').strip() or False
        full_name = (
            order_data.get('invoice_fullname')
            or order_data.get('delivery_fullname')
            or email
            or 'BaseLinker Customer'
        ).strip()

        # Search by email first (most reliable dedup key)
        if email:
            partner = Partner.search([
                ('email', '=', email),
                ('company_id', 'in', [self.company_id.id, False]),
            ], limit=1)
            if partner:
                return partner.id

        # Fallback: search by name
        partner = Partner.search([
            ('name', '=', full_name),
            ('company_id', 'in', [self.company_id.id, False]),
        ], limit=1)
        if partner:
            return partner.id

        # Create new partner with invoice address
        vals = {
            'name': full_name,
            'email': email,
            'phone': order_data.get('phone') or '',
            'street': order_data.get('invoice_address') or '',
            'city': order_data.get('invoice_city') or '',
            'zip': order_data.get('invoice_postcode') or '',
            'customer_rank': 1,
            'company_id': self.company_id.id,
        }

        # Country
        country_code = (
            order_data.get('invoice_country_code') or ''
        ).upper()
        if country_code:
            country = self.env['res.country'].search(
                [('code', '=', country_code)], limit=1,
            )
            if country:
                vals['country_id'] = country.id

        # VAT
        vat = (order_data.get('invoice_nip') or '').strip()
        if vat:
            vals['vat'] = vat

        return Partner.create(vals).id

    def _ensure_shipping_partner(self, order_data, invoice_partner_id):
        """Create a child 'delivery' contact when the shipping address
        differs from the invoice address.  Returns partner id or False."""
        self.ensure_one()

        inv_name = (order_data.get('invoice_fullname') or '').strip()
        del_name = (order_data.get('delivery_fullname') or '').strip()
        inv_addr = (order_data.get('invoice_address') or '').strip()
        del_addr = (order_data.get('delivery_address') or '').strip()

        # No separate delivery info, or identical — skip
        if not del_name or (del_name == inv_name and del_addr == inv_addr):
            return False

        Partner = self.env['res.partner']

        # Reuse existing child contact
        existing = Partner.search([
            ('parent_id', '=', invoice_partner_id),
            ('type', '=', 'delivery'),
            ('name', '=', del_name),
            ('street', '=', del_addr),
        ], limit=1)
        if existing:
            return existing.id

        vals = {
            'parent_id': invoice_partner_id,
            'type': 'delivery',
            'name': del_name,
            'street': del_addr,
            'city': order_data.get('delivery_city') or '',
            'zip': order_data.get('delivery_postcode') or '',
            'phone': order_data.get('phone') or '',
            'company_id': self.company_id.id,
        }

        country_code = (
            order_data.get('delivery_country_code') or ''
        ).upper()
        if country_code:
            country = self.env['res.country'].search(
                [('code', '=', country_code)], limit=1,
            )
            if country:
                vals['country_id'] = country.id

        return Partner.create(vals).id

    # =========================================================================
    # Product helpers
    # =========================================================================

    def _ensure_product(self, sku, name, price):
        """Find a product by default_code (SKU) or create a new one."""
        self.ensure_one()
        Product = self.env['product.product']

        if sku:
            product = Product.search(
                [('default_code', '=', sku)], limit=1,
            )
            if product:
                return product.id

        # Create via template (Odoo auto-creates one product.product variant).
        # type='consu' = Goods in Odoo 17+.  In Odoo 18+ the stock module
        # auto-computes is_storable=True for type in ('consu', 'product'),
        # so inventory tracking works out of the box — do NOT set is_storable
        # manually (it is a computed readonly field).
        template = self.env['product.template'].create({
            'name': name or sku or 'Unknown Product',
            'default_code': sku or False,
            'type': 'consu',
            'list_price': float(price or 0),
            'sale_ok': True,
            'purchase_ok': True,
        })
        return template.product_variant_id.id

    @staticmethod
    def _calc_net_price(price_brutto, tax_rate):
        """Calculate net price from BaseLinker gross price and tax_rate.

        Special BL tax_rate values:
            -1    = exempt (ZW)
            -0.02 = NP annotation
            -0.03 = reverse charge (OO)
        """
        if tax_rate and tax_rate > 0:
            return price_brutto / (1.0 + tax_rate / 100.0)
        # Exempt / special / zero — net equals gross
        return price_brutto

    def _resolve_tax_for_line(self, line_vals):
        """Set tax_id on a SOL dict depending on pricing mode."""
        if not self.use_net_price:
            # Gross price import — clear taxes to prevent double-taxation
            line_vals['tax_id'] = [(5, 0, 0)]
        elif self.default_tax_id:
            # Net price import with explicit fallback tax
            line_vals['tax_id'] = [(6, 0, [self.default_tax_id.id])]
        # else: net price, no default tax → keep Odoo product defaults

    def _create_order_lines(self, sale_order, order_data):
        """Create sale.order.line records from BL order products."""
        self.ensure_one()
        SOLine = self.env['sale.order.line']

        for item in order_data.get('products', []):
            sku = (item.get('sku') or item.get('ean') or '').strip()
            name = item.get('name') or sku or 'Item'
            qty = float(item.get('quantity', 1))

            price_brutto = float(item.get('price_brutto') or 0)
            tax_rate = float(item.get('tax_rate') or 0)

            if self.use_net_price:
                price = self._calc_net_price(price_brutto, tax_rate)
            else:
                price = price_brutto

            product_id = self._ensure_product(sku, name, price)

            line_vals = {
                'order_id': sale_order.id,
                'name': name,
                'product_uom_qty': qty,
                'price_unit': price,
            }
            if product_id:
                line_vals['product_id'] = product_id

            self._resolve_tax_for_line(line_vals)
            SOLine.create(line_vals)

    def _add_shipping_line(self, sale_order, delivery_price, order_data):
        """Add a shipping charge line to the sale order."""
        self.ensure_one()
        Product = self.env['product.product']
        shipping_code = self.shipping_product_code or 'SHIPPING'

        product = Product.search(
            [('default_code', '=', shipping_code)], limit=1,
        )
        if not product:
            template = self.env['product.template'].create({
                'name': 'Shipping',
                'default_code': shipping_code,
                'type': 'service',
                'list_price': 0,
                'sale_ok': True,
                'purchase_ok': False,
            })
            product = template.product_variant_id

        delivery_method = order_data.get('delivery_method') or 'Shipping'
        line_vals = {
            'order_id': sale_order.id,
            'product_id': product.id if product else False,
            'name': delivery_method,
            'product_uom_qty': 1,
            'price_unit': delivery_price,
        }
        self._resolve_tax_for_line(line_vals)
        self.env['sale.order.line'].create(line_vals)

    def _import_product(self, prod_info):
        """Import or update a single product from BaseLinker inventory data."""
        self.ensure_one()
        Product = self.env['product.product']

        sku = (prod_info.get('sku') or prod_info.get('ean') or '').strip()
        if not sku:
            return

        # Name: BL inventory stores text fields in a nested dict
        name = ''
        text_fields = prod_info.get('text_fields', {})
        if isinstance(text_fields, dict):
            name = text_fields.get('name') or ''
        if not name:
            name = prod_info.get('name') or sku

        # Price: take first available price
        price = 0
        prices = prod_info.get('prices', {})
        if isinstance(prices, dict) and prices:
            price = float(next(iter(prices.values()), 0))

        weight = float(prod_info.get('weight') or 0)
        ean = (prod_info.get('ean') or '').strip()

        # Update existing
        existing = Product.search([('default_code', '=', sku)], limit=1)
        if existing:
            update_vals = {}
            if name:
                update_vals['name'] = name
            if weight:
                update_vals['weight'] = weight
            if ean and not existing.barcode:
                update_vals['barcode'] = ean
            if price:
                update_vals['list_price'] = price
            if update_vals:
                existing.product_tmpl_id.write(update_vals)
            return

        # Create new
        tmpl_vals = {
            'name': name,
            'default_code': sku,
            'type': 'consu',
            'list_price': price,
            'sale_ok': True,
            'purchase_ok': True,
        }
        if weight:
            tmpl_vals['weight'] = weight
        if ean:
            tmpl_vals['barcode'] = ean

        self.env['product.template'].create(tmpl_vals)

    # =========================================================================
    # Sync log
    # =========================================================================

    def _create_sync_log(self, sync_type, status, synced, failed,
                         error_msg, duration):
        """Create a sync log entry."""
        self.env['impl.baselinker.sync.log'].create({
            'backend_id': self.id,
            'sync_type': sync_type,
            'status': status,
            'records_synced': synced,
            'records_failed': failed,
            'error_message': error_msg or False,
            'duration': duration,
        })


class _OrderSkipped(Exception):
    """Raised internally when an order is already imported (dedup)."""
