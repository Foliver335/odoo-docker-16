# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class FinanceFiscalCancelWizard(models.TransientModel):
    _name = "finance.fiscal.cancel.wizard"
    _description = "Cancel Fiscal Document Wizard"

    document_id = fields.Many2one("finance.fiscal.document", required=True)
    reason = fields.Char(string="Reason", required=True)

    def action_confirm(self):
        self.ensure_one()
        doc = self.document_id
        if doc.state not in ("authorized", "transmitted", "validated"):
            return
        doc.state = "canceled"
        doc.last_message = _("Canceled: %s") % (self.reason or "")
        doc.message_post(body=doc.last_message)
