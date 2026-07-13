#!/usr/bin/env python3
"""
Bloqueia um numero especifico na planilha (pessoa pediu para nao ser incomodada).
Marca status = "recusou" e tentativas = 99 — a campanha nunca mais envia.

Uso:
    python bloquear_numero.py 5521966628839
    python bloquear_numero.py 5521966628839 5521912345678   (varios de uma vez)
"""

import sys
import re
from datetime import date

import openpyxl

ARQUIVO = "leads.xlsx"
COL_NOME = 1
COL_TELEFONE = 2
COL_STATUS = 4
COL_TENTATIVAS = 8
COL_OBS = 11


def so_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def main():
    numeros = [so_digitos(a) for a in sys.argv[1:] if so_digitos(a)]
    if not numeros:
        print("Uso: python bloquear_numero.py 5521966628839")
        return

    wb = openpyxl.load_workbook(ARQUIVO)
    ws = wb["Leads"]
    hoje = date.today().strftime("%d/%m/%Y")

    encontrados = set()
    for row in ws.iter_rows(min_row=2):
        tel = so_digitos(row[COL_TELEFONE - 1].value)
        if not tel:
            continue
        for num in numeros:
            # Compara com e sem o 9 extra (5521 9 6662-8839 vs 5521 6662-8839)
            if tel == num or tel[-8:] == num[-8:] and tel[:4] == num[:4]:
                nome = str(row[COL_NOME - 1].value or "?")
                row[COL_STATUS - 1].value = "recusou"
                row[COL_TENTATIVAS - 1].value = 99
                obs = str(row[COL_OBS - 1].value or "")
                if "NAO PERTURBE" not in obs:
                    row[COL_OBS - 1].value = (obs + f" [NAO PERTURBE {hoje}]").strip()
                encontrados.add(num)
                print(f"✓ Bloqueado: {nome} ({tel})")

    wb.save(ARQUIVO)

    for num in numeros:
        if num not in encontrados:
            print(f"! Numero {num} nao encontrado na planilha — nada a fazer.")


if __name__ == "__main__":
    main()
