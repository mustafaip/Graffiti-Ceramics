# -*- coding: utf-8 -*-
{
    'name': "Sentos Connector – Odoo Marketplace Integration",

    'summary': """Seamless integration between Odoo and Sentos to synchronize products, inventory, orders, and marketplace status in real time.
               🌐 Supported Marketplaces & Platforms: 
               Major Marketplaces: Trendyol – Hepsiburada - n11 - Amazon - ÇiçekSepeti - Boyner - LC Waikiki - Farmazon - EpttAVM - Koçtaş - Teknosa - ToptanTR - Turkcell Pasaj - Akakçe - Cimri - Beymen - Idefix - Pazarama
               eCommerce Platforms: Shopify - WooCommerce - Opencart - Ticimax - IdeaSoft - İkas
               Supports Turkish e-Fatura
               Supported Shipping Companies: Yurtiçi Kargo - DHL eCommerce - Aras Kargo - Sürat Kargo - UPS Kargo - PTT Kargo - Sendeo - Net Kargo - Amazon Easy Ship""",

    'description': """
    Sentos Connector is a powerful Odoo integration module that connects your Odoo ERP with the Sentos platform, enabling full automation of marketplace operations from a single system.

This module is designed for businesses operating in retail and wholesale, especially those selling through multiple online marketplaces such as Trendyol and other Sentos-connected channels. It eliminates manual work, reduces errors, and ensures accurate data synchronization between Odoo and Sentos.

🚀 Key Features

Product Synchronization

Export Odoo products to Sentos

Sync product details, prices, and categories

Activate and deactivate products automatically

Inventory & Stock Sync

Real-time stock updates from Odoo to Sentos

Prevent overselling across multiple marketplaces

Order Management

Import marketplace orders from Sentos into Odoo

Automatic customer and sales order creation

Centralized order tracking and processing

Marketplace Status Control

Manage product availability per marketplace

Update product and shop status directly from Odoo

API-Based Integration

Secure and scalable Sentos API connection

Designed for high-volume transactions

Multi-Company & Multi-Warehouse Ready

Supports complex Odoo environments

Ideal for businesses with multiple branches

🎯 Benefits

Centralize all marketplace operations inside Odoo

Save time by automating product and order workflows

Improve stock accuracy and customer satisfaction

Reduce operational errors and manual data entry

Scale your eCommerce business with confidence

🧩 Use Cases

Companies selling on Trendyol via Sentos

Businesses managing multiple marketplaces

Retailers and wholesalers using Odoo as their main ERP

Saudi and regional eCommerce businesses looking for automation

🔧 Technical Notes

Built with Odoo best practices

Easy to extend and customize

Suitable for production environments

🌐 Supported Marketplaces & Platforms
Major Marketplaces

Trendyol – Popular Turkish marketplace

Hepsiburada – Turkey’s largest marketplace

n11 – Leading marketplace in Turkey

Amazon – Global eCommerce platform (supports multiple country stores)

ÇiçekSepeti – Gifts and lifestyle marketplace

Boyner – Fashion & lifestyle marketplace

LC Waikiki – Apparel marketplace

Farmazon – Pharmacy‑focused marketplace

EpttAVM – General marketplace in Turkey

Koçtaş – Home improvement & DIY marketplace

Teknosa – Electronics marketplace

ToptanTR – B2B wholesale platform

Turkcell Pasaj – Telecom‑linked marketplace

Akakçe – Price comparison marketplace

Cimri – ECommerce & comparison platform

Beymen – Luxury fashion marketplace

Idefix – Book & media marketplace

Pazarama – General marketplace

eCommerce Platforms (via Sentos integrations)

Shopify

WooCommerce

Opencart

Ticimax

IdeaSoft

İkas

Supported Shipping Companies: Yurtiçi Kargo - DHL eCommerce - Aras Kargo - Sürat Kargo - UPS Kargo - PTT Kargo - Sendeo - Net Kargo - Amazon Easy Ship
    """,

    'author': "Boraq-Group",
    'website': "https://boraq-group.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Connector',
    'version': '18.1',

    # any module necessary for this one to work correctly
    'images': ['static/description/banner.jpeg'],
    'depends': ['base'],
    'application': True,
    'installable': True,
    'license': 'AGPL-3',
}

