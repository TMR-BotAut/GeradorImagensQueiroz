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


def chave(valor):
    """Normaliza qualquer formato para DDD + 8 ultimos digitos.

    Assim '21966786622', '5521966786622' e '2166786622' (com/sem 55,
    com/sem o 9 extra do celular) apontam todos para a mesma chave e casam.
    Retorna None se nao houver digitos suficientes.
    """
    d = so_digitos(valor)
    if len(d) >= 12 and d.startswith("55"):
        d = d[2:]  # remove o codigo do pais
    if len(d) < 10:
        return None
    return d[:2] + d[-8:]  # DDD + 8 finais


def main():
    entradas = [a for a in sys.argv[1:] if so_digitos(a)]
    if not entradas:
        print("Uso: python bloquear_numero.py 21966786622   (com ou sem o 55 na frente)")
        return

    # chave normalizada -> texto original digitado (para a mensagem de nao encontrado)
    alvos = {}
    for a in entradas:
        k = chave(a)
        if k:
            alvos[k] = a

    wb = openpyxl.load_workbook(ARQUIVO)
    ws = wb["Leads"]
    hoje = date.today().strftime("%d/%m/%Y")

    encontrados = set()
    for row in ws.iter_rows(min_row=2):
        k = chave(row[COL_TELEFONE - 1].value)
        if k and k in alvos:
            nome = str(row[COL_NOME - 1].value or "?")
            tel = so_digitos(row[COL_TELEFONE - 1].value)
            row[COL_STATUS - 1].value = "recusou"
            row[COL_TENTATIVAS - 1].value = 99
            obs = str(row[COL_OBS - 1].value or "")
            if "NAO PERTURBE" not in obs:
                row[COL_OBS - 1].value = (obs + f" [NAO PERTURBE {hoje}]").strip()
            encontrados.add(k)
            print(f"✓ Bloqueado: {nome} ({tel})")

    wb.save(ARQUIVO)

    for k, orig in alvos.items():
        if k not in encontrados:
            print(f"! Numero {orig} nao encontrado na planilha — nada a fazer.")


if __name__ == "__main__":
    main()
