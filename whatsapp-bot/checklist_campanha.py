#!/usr/bin/env python3
"""
Checklist diario da campanha (roda às 11h via Agendador de Tarefas).

- Se a campanha rodou hoje: envia um resumo curto (rodou + abordagens do dia).
- Se a campanha NAO rodou hoje (ex: PC estava desligado às 10h por queda de energia):
  envia um alerta com o passo a passo COMPLETO para rodar manualmente, sem depender
  de ninguem.

Destino: config.json -> "alertas": {"numero": "55..."}
"""

import json
from datetime import date
from pathlib import Path

import openpyxl
import requests

ARQUIVO_LEADS = "leads.xlsx"
ARQUIVO_LOG = Path("logs") / "campanha.log"

COL_DATA_ULTIMO = 6


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


def campanha_rodou_hoje():
    """True se o campanha_whatsapp.py registrou execucao hoje no log.

    Detecta pela data ISO no inicio da linha (ex: '2026-07-23') + o cabecalho
    'Campanha WhatsApp'. Nao depende de acentos/traco (evita problema de encoding).
    """
    try:
        linhas = ARQUIVO_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    hoje_iso = date.today().isoformat()
    for linha in linhas[-3000:]:  # tail generoso: cobre o dia mesmo apos o verificar_whatsapp
        if linha.startswith(hoje_iso) and "Campanha WhatsApp" in linha:
            return True
    return False


def contar_abordagens_hoje():
    """Conta leads com data do ultimo contato = hoje."""
    hoje_iso = date.today().isoformat()
    hoje_br = date.today().strftime("%d/%m/%Y")
    n = 0
    if Path(ARQUIVO_LEADS).exists():
        wb = openpyxl.load_workbook(ARQUIVO_LEADS, read_only=True)
        ws = wb["Leads"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            ult = str(row[COL_DATA_ULTIMO - 1] or "")[:10]
            if ult in (hoje_iso, hoje_br):
                n += 1
        wb.close()
    return n


def mensagem_rodou(hoje_br):
    return [
        f"✅ *Checklist da Campanha — {hoje_br}*",
        "",
        "✓ Campanha rodou hoje",
        f"✓ Abordagens até agora: *{contar_abordagens_hoje()}*",
        "",
        "_Status das 11h_",
    ]


def mensagem_nao_rodou(hoje_br):
    return [
        f"⚠️ *Campanha NÃO rodou hoje — {hoje_br}*",
        "",
        "A campanha das 10h não foi executada (provável PC desligado ou queda de "
        "energia no horário). Nenhuma mensagem saiu ainda hoje.",
        "",
        "*Para rodar manualmente — passo a passo:*",
        "",
        "1) Feche a planilha *leads.xlsx*, se estiver aberta no Excel "
        "(o programa não consegue salvar com ela aberta).",
        "",
        "2) Abra o Prompt de Comando: tecla *Windows*, digite *cmd*, tecla *Enter*.",
        "",
        "3) Digite a linha abaixo e tecle *Enter*:",
        "cd C:\\Projetos\\bot-whatsapp",
        "",
        "4) Digite a linha abaixo e tecle *Enter*:",
        "python campanha_whatsapp.py",
        "",
        "5) Aguarde. Vão aparecer linhas de envio ao longo do tempo. "
        "*Deixe a janela aberta* até o fim do dia (ela envia espaçado).",
        "",
        "_Dica: quanto mais cedo rodar, mais espaçados ficam os envios. "
        "Se já passou muito das 15h, avalie deixar para o próximo dia útil._",
    ]


def main():
    cfg = carregar_config()
    numero_destino = str(cfg.get("alertas", {}).get("numero", "") or "")
    if not numero_destino:
        print('AVISO: configure "alertas": {"numero": "55..."} no config.json')
        return

    hoje_br = date.today().strftime("%d/%m/%Y")
    rodou = campanha_rodou_hoje()
    linhas = mensagem_rodou(hoje_br) if rodou else mensagem_nao_rodou(hoje_br)

    enviar_whatsapp(cfg, numero_destino, "\n".join(linhas))
    print(f"✓ Checklist enviado para {numero_destino} (campanha rodou hoje: {rodou})")


if __name__ == "__main__":
    main()
