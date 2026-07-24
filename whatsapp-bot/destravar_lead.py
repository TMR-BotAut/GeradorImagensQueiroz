#!/usr/bin/env python3
"""
Destrava leads marcados como 'abordado' por engano (ex: durante a pane do WAHA,
quando o envio era registrado como sucesso sem a mensagem ter sido entregue).

Volta o lead para 'pendente' e limpa o historico de tentativa, para que ele
receba a abordagem inicial normalmente na proxima campanha.

Uso:
    python destravar_lead.py 5521971839753 5521968344242 5521981649790
    (pode passar quantos numeros quiser, separados por espaco)
"""

import sys
import re

import openpyxl

ARQUIVO = "leads.xlsx"
COL_NOME = 1
COL_TELEFONE = 2
COL_STATUS = 4
COL_DATA_ULTIMO = 6
COL_PROXIMA_TENT = 7
COL_TENTATIVAS = 8


def so_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def main():
    numeros = [so_digitos(a) for a in sys.argv[1:] if so_digitos(a)]
    if not numeros:
        print("Uso: python destravar_lead.py 5521971839753 [outro...]")
        return

    wb = openpyxl.load_workbook(ARQUIVO)
    ws = wb["Leads"]

    encontrados = set()
    for row in ws.iter_rows(min_row=2):
        tel = so_digitos(row[COL_TELEFONE - 1].value)
        if not tel:
            continue
        for num in numeros:
            # Compara exato ou por sufixo de 8 digitos + DDD (tolera o 9 extra)
            if tel == num or (tel[-8:] == num[-8:] and tel[:4] == num[:4]):
                nome = str(row[COL_NOME - 1].value or "?")
                status_antigo = str(row[COL_STATUS - 1].value or "")
                row[COL_STATUS - 1].value = "pendente"
                row[COL_DATA_ULTIMO - 1].value = None
                row[COL_PROXIMA_TENT - 1].value = None
                row[COL_TENTATIVAS - 1].value = 0
                encontrados.add(num)
                print(f"✓ Destravado: {nome} ({tel}) — era '{status_antigo}', voltou para 'pendente'")

    wb.save(ARQUIVO)

    for num in numeros:
        if num not in encontrados:
            print(f"! Numero {num} nao encontrado na planilha — nada a fazer.")


if __name__ == "__main__":
    main()
