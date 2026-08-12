#!/usr/bin/env python3
"""
Envia por WhatsApp o resumo diario da campanha (roda ao final de rodar_campanha.bat).

Numero de destino: config.json -> "alertas": {"numero": "5521..."}

Fila de atendimento: leads com status "interessado" e a marca
[AGUARDA ATENDIMENTO dd/mm] nas Observacoes (o webhook grava essa marca).
Ao atender um lead, apague a marca na planilha para tira-lo da fila.
"""

import json
from datetime import date
from pathlib import Path

import openpyxl
import requests

ARQUIVO_LEADS = "leads.xlsx"
ARQUIVO_LOG = Path("logs") / "campanha.log"
MEDIA_ENVIOS_DIA = 14  # media entre limite_min e limite_max por dia

COL_NOME = 1
COL_TELEFONE = 2
COL_STATUS = 4
COL_DATA_ULTIMO = 6
COL_ULTIMA_RESP = 9
COL_HORA_RESP = 10
COL_OBS = 11


def carregar_config():
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)


def enviar_whatsapp(cfg, numero, texto):
    base = cfg["waha"]["url"].rstrip("/")
    headers = {"Content-Type": "application/json"}
    if cfg["waha"].get("api_key"):
        headers["X-Api-Key"] = cfg["waha"]["api_key"]
    payload = {"session": cfg["waha"]["sessao"],
               "chatId": f"{numero}@c.us", "text": texto}
    resp = requests.post(f"{base}/api/sendText", headers=headers,
                         json=payload, timeout=15)
    resp.raise_for_status()


def erros_da_ultima_execucao():
    """Conta linhas de erro no ultimo bloco do campanha.log."""
    try:
        linhas = ARQUIVO_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0, []
    inicio = 0
    for i, linha in enumerate(linhas):
        if "==================" in linha:
            inicio = i
    erros = [l.strip() for l in linhas[inicio:] if "ERROR" in l or "✗" in l]
    return len(erros), erros[:3]


def main():
    cfg = carregar_config()
    numero_destino = str(cfg.get("alertas", {}).get("numero", "") or "")
    if not numero_destino:
        print('AVISO: configure "alertas": {"numero": "55..."} no config.json')
        return

    hoje = date.today()
    hoje_iso = hoje.isoformat()
    hoje_br = hoje.strftime("%d/%m/%Y")

    contagem = {"pendente": 0, "abordado": 0, "ignorado": 0,
                "recusou": 0, "interessado": 0}
    enviadas_hoje = 0
    recusas_hoje = 0
    total = 0
    fila = []

    if Path(ARQUIVO_LEADS).exists():
        wb = openpyxl.load_workbook(ARQUIVO_LEADS, read_only=True)
        ws = wb["Leads"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            nome = str(row[COL_NOME - 1] or "").strip()
            tel = str(row[COL_TELEFONE - 1] or "").strip()
            if not (nome or tel):
                continue
            total += 1
            status = str(row[COL_STATUS - 1] or "pendente").strip().lower()
            if status in contagem:
                contagem[status] += 1

            ult = str(row[COL_DATA_ULTIMO - 1] or "")[:10]
            if ult in (hoje_iso, hoje_br):
                enviadas_hoje += 1

            hora_resp = str(row[COL_HORA_RESP - 1] or "")
            if status == "recusou" and hoje_br in hora_resp:
                recusas_hoje += 1

            obs = str(row[COL_OBS - 1] or "")
            if status == "interessado" and "AGUARDA ATENDIMENTO" in obs:
                resp_txt = str(row[COL_ULTIMA_RESP - 1] or "").strip()
                fila.append((nome, tel, hora_resp, resp_txt))
        wb.close()

    n_erros, exemplos_erros = erros_da_ultima_execucao()
    dias_estoque = round(contagem["pendente"] / MEDIA_ENVIOS_DIA)

    linhas = [f"📊 *Resumo da campanha — {hoje_br}*", ""]
    linhas.append(f"📤 Enviadas hoje: *{enviadas_hoje}*")
    linhas.append(f"📦 Estoque: {contagem['pendente']} pendentes (~{dias_estoque} dias úteis)")
    if contagem["pendente"] <= 3 * MEDIA_ENVIOS_DIA:
        linhas.append("⚠️ Estoque baixo — hora de rodar a coleta de leads!")
    linhas.append("")

    if fila:
        linhas.append(f"🔥 *Aguardando atendimento humano ({len(fila)}):*")
        for nome, tel, hora, resp in fila[:10]:
            item = f"• {nome} — {tel}"
            if hora:
                item += f" — desde {hora}"
            linhas.append(item)
            if resp:
                linhas.append(f'   💬 "{resp[:80]}"')
        if len(fila) > 10:
            linhas.append(f"   ... e mais {len(fila) - 10}")
        linhas.append("_(atendeu? apague a marca AGUARDA ATENDIMENTO nas Observações)_")
    else:
        linhas.append("✅ Ninguém aguardando atendimento humano")
    linhas.append("")

    if recusas_hoje:
        linhas.append(f"🚫 Recusas hoje: {recusas_hoje}")
    if n_erros:
        linhas.append(f"❌ Erros na última execução: {n_erros}")
        for e in exemplos_erros:
            linhas.append(f"   {e[:100]}")
    if not recusas_hoje and not n_erros:
        linhas.append("✅ Sem recusas hoje e sem erros na execução")
    linhas.append("")

    linhas.append(f"Funil geral ({total} leads):")
    linhas.append(f"• Abordados: {contagem['abordado']} | Interessados: {contagem['interessado']}")
    linhas.append(f"• Recusaram: {contagem['recusou']} | Ignorados: {contagem['ignorado']}")

    enviar_whatsapp(cfg, numero_destino, "\n".join(linhas))
    print(f"✓ Resumo enviado para {numero_destino}")


if __name__ == "__main__":
    main()
