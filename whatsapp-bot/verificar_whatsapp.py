#!/usr/bin/env python3
"""Normaliza telefones e verifica quais tem WhatsApp (nao envia nada)."""

import json
import time

import openpyxl
import requests

ARQUIVO = "leads.xlsx"
COL_TELEFONE = 2
COL_STATUS = 4
COL_OBS = 11

with open("config.json", encoding="utf-8") as f:
    CFG = json.load(f)

BASE = CFG["waha"]["url"].rstrip("/")
SESSAO = CFG["waha"]["sessao"]
HEADERS = {}
if CFG["waha"].get("api_key"):
    HEADERS["X-Api-Key"] = CFG["waha"]["api_key"]


def normalizar(bruto):
    digitos = "".join(filter(str.isdigit, bruto))
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    if len(digitos) == 12 and digitos[4] in "6789":
        digitos = digitos[:4] + "9" + digitos[4:]
    return digitos


def tem_whatsapp(numero):
    try:
        r = requests.get(f"{BASE}/api/contacts/check-exists", headers=HEADERS,
                         params={"phone": numero, "session": SESSAO}, timeout=15)
        r.raise_for_status()
        return bool(r.json().get("numberExists"))
    except Exception as e:
        print(f"  ! Erro ao verificar {numero}: {e}")
        return None


wb = openpyxl.load_workbook(ARQUIVO)
ws = wb["Leads"]

com_zap, sem_zap, erros, corrigidos, total = 0, 0, 0, 0, 0

for row in ws.iter_rows(min_row=2):
    cel_tel = row[COL_TELEFONE - 1]
    if cel_tel.value is None:
        continue
    bruto = str(cel_tel.value)
    if bruto.endswith(".0"):
        bruto = bruto[:-2]
    if not any(ch.isdigit() for ch in bruto):
        continue
    status = str(row[COL_STATUS - 1].value or "pendente").strip().lower()
    if status != "pendente":
        continue

    total += 1
    novo = normalizar(bruto)
    if novo != "".join(filter(str.isdigit, bruto)):
        corrigidos += 1
    cel_tel.value = novo
    cel_tel.number_format = "@"

    existe = tem_whatsapp(novo)
    if existe is False:
        sem_zap += 1
        row[COL_STATUS - 1].value = "ignorado"
        obs = str(row[COL_OBS - 1].value or "")
        if "SEM WHATSAPP" not in obs:
            row[COL_OBS - 1].value = (obs + " [SEM WHATSAPP]").strip()
        print(f"  x {novo} - SEM WhatsApp")
    elif existe is True:
        com_zap += 1
        print(f"  ok {novo}")
    else:
        erros += 1
    time.sleep(0.4)

wb.save(ARQUIVO)
print()
print(f"Verificados:             {total}")
print(f"Corrigidos/normalizados: {corrigidos}")
print(f"COM WhatsApp:            {com_zap}")
print(f"SEM WhatsApp (ignorado): {sem_zap}")
print(f"Erros de consulta:       {erros}")
