# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class FinanceFiscalInutilizeWizard(models.TransientModel):
    _name = "finance.fiscal.inutilize.wizard"
    _description = "Inutilize Number Range Wizard"

    number_from = fields.Integer(string="From", required=True)
    number_to = fields.Integer(string="To", required=True)
    justification = fields.Char(string="Justification", required=True)

    def action_confirm(self):
        self.ensure_one()
        msg = _("Number range %s-%s inutilized. Justification: %s") % (self.number_from, self.number_to, self.justification)
        self.env["mail.message"].create({
            "body": msg,
            "model": "res.company",
            "res_id": self.env.company.id,
        })
