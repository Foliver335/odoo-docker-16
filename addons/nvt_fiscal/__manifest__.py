# -*- coding: utf-8 -*-
{
    "name": "NVT Fiscal (Odoo 16)",
    "summary": "Finance module to issue Brazilian Nota Fiscal (NFe/NFS-e) with provider adapters.",
    "version": "16.0.1.0.0",
    "author": "NVT / Felipe Fause",
    "license": "LGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["base", "mail", "account"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "data/mail_templates.xml",

        # >>> Ordem importa: root + actions primeiro
        "views/fiscal_document_views.xml",
        # <<<

        "views/fiscal_settings_views.xml",
        "views/fiscal_wizard_views.xml",
        "report/report_actions.xml",
        "views/report_templates.xml"
    ],
    "qweb": [],
    "application": True,
    "installable": True
}
