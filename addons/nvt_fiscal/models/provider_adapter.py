# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64

class FinanceFiscalProviderAdapter(models.Model):
    _name = "finance.fiscal.provider.adapter"
    _description = "Fiscal Provider Adapter"
    _rec_name = "name"

    name = fields.Char(default="Adapter Dispatcher", readonly=True)

    @api.model
    def _get_adapter(self):
        ICP = self.env["ir.config_parameter"].sudo()
        provider = ICP.get_param("nvt_fiscal.fiscal_provider_code", "dummy")
        if provider == "sefaz_nfe":
            return self.env["finance.fiscal.provider.sefaz_nfe"]
        if provider == "nfse_brasilia":
            return self.env["finance.fiscal.provider.nfse_brasilia"]
        return self.env["finance.fiscal.provider.dummy"]

class FinanceFiscalProviderDummy(models.Model):
    _name = "finance.fiscal.provider.dummy"
    _description = "Dummy Fiscal Provider"
    _rec_name = "name"

    name = fields.Char(default="Dummy Provider", readonly=True)

    @api.model
    def send_document(self, document):
        env = self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.fiscal_environment", "homolog")
        total = document.amount_total or 0.0
        authorized = total > 0 and env in ("homolog", "prod")
        access_key = "DUMMY-%s" % (document.name or "NOSEQ")
        protocol = "PROT-%s" % (document.name or "NOSEQ")
        message = _("Authorized in %s") % env if authorized else _("Denied: total must be > 0")
        html = "<html><body><h3>DANFE (Dummy)</h3><p>Number: %s</p><p>Total: %.2f</p></body></html>" % (document.name or "", total)
        pdf_like = base64.b64encode(html.encode("utf-8"))
        return {
            "authorized": authorized,
            "status": "100" if authorized else "301",
            "access_key": access_key,
            "protocol": protocol,
            "message": message,
            "pdf": {"filename": "%s_DANFE.pdf" % (document.name or "document"), "content": pdf_like},
        }

class FinanceFiscalProviderSefazNFe(models.Model):
    _name = "finance.fiscal.provider.sefaz_nfe"
    _description = "SEFAZ NFe Provider (basic flow)"
    _rec_name = "name"

    name = fields.Char(default="SEFAZ NFe", readonly=True)

    @api.model
    def _build_nfe_xml(self, document):
        from lxml import etree
        # **Simplified** NFe-like XML (NOT official schema)
        nfe = etree.Element("NFe")
        inf = etree.SubElement(nfe, "infNFe", Id=f"NFe{document.name or ''}", versao="4.00")
        ide = etree.SubElement(inf, "ide")
        etree.SubElement(ide, "cUF").text = (self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.sefaz_uf") or "")[:2]
        etree.SubElement(ide, "mod").text = "55"
        etree.SubElement(ide, "serie").text = "1"
        etree.SubElement(ide, "nNF").text = (document.name or "0").split("/")[-1]
        dets = etree.SubElement(inf, "detalhes")
        for line in document.line_ids:
            det = etree.SubElement(dets, "det")
            etree.SubElement(det, "xProd").text = line.name or ""
            etree.SubElement(det, "qCom").text = str(line.quantity or 0.0)
            etree.SubElement(det, "vUnCom").text = "%.6f" % (line.price_unit or 0.0)
        total = etree.SubElement(inf, "total")
        etree.SubElement(total, "vNF").text = "%.2f" % (document.amount_total or 0.0)
        xml = etree.tostring(nfe, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        return xml

    @api.model
    def send_document(self, document):
        env = self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.fiscal_environment", "homolog")
        xml = self._build_nfe_xml(document)
        # In homolog, we simulate authorization:
        authorized = (document.amount_total or 0) > 0
        access_key = "NFe-%s" % (document.name or "NOSEQ")
        protocol = "SEFAZ-%s" % (document.name or "NOSEQ")
        message = _("NFe %s") % ("authorized (homolog)" if authorized else "denied")
        return {
            "authorized": authorized,
            "status": "100" if authorized else "301",
            "access_key": access_key,
            "protocol": protocol,
            "message": message,
            "xml": {"filename": "%s.xml" % (access_key), "content": base64.b64encode(xml)},
            "pdf": {"filename": "%s_DANFE.pdf" % (document.name or "document"), "content": base64.b64encode(b"<pdf placeholder>")},
        }

class FinanceFiscalProviderNFSeBrasilia(models.Model):
    _name = "finance.fiscal.provider.nfse_brasilia"
    _description = "NFS-e Brasília Provider (ABRASF-like, basic)"
    _rec_name = "name"

    name = fields.Char(default="NFS-e Brasília", readonly=True)

    @api.model
    def _build_nfse_rps_xml(self, document):
        from lxml import etree
        rps = etree.Element("ConsultarLoteRpsEnvio")  # placeholder op
        # Minimal ABRASF-like structure (NOT official schema)
        lote = etree.SubElement(rps, "LoteRps")
        etree.SubElement(lote, "NumeroLote").text = (document.name or "1").replace("/", "")
        etree.SubElement(lote, "Cnpj").text = (self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.company_cnpj") or "")
        etree.SubElement(lote, "InscricaoMunicipal").text = (self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.nfse_cmc") or "")
        etree.SubElement(lote, "QuantidadeRps").text = "1"
        lista = etree.SubElement(lote, "ListaRps")
        nrps = etree.SubElement(lista, "Rps")
        inf = etree.SubElement(nrps, "InfRps")
        etree.SubElement(inf, "Numero").text = (document.name or "1").replace("/", "")
        etree.SubElement(inf, "Serie").text = "UN"
        etree.SubElement(inf, "Tipo").text = "1"
        servico = etree.SubElement(inf, "Servico")
        vServ = etree.SubElement(servico, "Valores")
        etree.SubElement(vServ, "ValorServicos").text = "%.2f" % (document.amount_total or 0.0)
        etree.SubElement(servico, "ItemListaServico").text = "1.05"
        tomador = etree.SubElement(inf, "Tomador")
        ide = etree.SubElement(tomador, "IdentificacaoTomador")
        nilo = etree.SubElement(ide, "CpfCnpj")
        etree.SubElement(nilo, "Cnpj").text = (self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.company_cnpj") or "")
        etree.SubElement(tomador, "RazaoSocial").text = document.partner_id.name or ""
        xml = etree.tostring(rps, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        return xml

    @api.model
    def send_document(self, document):
        env = self.env["ir.config_parameter"].sudo().get_param("nvt_fiscal.fiscal_environment", "homolog")
        xml = self._build_nfse_rps_xml(document)
        # Homolog: simular protocolo e número da NFS-e
        authorized = (document.amount_total or 0) > 0
        access_key = "NFSe-%s" % (document.name or "NOSEQ")
        protocol = "BRASILIA-%s" % (document.name or "NOSEQ")
        message = _("NFS-e %s") % ("authorized (homolog)" if authorized else "denied")
        return {
            "authorized": authorized,
            "status": "100" if authorized else "301",
            "access_key": access_key,
            "protocol": protocol,
            "message": message,
            "xml": {"filename": "%s.xml" % (access_key), "content": base64.b64encode(xml)},
            "pdf": {"filename": "%s_RPS.pdf" % (document.name or "document"), "content": base64.b64encode(b"<pdf placeholder>")},
        }
