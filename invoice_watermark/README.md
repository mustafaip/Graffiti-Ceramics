# Invoice Payment Watermark
### Odoo 19 Community Edition — Custom Module

---

## Overview

This module adds a **"CASH"** or **"CREDIT"** diagonal watermark to the background of customer invoice PDFs in Odoo 19 Community.

---

## Features

- Dropdown field on the customer invoice form: **None / Cash / Credit**
- Watermark appears **only in the printed PDF** — not in the web UI
- `CASH` renders in a subtle **dark green**
- `CREDIT` renders in a subtle **dark red**
- Watermark is diagonal (−45°), large, and semi-transparent so invoice data remains fully readable
- Only visible on **customer invoices** (`out_invoice`); hidden on bills, credit notes, etc.
- No external images or assets required — pure CSS/QWeb

---

## Installation

1. Copy the `invoice_watermark` folder into your Odoo addons directory:
   ```
   /path/to/odoo/addons/invoice_watermark/
   ```

2. Restart the Odoo server:
   ```bash
   ./odoo-bin -c your.conf -u invoice_watermark
   ```

3. Activate **Developer Mode** in Odoo settings.

4. Go to **Apps → Update Apps List**, then search for **"Invoice Payment Watermark"** and click **Install**.

---

## Usage

1. Open any **Customer Invoice** (`Accounting → Customers → Invoices`).
2. Locate the **"Payment Watermark"** dropdown field (near the Payment Reference field).
3. Select **Cash** or **Credit** (or leave as **None** for no watermark).
4. Save the invoice, then **Print** or **Preview** the PDF.

---

## Module Structure

```
invoice_watermark/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── account_move.py          ← Adds payment_watermark field
├── views/
│   └── account_move_views.xml   ← Injects dropdown into invoice form
├── report/
│   └── invoice_report.xml       ← Injects CSS watermark into PDF template
└── README.md
```

---

## Technical Notes

| Item | Detail |
|------|--------|
| Odoo Version | 19.0 Community |
| Depends | `account` |
| Field | `account.move.payment_watermark` (Selection) |
| Report | Inherits `account.report_invoice_document` |
| Rendering | Inline CSS via QWeb (`position: fixed`, `transform: rotate(-45deg)`) |
| PDF Engine | Compatible with `wkhtmltopdf` (Odoo default) |

---

## Customization

To adjust watermark appearance, edit `report/invoice_report.xml`:

- **Opacity**: Change `opacity: 0.10` (lower = more transparent)
- **Font size**: Change `font-size: 130px`
- **Colors**: Modify `.watermark-cash` and `.watermark-credit` color values
- **Rotation angle**: Change `transform: rotate(-45deg)`
