#!/usr/bin/env python3
"""
WebhookRespostas -- Servidor WhatsApp via WAHA
- Leads conhecidos (na planilha): FAQ + classificacao de resposta
- Contatos desconhecidos: menu interativo com triagem por produto
"""

import json
import logging
import time
from datetime import datetime, date
from pathlib import Path

import requests as http_requests
from flask import Flask, request, jsonify
import openpyxl

# -- Log -----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("webhook.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# -- Config --------------------------------------------------------------------
with open("config.json", encoding="utf-8") as f:
    CFG = json.load(f)

ARQUIVO_LEADS = CFG["campanha"]["arquivo_leads"]
WAHA_URL = CFG["waha"]["url"].rstrip("/")
WAHA_SESSAO = CFG["waha"]["sessao"]
WAHA_API_KEY = CFG["waha"].get("api_key", "")

# Mapa <id de privacidade @lid> -> <telefone real>, alimentado pela campanha.
# O WhatsApp novo identifica alguns contatos por um "@lid" em vez do numero;
# este mapa permite reconhecer o lead quando a resposta chega.
ARQUIVO_LID_MAP = "lid_map.json"

# Rodrigo -- parceiro para produtos fora de saude
RODRIGO_NOME = "Rodrigo"
RODRIGO_TELEFONE = "5521988541324"

# Status
STATUS_ABORDADO = "abordado"
STATUS_RECUSOU = "recusou"
STATUS_INTERESSADO = "interessado"

# Colunas da aba Leads
COL_NOME = 1
COL_TELEFONE = 2
COL_CIDADE = 3
COL_STATUS = 4
COL_ULTIMA_R = 9
COL_HORA_R = 10
COL_OBS = 11

# Menus
MENU_CATEGORIA = (
    "O que voce esta buscando, {apelido}? \U0001f60a\n\n"
    "1 - Plano de Saude e Odontologico\n"
    "2 - Seguros\n"
    "3 - Solucoes Financeiras\n\n"
    "Responda com o numero da opcao."
)

MENU_SEGUROS = (
    "Otimo, {apelido}! Qual tipo de seguro?\n\n"
    "1 - Veiculo\n"
    "2 - Vida\n"
    "3 - Residencia\n"
    "4 - Equipamentos Portateis\n"
    "5 - Viagem\n\n"
    "Responda com o numero da opcao."
)

MENU_FINANCEIRO = (
    "Otimo, {apelido}! Qual solucao financeira?\n\n"
    "1 - Consorcio\n"
    "2 - Financiamento\n"
    "3 - Previdencia Privada\n"
    "4 - Responsabilidade Civil\n"
    "5 - Seguro de Vida\n\n"
    "Responda com o numero da opcao."
)

PRODUTOS_SEGUROS = {
    "1": "Veiculo",
    "2": "Vida",
    "3": "Residencia",
    "4": "Equipamentos Portateis",
    "5": "Viagem",
}

PRODUTOS_FINANCEIRO = {
    "1": "Consorcio",
    "2": "Financiamento",
    "3": "Previdencia Privada",
    "4": "Responsabilidade Civil",
    "5": "Seguro de Vida",
}

# Controle de mensagens ja processadas (evita duplicatas)
PROCESSADOS: set = set()

# Estado das conversas de contatos desconhecidos
CONVERSAS: dict = {}

app = Flask(__name__)


# -- Resolucao do id de privacidade (@lid) -------------------------------------
def resolver_telefone(raw_id: str) -> str:
    """Converte o id de privacidade (@lid) do WhatsApp no telefone real.

    Consulta o lid_map.json (alimentado pela campanha ao enviar). Se nao
    encontrar, devolve o proprio raw_id (contato realmente desconhecido).
    """
    try:
        if Path(ARQUIVO_LID_MAP).exists():
            mapa = json.loads(Path(ARQUIVO_LID_MAP).read_text(encoding="utf-8"))
            if raw_id in mapa:
                return str(mapa[raw_id])
    except Exception as e:
        log.warning(f"Nao consegui ler {ARQUIVO_LID_MAP}: {e}")
    return raw_id


# -- Envio de mensagens --------------------------------------------------------
def enviar_resposta(telefone: str, texto: str) -> bool:
    url = f"{WAHA_URL}/api/sendText"
    headers = {"Content-Type": "application/json"}
    if WAHA_API_KEY:
        headers["X-Api-Key"] = WAHA_API_KEY
    # Usa o chatId original se ja tiver @, senao adiciona @c.us
    chat_id = telefone if "@" in telefone else f"{telefone}@c.us"
    payload = {"session": WAHA_SESSAO, "chatId": chat_id, "text": texto}
    try:
        time.sleep(2)
        resp = http_requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        log.info(f" -> Mensagem enviada para {telefone}")
        return True
    except Exception as e:
        log.error(f" ERRO ao enviar para {telefone}: {e}")
        return False


def notificar_rodrigo(apelido: str, telefone_cliente: str, produto: str):
    msg = (
        f"*Novo contato - Queiroz Seguros*\n\n"
        f"Nome: {apelido}\n"
        f"Telefone: {telefone_cliente}\n"
        f"Interesse: {produto}"
    )
    enviar_resposta(RODRIGO_TELEFONE, msg)
    log.info(f" Rodrigo notificado: {apelido} / {produto}")


# -- Fluxo de contatos desconhecidos -------------------------------------------
def processar_desconhecido(from_jid: str, telefone: str, texto: str):
    """
    from_jid: JID completo para envio (ex: 28527491567699@lid ou 5521999@c.us)
    telefone: numero puro para chave do dicionario e planilha
    """
    estado = CONVERSAS.get(telefone, {"etapa": "inicio"})
    etapa = estado.get("etapa", "inicio")
    texto = texto.strip()

    if etapa == "inicio":
        CONVERSAS[telefone] = {"etapa": "aguarda_nome", "from_jid": from_jid}
        enviar_resposta(
            from_jid,
            "Ola! \U0001f60a Seja bem-vindo a *Queiroz Seguros*!\n\nAntes de tudo, como posso te chamar?"
        )
        log.info(f" Novo contato {from_jid} - iniciando fluxo de triagem")
        return

    from_jid = estado.get("from_jid", from_jid)

    if etapa == "aguarda_nome":
        apelido = texto.strip().split()[0].capitalize()
        CONVERSAS[telefone]["apelido"] = apelido
        CONVERSAS[telefone]["etapa"] = "aguarda_categoria"
        enviar_resposta(
            from_jid,
            f"Prazer, {apelido}! \U0001f60a\n\n" + MENU_CATEGORIA.format(apelido=apelido)
        )
        return

    if etapa == "aguarda_categoria":
        apelido = estado.get("apelido", "")
        if texto == "1":
            # Plano de Saude e Odontologico -> atendimento interno
            enviar_resposta(
                from_jid,
                f"Otima escolha, {apelido}! \U0001f60a\n\n"
                f"Nossa equipe especializada em *Plano de Saude e Odontologico* vai entrar em contato com voce em breve.\n\n"
                f"Fique a vontade para perguntar qualquer coisa por aqui!"
            )
            registrar_lead_desconhecido(telefone, estado, "Plano de Saude e Odontologico", "saude_interno")
            log.info(f" {apelido} ({telefone}) - Saude/Odonto -> ATENDIMENTO INTERNO")
            del CONVERSAS[telefone]
        elif texto == "2":
            CONVERSAS[telefone]["categoria"] = "seguros"
            CONVERSAS[telefone]["etapa"] = "aguarda_produto_seguro"
            enviar_resposta(from_jid, MENU_SEGUROS.format(apelido=apelido))
        elif texto == "3":
            CONVERSAS[telefone]["categoria"] = "financeiro"
            CONVERSAS[telefone]["etapa"] = "aguarda_produto_financeiro"
            enviar_resposta(from_jid, MENU_FINANCEIRO.format(apelido=apelido))
        else:
            enviar_resposta(
                from_jid,
                f"Por favor, {apelido}, responda apenas com *1*, *2* ou *3*. \U0001f60a\n\n"
                + MENU_CATEGORIA.format(apelido=apelido)
            )
        return

    if etapa == "aguarda_produto_seguro":
        apelido = estado.get("apelido", "")
        tel_cliente = telefone
        produto = PRODUTOS_SEGUROS.get(texto)

        if not produto:
            enviar_resposta(
                from_jid,
                f"Por favor, {apelido}, responda com um numero de 1 a 5. \U0001f60a\n\n"
                + MENU_SEGUROS.format(apelido=apelido)
            )
            return

        enviar_resposta(
            from_jid,
            f"*{RODRIGO_NOME}* e especialista em *{produto}* e vai entrar em contato com voce em breve, {apelido}! \U0001f60a\n\n"
            f"Caso prefira, pode chama-lo diretamente: (21) 98854-1324"
        )
        notificar_rodrigo(apelido, tel_cliente, produto)
        registrar_lead_desconhecido(telefone, estado, produto, "rodrigo")
        del CONVERSAS[telefone]
        return

    if etapa == "aguarda_produto_financeiro":
        apelido = estado.get("apelido", "")
        tel_cliente = telefone
        produto = PRODUTOS_FINANCEIRO.get(texto)

        if not produto:
            enviar_resposta(
                from_jid,
                f"Por favor, {apelido}, responda com um numero de 1 a 5. \U0001f60a\n\n"
                + MENU_FINANCEIRO.format(apelido=apelido)
            )
            return

        enviar_resposta(
            from_jid,
            f"*{RODRIGO_NOME}* e especialista em *{produto}* e vai entrar em contato com voce em breve, {apelido}! \U0001f60a\n\n"
            f"Caso prefira, pode chama-lo diretamente: (21) 98854-1324"
        )
        notificar_rodrigo(apelido, tel_cliente, produto)
        registrar_lead_desconhecido(telefone, estado, produto, "rodrigo")
        del CONVERSAS[telefone]
        return


def registrar_lead_desconhecido(telefone: str, estado: dict, produto: str, destino: str):
    if not Path(ARQUIVO_LEADS).exists():
        return
    try:
        apelido = estado.get("apelido", "")
        wb = openpyxl.load_workbook(ARQUIVO_LEADS)
        ws = wb["Leads"]
        nova_linha = ws.max_row + 1
        ws.cell(nova_linha, COL_NOME).value = apelido
        ws.cell(nova_linha, COL_TELEFONE).value = telefone
        ws.cell(nova_linha, COL_STATUS).value = STATUS_INTERESSADO
        ws.cell(nova_linha, COL_HORA_R).value = datetime.now().strftime("%d/%m/%Y %H:%M")
        obs = f"[INBOUND] Produto: {produto} | Tel: {telefone} | Encaminhado: {destino.upper()}"
        ws.cell(nova_linha, COL_OBS).value = obs
        atualizar_dashboard(wb)
        wb.save(ARQUIVO_LEADS)
        log.info(f" Lead {apelido} ({telefone}) registrado -> {produto}")
    except Exception as e:
        log.error(f" Erro ao registrar lead desconhecido: {e}")


# -- Fluxo de leads conhecidos -------------------------------------------------
def verificar_faq(texto: str):
    texto_lower = texto.lower().strip()
    faq = CFG.get("faq", {})
    for tema, dados in faq.items():
        if tema.startswith("_"):
            continue
        for gatilho in dados.get("gatilhos", []):
            if gatilho in texto_lower:
                return tema, dados["resposta"]
    return None, None


def classificar_resposta(texto: str) -> str:
    texto_lower = texto.lower().strip()
    for palavra in CFG["palavras_recusa"]:
        if palavra in texto_lower:
            return STATUS_RECUSOU
    tema_faq, _ = verificar_faq(texto)
    if tema_faq:
        return "faq"
    for palavra in CFG["palavras_interesse"]:
        if palavra in texto_lower:
            return STATUS_INTERESSADO
    return "aguarda_humano"


def atualizar_lead(from_jid: str, telefone: str, texto: str, classificacao: str):
    # from_jid = destino para responder (pode ser @lid); telefone = numero real (busca na planilha)
    if not Path(ARQUIVO_LEADS).exists():
        log.warning(f"Arquivo {ARQUIVO_LEADS} nao encontrado.")
        return False

    telefone_limpo = "".join(filter(str.isdigit, telefone))

    try:
        wb = openpyxl.load_workbook(ARQUIVO_LEADS)
        ws = wb["Leads"]
        encontrado = False

        for row in ws.iter_rows(min_row=2, values_only=False):
            tel_planilha = str(row[COL_TELEFONE - 1].value or "")
            tel_limpo = "".join(filter(str.isdigit, tel_planilha))

            if tel_limpo[-11:] == telefone_limpo[-11:] or tel_limpo == telefone_limpo:
                row_num = row[0].row
                nome = row[COL_NOME - 1].value or "?"

                if classificacao == STATUS_RECUSOU:
                    novo_status = STATUS_RECUSOU
                    log.info(f" RECUSOU -> {nome} ({tel_planilha})")

                elif classificacao == "faq":
                    tema_faq, resposta_faq = verificar_faq(texto)
                    cidade = str(row[COL_CIDADE - 1].value or "sua cidade").strip()
                    resposta_faq = resposta_faq.replace("[CIDADE]", cidade)
                    enviar_resposta(from_jid, resposta_faq)
                    novo_status = STATUS_ABORDADO
                    log.info(f" FAQ '{tema_faq}' respondido para {nome}")

                elif classificacao == STATUS_INTERESSADO:
                    novo_status = STATUS_INTERESSADO
                    log.info(f" INTERESSADO -> {nome} ({tel_planilha}) - ATENCAO HUMANA")

                else:
                    novo_status = STATUS_INTERESSADO
                    log.info(f" RESPOSTA -> {nome} ({tel_planilha}) - REVISAR")

                ws.cell(row_num, COL_STATUS).value = novo_status
                ws.cell(row_num, COL_ULTIMA_R).value = texto[:200]
                ws.cell(row_num, COL_HORA_R).value = datetime.now().strftime("%d/%m/%Y %H:%M")

                if novo_status == STATUS_INTERESSADO:
                    obs_atual = str(ws.cell(row_num, COL_OBS).value or "")
                    flag = f"[AGUARDA ATENDIMENTO {date.today().strftime('%d/%m')}]"
                    if flag not in obs_atual:
                        ws.cell(row_num, COL_OBS).value = f"{flag} {obs_atual}".strip()

                encontrado = True
                break

        if not encontrado:
            return False

        atualizar_dashboard(wb)
        wb.save(ARQUIVO_LEADS)
        log.info(f"Planilha atualizada -> {ARQUIVO_LEADS}")
        return True

    except Exception as e:
        log.error(f"Erro ao atualizar planilha: {e}")
        return False


def lead_existe_na_planilha(telefone: str) -> bool:
    if not Path(ARQUIVO_LEADS).exists():
        return False
    telefone_limpo = "".join(filter(str.isdigit, telefone))
    try:
        wb = openpyxl.load_workbook(ARQUIVO_LEADS, read_only=True)
        ws = wb["Leads"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            tel = "".join(filter(str.isdigit, str(row[COL_TELEFONE - 1] or "")))
            if tel[-11:] == telefone_limpo[-11:] or tel == telefone_limpo:
                return True
    except Exception:
        pass
    return False


def atualizar_dashboard(wb):
    STATUS_PENDENTE = "pendente"
    COL_DATA_ULTIMO = 6
    try:
        ws_leads = wb["Leads"]
        ws_dash = wb["Dashboard"]
    except KeyError:
        return

    contadores = {
        STATUS_PENDENTE: 0, STATUS_ABORDADO: 0,
        "ignorado": 0, STATUS_RECUSOU: 0, STATUS_INTERESSADO: 0,
    }
    total_abordados = 0
    abordados_hoje = 0
    hoje_str = date.today().isoformat()

    for row in ws_leads.iter_rows(min_row=2, values_only=True):
        nome = row[COL_NOME - 1]
        status = str(row[COL_STATUS - 1] or STATUS_PENDENTE)
        ult = str(row[COL_DATA_ULTIMO - 1] or "")
        if not nome:
            continue
        if status in contadores:
            contadores[status] += 1
        if status != STATUS_PENDENTE:
            total_abordados += 1
        if ult == hoje_str:
            abordados_hoje += 1

    total = sum(contadores.values())

    for row in ws_dash.iter_rows(min_row=1, values_only=False):
        label = str(row[0].value or "").strip().lower()
        if not label or len(row) < 2:
            continue
        cel = row[1]
        if "total leads" in label: cel.value = total
        elif "abordados hoje" in label: cel.value = abordados_hoje
        elif "total abordados" in label: cel.value = total_abordados
        elif "pendentes" in label: cel.value = contadores[STATUS_PENDENTE]
        elif "ignorados" in label: cel.value = contadores["ignorado"]
        elif "recusaram" in label: cel.value = contadores[STATUS_RECUSOU]
        elif "interessados" in label: cel.value = contadores[STATUS_INTERESSADO]
        elif "ultima atualiz" in label: cel.value = datetime.now().strftime("%d/%m/%Y %H:%M")
        elif "taxa resposta" in label:
            if total_abordados > 0:
                taxa = (contadores[STATUS_INTERESSADO] / total_abordados) * 100
                cel.value = round(taxa, 1)


# -- Rotas ---------------------------------------------------------------------
@app.route("/webhook", methods=["GET", "POST"])
def receber_mensagem():
    if request.method == "GET":
        return jsonify({"status": "ok"}), 200

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "ignored"}), 200

    try:
        evento = payload.get("event", "")
        if evento != "message":
            return jsonify({"status": "ignored"}), 200

        msg = payload.get("payload", {})
        msg_id = msg.get("id", "")
        from_me = msg.get("fromMe", False)

        if from_me:
            return jsonify({"status": "ignored"}), 200

        if msg_id in PROCESSADOS:
            return jsonify({"status": "duplicate"}), 200
        PROCESSADOS.add(msg_id)

        from_jid = msg.get("from", "") or msg.get("chatId", "")
        # Resolve o @lid (id de privacidade) para o telefone real, se conhecido
        telefone = resolver_telefone(from_jid.split("@")[0])

        body = msg.get("body", "")
        texto = body if isinstance(body, str) else ""

        if not texto:
            return jsonify({"status": "no_text"}), 200

        # Ignora mensagens de grupos (IDs de grupo sao muito longos ou terminam em @g.us)
        if "@g.us" in from_jid or len(telefone) > 15:
            log.info(f"Grupo ignorado: {from_jid}")
            return jsonify({"status": "ignored"}), 200

        log.info(f"Mensagem de {from_jid}: '{texto[:80]}'")

        if lead_existe_na_planilha(telefone):
            classificacao = classificar_resposta(texto)
            atualizar_lead(from_jid, telefone, texto, classificacao)
        else:
            processar_desconhecido(from_jid, telefone, texto)

    except Exception as e:
        log.error(f"Erro ao processar payload: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "arquivo_leads": ARQUIVO_LEADS,
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "processados_sessao": len(PROCESSADOS),
        "conversas_ativas": len(CONVERSAS),
    })


# -- Entrada -------------------------------------------------------------------
if __name__ == "__main__":
    log.info("=" * 60)
    log.info(" Webhook WhatsApp -- Queiroz Seguros")
    log.info(" Status: http://localhost:5000/status")
    log.info("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
