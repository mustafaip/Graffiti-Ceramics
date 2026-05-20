{
    "name": "Post Dated Cheque Management",
    "author": "Nexera Innovations",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": (
        "Post-Dated Cheque Management, Manage Post-Dated Cheques App, "
        "View Vendor Invoice PDCs, List of Customer PDC Payments, "
        "Track Client PDC Processes, Register Vendor Post-Dated Cheques Module, "
        "Print Vendor PDC Reports, Print Customer PDC Reports in Odoo."
    ),
    "description": """
        In invoicing and billing, a Post-Dated Cheque (PDC) refers to a cheque issued
        by a customer or vendor (payer) with a future date.
        This module enables efficient management of post-dated cheques along with their
        corresponding accounting journal entries. Cheques can be moved through stages —
        Draft, Registered, Returned, Deposited, Bounced, and Done — with each stage
        automatically generating the appropriate journal entries.
        Per-invoice allocation lets you specify exactly how much of a cheque applies
        to each outstanding invoice.
    """,
    "images": ["static/description/banner.png"],
    "depends": [
        "account",
        "account_reports",
    ],
    "data": [
        "data/ir_sequence.xml",
        "data/account_data.xml",
        "data/ir_cron_cust.xml",
        "data/ir_cron_ven.xml",
        "data/mail_templates.xml",
        "security/ir.model.access.csv",
        "security/pdc_security.xml",
        "security/report_payment_pdc.xml",
        "views/res_config_settings_views.xml",
        "wizard/pdc_payment_wizard_views.xml",
        "wizard/pdc_multi_action_views.xml",
        "wizard/partner_wizard_views.xml",
        "views/views.xml",
        "report/pdc_wizard.xml",
        "report/report_action.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "jm_pdc/static/src/scss/pdc_form.scss",
        ],
    },
    "application": True,
    "auto_install": False,
    "installable": True,
    "price": 5.89,
    "currency": "USD",
}
