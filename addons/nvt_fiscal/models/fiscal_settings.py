# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Ambiente e provedor
    fiscal_environment = fields.Selection(
        [("homolog", "Homologation"), ("prod", "Production")],
        string="Fiscal Environment",
        default="homolog",
        config_parameter="nvt_fiscal.fiscal_environment",
    )
    fiscal_provider_code = fields.Selection(
        [
            ("dummy", "Dummy"),
            ("sefaz_nfe", "SEFAZ NFe"),
            ("nfse_brasilia", "NFS-e Brasília"),
        ],
        string="Fiscal Provider",
        default="dummy",
        config_parameter="nvt_fiscal.fiscal_provider_code",
    )

    # Comuns
    csc_token = fields.Char(string="CSC/Token", config_parameter="nvt_fiscal.csc_token")
    csc_id = fields.Char(string="CSC/ID", config_parameter="nvt_fiscal.csc_id")
    company_cnpj = fields.Char(string="Company CNPJ", config_parameter="nvt_fiscal.company_cnpj")

    # SEFAZ NFe
    sefaz_uf = fields.Char(string="SEFAZ UF", config_parameter="nvt_fiscal.sefaz_uf")

    # ATENÇÃO: Binary NÃO pode usar config_parameter em res.config.settings no Odoo 16.
    a1_certificate = fields.Binary(string="A1 Certificate (PFX/P12)")
    a1_certificate_filename = fields.Char(string="A1 File Name", config_parameter="nvt_fiscal.a1_certificate_filename")
    a1_certificate_password = fields.Char(string="A1 Password", config_parameter="nvt_fiscal.a1_certificate_password")
    a1_certificate_attachment_id = fields.Many2one(
        "ir.attachment", string="A1 Attachment (internal ref)", readonly=True
    )

    # NFS-e Brasília
    nfse_cmc = fields.Char(string="CMC", config_parameter="nvt_fiscal.nfse_cmc")
    nfse_login = fields.Char(string="NFS-e Login", config_parameter="nvt_fiscal.nfse_login")
    nfse_password = fields.Char(string="NFS-e Password", config_parameter="nvt_fiscal.nfse_password")
    nfse_municipality_code = fields.Char(string="Municipality Code", config_parameter="nvt_fiscal.nfse_municipality_code")

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()

        # Recupera ID do anexo do certificado (se houver)
        attach_id_str = ICP.get_param("nvt_fiscal.a1_certificate_attachment_id")
        attach = False
        if attach_id_str and attach_id_str.isdigit():
            att = self.env["ir.attachment"].sudo().browse(int(attach_id_str))
            attach = att if att.exists() else False

        res.update(
            fiscal_environment=ICP.get_param("nvt_fiscal.fiscal_environment", "homolog"),
            fiscal_provider_code=ICP.get_param("nvt_fiscal.fiscal_provider_code", "dummy"),
            csc_token=ICP.get_param("nvt_fiscal.csc_token"),
            csc_id=ICP.get_param("nvt_fiscal.csc_id"),
            company_cnpj=ICP.get_param("nvt_fiscal.company_cnpj"),
            sefaz_uf=ICP.get_param("nvt_fiscal.sefaz_uf"),
            # Por segurança, não repopular o binário do certificado ao abrir a tela
            a1_certificate=False,
            a1_certificate_filename=ICP.get_param("nvt_fiscal.a1_certificate_filename"),
            a1_certificate_password=ICP.get_param("nvt_fiscal.a1_certificate_password"),
            nfse_cmc=ICP.get_param("nvt_fiscal.nfse_cmc"),
            nfse_login=ICP.get_param("nvt_fiscal.nfse_login"),
            nfse_password=ICP.get_param("nvt_fiscal.nfse_password"),
            nfse_municipality_code=ICP.get_param("nvt_fiscal.nfse_municipality_code"),
            a1_certificate_attachment_id=attach.id if attach else False,
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        for rec in self:
            # Persiste filename e senha sempre
            ICP.set_param("nvt_fiscal.a1_certificate_filename", rec.a1_certificate_filename or "")
            ICP.set_param("nvt_fiscal.a1_certificate_password", rec.a1_certificate_password or "")

            # Se o usuário enviou um novo arquivo A1, salva/atualiza como anexo
            if rec.a1_certificate:
                attach_vals = {
                    "name": rec.a1_certificate_filename or "a1_certificate.pfx",
                    "type": "binary",
                    "datas": rec.a1_certificate,  # base64
                    "mimetype": "application/x-pkcs12",
                    "res_model": "res.company",
                    "res_id": self.env.company.id,
                }
                old_id_str = ICP.get_param("nvt_fiscal.a1_certificate_attachment_id")
                attach = False
                if old_id_str and old_id_str.isdigit():
                    old = self.env["ir.attachment"].sudo().browse(int(old_id_str))
                    if old.exists():
                        old.sudo().write(attach_vals)
                        attach = old
                if not attach:
                    attach = self.env["ir.attachment"].sudo().create(attach_vals)

                # Guarda apenas a referência do anexo em ir.config_parameter
                ICP.set_param("nvt_fiscal.a1_certificate_attachment_id", str(attach.id))
