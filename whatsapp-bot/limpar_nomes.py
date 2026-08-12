#!/usr/bin/env python3
"""Limpa a coluna Nome: tira ID numerico do inicio e formata maiusculas."""

import openpyxl

ARQUIVO = "leads.xlsx"
COL_NOME = 1
COL_OBS = 11

MINUSCULAS = {"da", "de", "do", "das", "dos", "e"}


def tem_digito(token):
    return any(ch.isdigit() for ch in token)


def formatar(nome):
    palavras = []
    for i, p in enumerate(nome.lower().split()):
        if i > 0 and p in MINUSCULAS:
            palavras.append(p)
        else:
            palavras.append(p.capitalize())
    return " ".join(palavras)


wb = openpyxl.load_workbook(ARQUIVO)
ws = wb["Leads"]

limpos, revisar = 0, []

for row in ws.iter_rows(min_row=2):
    cel = row[COL_NOME - 1]
    if not cel.value:
        continue
    original = str(cel.value).strip()
    tokens = original.split()

    id_removido = []
    while tokens and tem_digito(tokens[0]):
        id_removido.append(tokens.pop(0))

    if not tokens:
        revisar.append(cel.row)
        continue

    novo = formatar(" ".join(tokens))
    if novo != original:
        cel.value = novo
        limpos += 1
    if id_removido:
        obs_cel = row[COL_OBS - 1]
        obs = str(obs_cel.value or "")
        if "[ID:" not in obs:
            obs_cel.value = (obs + f" [ID: {' '.join(id_removido)}]").strip()

wb.save(ARQUIVO)
print(f"Nomes corrigidos: {limpos}")
print(f"Linhas para revisar (nome era so numero): {revisar}")
