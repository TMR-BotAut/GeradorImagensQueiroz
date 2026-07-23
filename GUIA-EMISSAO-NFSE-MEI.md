# Guia de Emissão de NFS-e para MEI — Queiroz Seguros

Guia prático de como emitir a **Nota Fiscal de Serviço eletrônica (NFS-e)** de um
MEI usando o **Sistema Nacional NFS-e** do gov.br.

> ⚠️ **Aviso**: este guia é orientativo. Regras de ISS, códigos de serviço e
> tributação variam por município e pela atividade. Confirme os detalhes fiscais
> com seu contador antes de emitir em produção.

---

## 1. O que é a NFS-e Nacional

Desde a adesão do país ao **Padrão Nacional da NFS-e**, o **MEI prestador de
serviço** emite suas notas pelo **Emissor Nacional** (gov.br), e não mais por
sistemas próprios de cada prefeitura. É gratuito e não exige certificado digital.

- **Portal**: https://www.nfse.gov.br
- **Emissor Web** (pelo navegador) e **App NFS-e Mobile** (Android/iOS)
- **Login**: conta **gov.br nível Prata ou Ouro**

---

## 2. Caminho recomendado para o MEI: Emissor Web (sem certificado)

Este é o jeito realista e imediato de emitir hoje.

### Passo 1 — Elevar a conta gov.br para Prata ou Ouro
A NFS-e exige nível Prata ou Ouro.
- Acesse https://www.gov.br → entrar → **Segurança da conta** → **Selo de
  confiabilidade**.
- Formas comuns de subir de nível: validação pelo **app gov.br**
  (reconhecimento facial), **banco credenciado** (internet banking), ou base do
  **INSS/servidor**.

### Passo 2 — Primeiro acesso ao Emissor Nacional
1. Acesse https://www.nfse.gov.br
2. Clique em **Emissor Web** (ou **Área do Contribuinte**).
3. Faça login com a conta **gov.br**.
4. Aceite o **Termo de Adesão** ao Emissor Nacional (aparece no 1º acesso).

### Passo 3 — Configurar o emitente (fazer uma vez)
No menu **Configurações**, preencha os dados do prestador:
- Regime de tributação: **Simples Nacional / MEI**.
- Serviço(s) que você presta (código da lista de serviços LC 116/2003).
  Para corretagem de seguros/planos, a atividade costuma se enquadrar em
  **10.01 – Agenciamento, corretagem ou intermediação** — **confirme com o
  contador** o código exato aplicável.
- Alíquota / retenção de ISS: para MEI, o ISS geralmente já está recolhido no
  **DAS** (valor fixo mensal), então normalmente marca-se como **não incidência
  / recolhido no DAS** — **confirme com o contador**.

### Passo 4 — Emitir a nota
1. No Emissor Web, clique em **Emitir NFS-e**.
2. **Tomador do serviço** (cliente): informe CPF/CNPJ, nome/razão social e
   endereço. Se for pessoa física sem CPF informado, é possível emitir sem
   identificar (consumidor).
3. **Serviço prestado**: selecione o código configurado e escreva a
   **descrição** (ex.: "Corretagem de plano de saúde — referência mês/ano").
4. **Valor do serviço**: informe o valor em R$.
5. Revise a prévia e clique em **Emitir**.
6. A NFS-e é gerada com número, chave de acesso e **DANFSe (PDF)** para enviar
   ao cliente.

### Passo 5 — App NFS-e Mobile (opcional)
Mesmo login gov.br, permite emitir e consultar notas pelo celular. Bom para
emissão rápida no dia a dia.

---

## 3. Boas práticas

- **Descrição clara**: descreva o serviço e o período de referência.
- **Guarde os PDFs (DANFSe)**: envie ao cliente e arquive.
- **Limite do MEI**: acompanhe o faturamento anual para não estourar o teto do
  MEI (o excedente muda a tributação).
- **Cancelamento**: notas emitidas por engano podem ser canceladas no próprio
  Emissor, dentro do prazo permitido, informando a justificativa.

---

## 4. Caminho avançado: integração via API (para automação)

Só faz sentido se você for **automatizar** a emissão a partir de um sistema.
**Não funciona em página HTML/navegador** — exige um **backend**.

### Requisitos técnicos
- **Certificado digital ICP-Brasil A1 ou A3** (e-CNPJ do MEI).
  - Obs.: o MEI também pode autenticar no ambiente do contribuinte via conta
    **gov.br Prata/Ouro**, mas a automação servidor-a-servidor usa certificado.
- **mTLS** (TLS mútuo com o certificado) nas chamadas.
- Montagem do **XML da DPS** (Declaração de Prestação de Serviço) validado
  contra o **XSD** oficial.
- **Assinatura digital** do XML (XMLDSIG) com a chave privada do certificado.
- Envio do XML **compactado em GZIP + Base64** dentro de um JSON.

### Fluxo resumido
1. Gerar o XML da **DPS** com os dados da nota.
2. **Assinar** o XML (XMLDSIG).
3. **Comprimir** (GZIP) e codificar em **Base64**.
4. `POST` para o endpoint de emissão do **SEFIN Nacional** (via mTLS).
5. Receber o **XML da NFS-e** processada (também GZIP+Base64) com a chave de
   acesso.
6. Gerar/baixar o **DANFSe** (PDF) pelo módulo correspondente.

### Ambientes e documentação
- **Produção Restrita** (homologação/testes) e **Produção**.
- **Swaggers por módulo**: CNC, ADN, Parametrização, DANFSe e **SEFIN**.
- Portal de documentação técnica:
  https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao
- **Swagger do contribuinte (ISSQN)**:
  https://www.nfse.gov.br/swagger/contribuintesissqn/
  (acesso com usuário/senha, certificado digital, ou conta gov.br Prata/Ouro
  para MEI).
- **Manual do Contribuinte — Emissor Público / API** (PDF oficial): busque por
  "Manual Contribuintes Emissor Público API Sistema Nacional NFS-e" no portal
  gov.br/nfse.

> Para um MEI que só precisa emitir algumas notas por mês, a **Seção 2 (Emissor
> Web)** resolve. A API só compensa com volume alto ou integração a um ERP.

---

## 5. Resumo rápido

| Necessidade | Caminho | Precisa de certificado? |
|---|---|---|
| Emitir algumas notas/mês | Emissor Web (nfse.gov.br) | Não — só conta gov.br Prata/Ouro |
| Emitir pelo celular | App NFS-e Mobile | Não |
| Automatizar via sistema/ERP | API SEFIN Nacional (backend) | Sim — A1/A3 (ou gov.br p/ MEI) |

**Links essenciais**
- Emissor / Portal: https://www.nfse.gov.br
- Documentação da API: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao
- Conta gov.br: https://www.gov.br
