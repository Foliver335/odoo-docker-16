# -*- coding: utf-8 -*-
from odoo import api, fields, models

class FinanceFiscalDocumentLine(models.Model):
    _name = "finance.fiscal.document.line"
    _description = "Fiscal Document Line"
    _order = "sequence, id"

    document_id = fields.Many2one("finance.fiscal.document", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one("product.product", string="Product/Service")
    name = fields.Char(string="Description", required=True)
    quantity = fields.Float(string="Qty", default=1.0)
    price_unit = fields.Float(string="Unit Price", default=0.0)
    price_subtotal = fields.Monetary(string="Subtotal", currency_field="currency_id", compute="_compute_subtotal", store=True)
    tax_percent = fields.Float(string="Tax (%)", default=0.0, help="Simple percent to simulate ICMS/PIS/COFINS sum.")
    tax_amount = fields.Monetary(string="Tax Amount", currency_field="currency_id", compute="_compute_subtotal", store=True)
    currency_id = fields.Many2one(related="document_id.currency_id", store=True, readonly=True)

    @api.depends("quantity", "price_unit", "tax_percent")
    def _compute_subtotal(self):
        for rec in self:
            subtotal = (rec.quantity or 0.0) * (rec.price_unit or 0.0)
            tax = subtotal * ((rec.tax_percent or 0.0) / 100.0)
            rec.price_subtotal = subtotal
            rec.tax_amount = tax
