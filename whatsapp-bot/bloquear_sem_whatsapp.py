#!/usr/bin/env python3
"""Bloqueia de vez os leads [SEM WHATSAPP]. Rode sempre apos verificar_whatsapp.py."""

import openpyxl

ARQUIVO = "leads.xlsx"
COL_STATUS = 4
COL_TENTATIVAS = 8
COL_OBS = 11

wb = openpyxl.load_workbook(ARQUIVO)
ws = wb["Leads"]

bloqueados = 0
for row in ws.iter_rows(min_row=2):
    obs = str(row[COL_OBS - 1].value or "")
    if "SEM WHATSAPP" in obs:
        row[COL_STATUS - 1].value = "ignorado"
        row[COL_TENTATIVAS - 1].value = 99
        bloqueados += 1

wb.save(ARQUIVO)
print(f"Leads sem WhatsApp bloqueados definitivamente: {bloqueados}")
