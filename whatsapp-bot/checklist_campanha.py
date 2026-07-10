#!/usr/bin/env python3
"""
Envia checklist diario da campanha às 11h.
Informa: campanha iniciada + quantidade de abordagens programadas para o dia.
"""

import json
from datetime import date
from pathlib import Path
import openpyxl
import requests

ARQUIVO_LEADS = "leads.xlsx"
ARQUIVO_LOG = Path("logs") / "campanha.log"

COL_NOME = 1
COL_TELEFONE = 2
COL_STATUS = 4
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


def campanha_foi_iniciada_hoje():
    """Verifica se campanha_whatsapp.py foi executado hoje."""
    try:
        linhas = ARQUIVO_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False

    hoje_br = date.today().strftime("%d/%m/%Y")
    for linha in linhas[-100:]:  # Verifica últimas 100 linhas
        if f"Campanha WhatsApp ÔÇö {hoje_br}" in linha or "Campanha WhatsApp" in linha and "Elegíveis:" in linha:
            return True
    return False


def contar_abordagens_programadas():
    """Conta quantas pessoas foram abordadas hoje (data_ultimo = hoje)."""
    hoje_iso = date.today().isoformat()
    hoje_br = date.today().strftime("%d/%m/%Y")

    abordagens = 0
    if Path(ARQUIVO_LEADS).exists():
        wb = openpyxl.load_workbook(ARQUIVO_LEADS, read_only=True)
        ws = wb["Leads"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            ult = str(row[COL_DATA_ULTIMO - 1] or "")[:10]
            if ult in (hoje_iso, hoje_br):
                abordagens += 1
        wb.close()

    return abordagens


def main():
    cfg = carregar_config()
    numero_destino = str(cfg.get("alertas", {}).get("numero", "") or "")
    if not numero_destino:
        print('AVISO: configure "alertas": {"numero": "55..."} no config.json')
        return

    hoje_br = date.today().strftime("%d/%m/%Y")

    iniciada = campanha_foi_iniciada_hoje()
    abordagens = contar_abordagens_programadas()

    linhas = [f"✅ *Checklist da Campanha — {hoje_br}*", ""]

    if iniciada:
        linhas.append("✓ Campanha iniciada")
    else:
        linhas.append("✗ Campanha NÃO iniciada")

    linhas.append(f"✓ Abordagens programadas: *{abordagens}*")
    linhas.append("")
    linhas.append("_Status das 11h_")

    enviar_whatsapp(cfg, numero_destino, "\n".join(linhas))
    print(f"✓ Checklist enviado para {numero_destino}")


if __name__ == "__main__":
    main()
