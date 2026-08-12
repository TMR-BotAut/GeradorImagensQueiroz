#!/usr/bin/env python3
"""
Troca APENAS o texto da mensagem inicial da campanha no config.json.
Nao mexe em mais nada (menu, recontato, faq, etc.). Faz backup em config.json.bak.
Rode uma vez:  python mudar_inicial.py
O texto novo entra automaticamente na proxima campanha (nao precisa reiniciar nada).
"""

import json
import shutil
from pathlib import Path

INICIAL = (
    "Oi! Sou o Rodrigo, corretor de seguros aqui em Teresópolis. "
    "Trabalho com planos de saúde, seguros e previdência — se estiver renovando ou "
    "buscando cotação, posso te mandar opções sem compromisso. "
    "Qual seguro te interessa mais hoje — saúde, auto ou previdência?\n\n"
    "Se não for o momento, sem problema! Me busca no Insta como Queiroz_Seguros "
    "que quando precisar é só chamar."
)

cfg_path = Path("config.json")
if not cfg_path.exists():
    print("ERRO: config.json nao encontrado. Rode este script na pasta do bot.")
    raise SystemExit(1)

shutil.copy(cfg_path, "config.json.bak")
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg.setdefault("mensagem", {})
cfg["mensagem"]["inicial"] = INICIAL
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("OK — mensagem inicial atualizada (backup em config.json.bak).")
print("-" * 55)
print(INICIAL)
print("-" * 55)
