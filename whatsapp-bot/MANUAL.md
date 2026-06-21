# 📘 Manual do Bot de Prospecção — Queiroz Seguros

Guia completo de como o bot funciona, como colocar pra rodar e o que esperar.

---

## 1. O que é este bot

É um **assistente automático de prospecção no WhatsApp**. Ele faz o trabalho
repetitivo de:

- enviar mensagens de abordagem para uma lista de contatos (leads);
- receber as respostas e entender se a pessoa **recusou**, fez uma **pergunta**
  ou demonstrou **interesse**;
- responder dúvidas comuns sozinho (FAQ);
- organizar tudo numa planilha com um painel (Dashboard).

O objetivo é deixar pra você apenas a parte boa: **falar com quem realmente se
interessou.**

---

## 2. As peças do sistema

| Componente | Arquivo | Função |
|---|---|---|
| **Gerador da planilha** | `criar_planilha.py` | Cria o `leads.xlsx` (abas Leads + Dashboard). Roda **uma vez**. |
| **Campanha (envia)** | `campanha_whatsapp.py` | Dispara as mensagens para os leads pendentes. |
| **Webhook (recebe)** | `webhook_respostas.py` | Servidor que escuta e classifica as respostas. |
| **Configuração** | `config.json` | Suas chaves, mensagens, FAQ e regras. (criado por você) |
| **WAHA** | (Docker) | A "ponte" que conecta o código ao WhatsApp. |

> **WAHA** = *WhatsApp HTTP API*. É um programa gratuito (roda em Docker) que
> conecta seu número de WhatsApp ao bot. O código conversa com o WAHA, e o WAHA
> conversa com o WhatsApp.

---

## 3. Pré-requisitos

- **Python 3.9+** instalado
- **Docker** instalado (para rodar o WAHA)
- Um **número de WhatsApp** dedicado à prospecção (de preferência **não** o seu
  pessoal — veja os avisos no fim)

---

## 4. Instalação (passo a passo)

### 4.1. Instalar as dependências do Python

Dentro da pasta `whatsapp-bot/`:

```bash
pip install -r requirements.txt
```

### 4.2. Subir o WAHA (a ponte com o WhatsApp)

```bash
docker run -it --rm -p 3000:3000 devlikeapro/waha
```

Isso deixa o WAHA disponível em `http://localhost:3000`.

### 4.3. Conectar seu WhatsApp

1. Abra `http://localhost:3000` no navegador (painel do WAHA).
2. Inicie a sessão `default` e gere o **QR Code**.
3. No celular: WhatsApp → Aparelhos conectados → Conectar um aparelho → escaneie
   o QR. Pronto, o número está ligado ao bot.

### 4.4. Criar o arquivo de configuração

Copie o modelo e preencha com seus dados reais:

```bash
cp config.example.json config.json
```

> ⚠️ O `config.json` **nunca** vai para o Git (está no `.gitignore`). É nele que
> ficam suas chaves e mensagens reais.

### 4.5. Gerar a planilha de leads

```bash
python criar_planilha.py
```

Isso cria o `leads.xlsx`. Abra, vá na aba **Leads** e preencha a partir da linha 2:

- **Nome**, **Telefone** (formato `5521999990001` = 55 + DDD + número), **Cidade**
- **Status**: deixe todos como `pendente`

---

## 5. Como configurar (`config.json`)

| Seção | O que ajustar |
|---|---|
| `waha` | URL (`http://localhost:3000`), sessão (`default`) e `api_key` (se você definir uma no WAHA). |
| `modo_teste` | `ativo: true` para testar sem respeitar dia/horário e limitando os envios. **Em produção, deixe `false`.** |
| `campanha` | Limites por dia (11–17), janela de horário (10:00–15:30), dias de recontato (12) e máximo de tentativas (2). |
| `mensagem` | Texto da abordagem `inicial` e do `recontato`. Use `{nome}` e `{cidade}`. **Troque `[SEU NOME]`.** |
| `faq` | Perguntas frequentes e respostas automáticas (veja a seção 8). |
| `palavras_recusa` | Palavras que marcam o lead como **recusou**. |
| `palavras_interesse` | Palavras que marcam o lead como **interessado**. |

---

## 6. Como rodar a campanha (envio)

```bash
python campanha_whatsapp.py
```

**Recomendação:** comece com `modo_teste.ativo = true` no `config.json`. Assim o
bot envia só 2 mensagens, ignorando as travas de dia/horário, pra você conferir
se está tudo certo. Depois mude para `false`.

### Regras de envio (em produção)

- **Dias:** Segunda a Quinta apenas.
- **Horário:** entre 10:00 e 15:30 (os horários exatos são sorteados dentro
  dessa janela, pra parecer natural).
- **Volume:** entre 11 e 17 contatos por dia (sorteado).
- **Feriados:** o bot pula feriados nacionais (consulta a BrasilAPI),
  estaduais do RJ e municipais de Teresópolis.

> 💡 Para rodar **todo dia automaticamente**, agende o `campanha_whatsapp.py` no
> agendador do sistema (cron no Linux/Mac, Agendador de Tarefas no Windows).

---

## 7. Como rodar o webhook (recebimento)

```bash
python webhook_respostas.py
```

Ele sobe um servidor em `http://localhost:5000`. Depois, **avise o WAHA** para
mandar as mensagens recebidas pra ele:

> No painel do WAHA: **Settings → Webhooks** → URL `http://localhost:5000/webhook`
> → evento **`message`**.

Para conferir se está no ar, acesse `http://localhost:5000/status`.

> ⚠️ A campanha e o webhook são **dois programas separados**. Em produção, o
> webhook precisa ficar **sempre ligado** para captar as respostas; a campanha
> roda uma vez por dia.

---

## 8. FAQ — respostas automáticas

Quando um lead conhecido faz uma pergunta, o bot procura **palavras-gatilho** e
responde sozinho. Hoje vêm configurados 2 temas:

- **`preco`** — gatilhos: *quanto custa, valor, preço, mensalidade, caro, barato…*
- **`rede`** — gatilhos: *rede credenciada, hospital, clínica, exame, especialista…*

**Você pode editar e adicionar temas** livremente no `config.json`, seção `faq`.
Cada tema tem `gatilhos` (palavras que ativam) e `resposta` (texto enviado).
Dentro da resposta, `[CIDADE]` é trocado automaticamente pela cidade do lead;
campos como `[VALOR]` você preenche manualmente.

---

## 9. O que esperar — os status dos leads

Cada contato anda por estes status (coluna **Status** da planilha):

| Status | Significado |
|---|---|
| `pendente` | Ainda não foi abordado. |
| `abordado` | Mensagem enviada, aguardando resposta. |
| `ignorado` | Não respondeu — entra na fila de recontato; após 2 tentativas, encerrado. |
| `recusou` | Pediu para não receber mais — o bot **não envia mais** proativamente. |
| `interessado` | Demonstrou interesse — **precisa de atendimento humano (você).** |

### Como o "interessado" é sinalizado

É **passivo**, dentro da planilha:

- a coluna **Status** vira `interessado`;
- na coluna **Observações** entra uma marca `[AGUARDA ATENDIMENTO dd/mm]`;
- o contador **Interessados** do **Dashboard** sobe.

👉 Ou seja: **acompanhe o Dashboard / filtre a coluna Status por "interessado"**.
O sistema não te manda um alerta ativo (isso pode ser adicionado, se quiser).

> Exceção: na triagem de **contatos novos** que pedem produtos do parceiro
> (Rodrigo), o **Rodrigo recebe um WhatsApp** automático com o contato.

---

## 10. Recontato e encerramento (sem resposta)

1. **1ª tentativa:** mensagem inicial → status `abordado`.
2. Passados **12 dias** sem resposta, o lead volta para a fila e recebe a
   mensagem de **recontato** (2ª tentativa).
3. Passados mais **12 dias** sem resposta, ele atinge o limite de **2 tentativas**
   e fica como `ignorado` — **o bot não envia mais**.

---

## 11. Triagem de contatos novos (quem chama primeiro)

Se alguém que **não está na planilha** manda mensagem, o webhook conduz um
menu interativo (usa o próprio número do WhatsApp da pessoa — **não** pede
telefone):

1. Pergunta o **nome**
2. Pergunta a **categoria**:
   - **1) Plano de Saúde e Odontológico** → atendimento interno (você/Queiroz)
   - **2) Seguros** → Veículo, Vida, Residência, Equipamentos Portáteis, Viagem → Rodrigo
   - **3) Soluções Financeiras** → Consórcio, Financiamento, Previdência, Resp. Civil, Seguro de Vida → Rodrigo
3. Pergunta o **produto** específico (para Seguros e Soluções Financeiras)
4. Encaminha: Saúde fica interno; os demais **avisam o Rodrigo** por WhatsApp e
   passam o contato dele

O contato é registrado na planilha como `interessado`, com observação `[INBOUND]`.

---

## 12. Boas práticas e avisos ⚠️

- **Use um número dedicado.** Disparos em massa podem fazer o WhatsApp
  **banir** o número. Os limites diários e a janela de horário existem
  justamente para reduzir esse risco — não aumente sem necessidade.
- **Nunca** suba o `config.json` ou o `leads.xlsx` para o Git (já estão
  protegidos no `.gitignore`).
- Teste sempre com `modo_teste.ativo = true` antes de ir pra produção.
- Mantenha o **webhook ligado** o tempo todo para não perder respostas.

---

## 13. Problemas comuns

| Sintoma | Provável causa |
|---|---|
| "Arquivo leads.xlsx não encontrado" | Rode `python criar_planilha.py` primeiro. |
| Nada é enviado | Hoje é Sex–Dom ou feriado, ou `modo_teste` está limitando. |
| Respostas não chegam | Webhook não está ligado, ou a URL não foi cadastrada no WAHA. |
| Erro de envio (HTTP) | WAHA fora do ar, sessão desconectada ou número/formato errado. |
