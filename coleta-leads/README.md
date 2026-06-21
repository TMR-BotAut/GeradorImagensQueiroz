# 🧲 Coletor de Leads — Casa dos Dados

Automatiza a coleta de leads (MEI com celular) em
[casadosdados.com.br](https://casadosdados.com.br/solucao/cnpj/pesquisa-avancada),
varrendo **todos os dias de um ano** e gravando **no formato da planilha de
leads** da campanha.

> Coleta, para cada dia: **Razão Social**, **CNPJ** e **Telefone**, com os
> filtros fixos **RJ · Teresópolis · Ativa · MEI · Somente Celular**.

---

## 1. Instalação

Precisa de **Python 3.9+**. Dentro da pasta `coleta-leads/`:

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. Como rodar

```bash
python coletar_casadosdados.py
```

- Na **primeira vez**, deixe `HEADLESS = False` (no topo do script) para **ver o
  navegador**. Se aparecer captcha ou aviso de cookies, resolva na tela e tecle
  **ENTER** no terminal para começar.
- O script percorre de **01/01/2025 até 31/12/2025**, um dia por vez, usando o
  mesmo dia nos dois campos de data.

## 3. O que ele gera

| Arquivo | Para que serve |
|---|---|
| `leads_coletados.xlsx` | A planilha com os leads (aba **Leads**, mesmo formato do `leads.xlsx`). |
| `progresso.json` | Marca o último dia coletado (permite **retomar**). |
| `coleta.log` | Registro do que aconteceu. |

Cada lead vem como: **Nome** = Razão Social · **Telefone** = `5521...` (limpo) ·
**Cidade** = Teresópolis · **Status** = pendente · **Observações** = CNPJ + data
de abertura.

👉 Depois é só **copiar as linhas (a partir da linha 2)** de `leads_coletados.xlsx`
para a aba **Leads** do seu `leads.xlsx` da campanha.

> ⚠️ Este arquivo **não** é um `leads.xlsx` completo (não tem a aba Dashboard);
> ele é a fonte pra você copiar os contatos.

## 4. Recursos úteis

- **Retomada:** pode fechar e reabrir — ele continua do dia seguinte ao último
  salvo. Salva a planilha **a cada dia**, então travamento não perde dados.
- **Sem duplicados:** não grava um CNPJ que já está na planilha.
- **Paginação:** se um dia tiver muitos resultados, ele segue as páginas
  (`SEGUIR_PAGINACAO = True`).

---

## 5. 🔧 Calibragem dos seletores (importante)

O site é dinâmico e muda de tempos em tempos, então um ou outro **seletor** pode
precisar de ajuste. Se o log avisar que não encontrou um campo, ou nada for
preenchido:

1. Rode com `HEADLESS = False`.
2. No navegador, aperte **F12** (DevTools) e clique no ícone de seta ↖ para
   inspecionar o campo problemático.
3. Clique com o botão direito no elemento → **Copy → Copy selector**.
4. Cole o seletor no bloco **`SEL`** no topo de `coletar_casadosdados.py`, na
   chave correspondente:

| Chave | Campo no site |
|---|---|
| `estado_input` / `cidade_input` | caixas de Estado e Cidade |
| `opcao_lista` | itens que aparecem na sugestão (dropdown) |
| `situacao_ativa` | a célula "ATIVA" |
| `toggle_mei` / `toggle_celular` | "Somente MEI" / "Somente Celular" |
| `data_de` / `data_ate` | campos de Data de Abertura |
| `btn_pesquisar` | botão Pesquisar |
| `detalhe_links` | link que abre o detalhe de cada resultado |

> 💡 Se você me **colar aqui o HTML** de um campo que não funcionou (ou um print
> do DevTools), eu acerto o seletor exato pra você.

---

## 6. ⚠️ Antes de usar em escala

- **Termos de Uso:** o site oferece **API/plano pago** para volume — esse é o
  caminho "oficial". Scraping pesado pode violar os termos e levar a **bloqueio
  de IP** (o site barra robôs ativamente).
- **Vá devagar:** as pausas no script existem por isso; não as reduza sem
  necessidade.
- **LGPD:** abordagem fria a esses contatos tem regras; respeite pedidos de
  remoção (o bot já trata o status `recusou`).
