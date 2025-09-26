# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions

class FinanceFiscalDocument(models.Model):
    _name = "finance.fiscal.document"
    _description = "Fiscal Document (Nota Fiscal)"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Number", readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("transmitted", "Transmitted"),
        ("authorized", "Authorized"),
        ("denied", "Denied"),
        ("canceled", "Canceled"),
    ], default="draft", tracking=True, index=True)

    operation_type = fields.Selection([
        ("out", "Output (Sale)"),
        ("in", "Input (Purchase)"),
    ], required=True, default="out", tracking=True)

    partner_id = fields.Many2one("res.partner", string="Partner", required=True, tracking=True)
    company_id = fields.Many2one("res.company", string="Company", required=True,
                                 default=lambda s: s.env.company, index=True)
    document_key = fields.Char(string="Access Key", copy=False, index=True)
    protocol_number = fields.Char(string="Protocol", copy=False)
    issue_date = fields.Datetime(string="Issue Date", default=fields.Datetime.now, required=True)

    line_ids = fields.One2many("finance.fiscal.document.line", "document_id", string="Lines")

    amount_untaxed = fields.Monetary(string="Amount Untaxed", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_tax = fields.Monetary(string="Taxes Total", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="Total", currency_field="currency_id", compute="_compute_amounts", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id, required=True)

    xml_file = fields.Binary(string="XML (NFe/NFS-e)", copy=False)
    xml_filename = fields.Char(string="XML Filename", copy=False)
    pdf_file = fields.Binary(string="PDF (DANFE)", copy=False)
    pdf_filename = fields.Char(string="PDF Filename", copy=False)

    last_message = fields.Text(string="Last Message", readonly=True)
    sefaz_status = fields.Char(string="SEFAZ/NFS-e Status", readonly=True)

    @api.depends("line_ids.price_subtotal", "line_ids.tax_amount")
    def _compute_amounts(self):
        for rec in self:
            untaxed = sum(rec.line_ids.mapped("price_subtotal"))
            tax = sum(rec.line_ids.mapped("tax_amount"))
            rec.amount_untaxed = untaxed
            rec.amount_tax = tax
            rec.amount_total = untaxed + tax

    def _ensure_lines(self):
        for rec in self:
            if not rec.line_ids:
                raise exceptions.UserError(_("Add at least one line before continuing."))

    def action_validate(self):
        self._ensure_lines()
        for rec in self:
            if rec.name:
                continue
            seq = self.env.ref("nvt_fiscal.seq_fiscal_document")
            rec.name = seq.next_by_id()
            rec.state = "validated"
            rec.message_post(body=_("Document validated."))

    def action_generate_xml(self):
        self._ensure_lines()
        for rec in self:
            xml_bytes, fname = rec._build_xml_base()  # base XML (genérico)
            rec.xml_file = xml_bytes
            rec.xml_filename = fname
            rec.message_post(body=_("XML generated: %s") % fname)

    def action_transmit(self):
        self._ensure_lines()
        self.action_generate_xml()
        adapter = self.env["finance.fiscal.provider.adapter"]._get_adapter()
        for rec in self:
            try:
                res = adapter.send_document(rec)
                rec.sefaz_status = res.get("status")
                rec.protocol_number = res.get("protocol")
                rec.document_key = res.get("access_key")
                rec.last_message = res.get("message")
                rec.state = "authorized" if res.get("authorized") else "denied"
                if res.get("pdf"):
                    rec.pdf_file = res["pdf"]["content"]
                    rec.pdf_filename = res["pdf"]["filename"]
                if res.get("xml"):  # permitir que o provedor substitua XML assinado
                    rec.xml_file = res["xml"]["content"]
                    rec.xml_filename = res["xml"]["filename"]
            except Exception:
                rec.state = "validated"
                raise

    def action_cancel(self):
        view = self.env.ref("nvt_fiscal.view_fiscal_cancel_wizard")
        return {
            "type": "ir.actions.act_window",
            "name": _("Cancel Fiscal Document"),
            "res_model": "finance.fiscal.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_id": self.id},
            "views": [(view.id, "form")],
        }

    def action_inutilize(self):
        view = self.env.ref("nvt_fiscal.view_fiscal_inutilize_wizard")
        return {
            "type": "ir.actions.act_window",
            "name": _("Inutilize Number Range"),
            "res_model": "finance.fiscal.inutilize.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {},
            "views": [(view.id, "form")],
        }

    def _build_xml_base(self):
        import base64
        from lxml import etree
        for rec in self:
            root = etree.Element("FiscalDocument")
            etree.SubElement(root, "Number").text = rec.name or ""
            etree.SubElement(root, "OperationType").text = rec.operation_type or ""
            etree.SubElement(root, "Partner").text = rec.partner_id.display_name or ""
            etree.SubElement(root, "IssueDate").text = fields.Datetime.to_string(rec.issue_date)
            totals = etree.SubElement(root, "Totals")
            etree.SubElement(totals, "Untaxed").text = "%.2f" % (rec.amount_untaxed or 0.0)
            etree.SubElement(totals, "Tax").text = "%.2f" % (rec.amount_tax or 0.0)
            etree.SubElement(totals, "Total").text = "%.2f" % (rec.amount_total or 0.0)
            lines = etree.SubElement(root, "Lines")
            for line in rec.line_ids:
                n = etree.SubElement(lines, "Line")
                etree.SubElement(n, "Product").text = line.name or ""
                etree.SubElement(n, "Qty").text = str(line.quantity or 0.0)
                etree.SubElement(n, "PriceUnit").text = "%.6f" % (line.price_unit or 0.0)
                etree.SubElement(n, "SubTotal").text = "%.2f" % (line.price_subtotal or 0.0)
                etree.SubElement(n, "Tax").text = "%.2f" % (line.tax_amount or 0.0)
            xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            fname = (rec.name or "document").replace("/", "_") + ".xml"
            return (base64.b64encode(xml_bytes), fname)

    def action_print_danfe(self):
        self.ensure_one()
        return self.env.ref("nvt_fiscal.action_report_danfe").report_action(self)
