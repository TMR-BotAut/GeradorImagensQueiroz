# Bot de WhatsApp — Queiroz Seguros

Automação de **prospecção** e **atendimento** via WhatsApp (gateway WAHA), em Python.

> ⚠️ **Projeto separado** do gerador de imagens. Está nesta pasta `whatsapp-bot/`
> apenas porque é o repositório que tínhamos acesso para versionar. O ideal é movê-lo
> para um **repositório privado próprio** (ver "Próximos passos").

---

## 📂 Arquivos

| Arquivo | Função |
|---|---|
| `campanha_whatsapp.py` | **Disparo ativo** — envia a 1ª mensagem aos leads (limites de dia/horário/volume, recontato) |
| `config.example.json` | Modelo de configuração. Copie para `config.json` e preencha |
| `requirements.txt` | Dependências Python (`requests`, `openpyxl`, `flask`) |
| `.gitignore` | Mantém segredos, dados de cliente e logs fora do Git |

> Os scripts **`webhook_respostas.py`** (servidor Flask que recebe respostas) e
> **`criar_planilha.py`** (gera o `leads.xlsx`) fazem parte do sistema e estão na
> pasta do Drive — podem ser adicionados a este repositório depois.

---

## 🔐 Segurança (importante)

O `.gitignore` **impede** o versionamento de:

- `config.json` — contém a `api_key` real do WAHA
- `leads.xlsx`, `chats.json` — **dados pessoais de clientes (LGPD)**
- `*.log` — logs de execução

**Nunca** comite esses arquivos. Coloque a `api_key` apenas no `config.json` local.

---

## 🧪 Modo teste

Durante os testes, ative no `config.json`:

```json
"modo_teste": {
  "ativo": true,
  "max_envios": 2,
  "ignorar_dia_horario": true
}
```

- `ativo: true` → ignora as travas de dia/feriado e horário, e limita os envios a `max_envios`.
  Os envios saem **na hora** (sem esperar a janela de horário) e o log marca `[MODO TESTE]`.
- **Em produção:** mude para `"ativo": false`. Aí valem as regras normais
  (Seg–Qui, 10h–15h30, 11–17 contatos/dia). **Sem mexer no código.**

---

## ▶️ Como rodar

```bash
pip install -r requirements.txt

# 1. Suba o WAHA (gateway de WhatsApp) e pegue a api_key
# 2. Copie a config e preencha:
cp config.example.json config.json
#    -> edite waha.api_key, mensagens e FAQ

# 3. Gere a planilha de leads (script criar_planilha.py, da pasta do Drive)
#    e preencha a aba "Leads"

# 4. Rode a campanha
python campanha_whatsapp.py
```

---

## 🛠️ Próximos passos recomendados

1. **Mover para um repositório privado próprio** (ex.: `queiroz-whatsapp-bot`) — separa do
   gerador de imagens e mantém o código fora de um repo público.
2. **Adicionar** `webhook_respostas.py` e `criar_planilha.py` ao repositório.
3. **Migrar a `api_key`** do `config.json` para uma variável de ambiente / `.env`.
4. **Aquecimento do número:** começar com poucos envios/dia e subir aos poucos,
   para reduzir risco de bloqueio do WhatsApp.
