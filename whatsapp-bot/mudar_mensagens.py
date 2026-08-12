#!/usr/bin/env python3
"""
Aplica os textos novos (estilo "Rodrigo") da campanha no config.json:
  - mensagem.inicial   (1a abordagem)
  - mensagem.recontato (2a tentativa, dias depois)

Nao mexe em mais nada. Faz backup em config.json.bak.
Rode uma vez:  python mudar_mensagens.py
Entra automaticamente na proxima campanha (nao precisa reiniciar nada).
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

RECONTATO = (
    "Oi! É o Rodrigo de novo, da corretora aqui de Teresópolis. Passando pra ver se "
    "posso te ajudar com algum seguro — saúde, auto ou previdência. Qual te interessa "
    "mais? Faço a cotação sem compromisso.\n\n"
    "Se não for a hora, tranquilo! Me acha no Insta como Queiroz_Seguros que quando "
    "precisar é só chamar."
)

cfg_path = Path("config.json")
if not cfg_path.exists():
    print("ERRO: config.json nao encontrado. Rode este script na pasta do bot.")
    raise SystemExit(1)

shutil.copy(cfg_path, "config.json.bak")
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg.setdefault("mensagem", {})
cfg["mensagem"]["inicial"] = INICIAL
cfg["mensagem"]["recontato"] = RECONTATO
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("OK — mensagens atualizadas (backup em config.json.bak).")
print("=" * 55)
print("INICIAL:\n" + INICIAL)
print("-" * 55)
print("RECONTATO:\n" + RECONTATO)
print("=" * 55)
