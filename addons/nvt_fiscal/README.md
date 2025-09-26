# NVT Fiscal (Odoo 16)

Módulo criado em Odoo 16, inclui:
- Documento fiscal, itens, totais, XML, DANFE (QWeb).
- **Adapters**: Arquivo de testes, **SEFAZ NFe (básico)** e **NFS-e Brasília (ABRASF-like)**.
- Configurações em `res.config.settings`: ambiente, provedor e credenciais.

> Adapters reais exigem certificados A1, assinatura XML, SOAP/REST e XSDs oficiais.
> Este módulo já deixa **pontos de extensão** e um fluxo de homologação funcional.

**Necessário**
É extremamente necessário o regisgtro de um **certificado eletronico A1** para gerar as notas fiscais.

