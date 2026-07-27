#!/usr/bin/env python3
"""
Aplica o texto novo da campanha (mensagem inicial com menu 1-5) e as respostas
automaticas do menu no config.json — sem voce precisar mexer em aspas/\\n.

Faz backup em config.json.bak antes de salvar.
Rode uma vez:  python aplicar_texto_novo.py
"""

import json
import shutil
from pathlib import Path

INICIAL = (
    "Mensagem automática da Queiroz Seguros — corretora de seguros em Teresópolis.\n\n"
    "Fazemos cotação gratuita de plano de saúde, odonto e seguros "
    "(auto, residencial, vida e equipamentos).\n\n"
    "Responda com o número da opção e já damos andamento:\n\n"
    "1 – Plano de saúde / odontológico\n"
    "2 – Seguro de auto\n"
    "3 – Residencial, vida ou equipamentos\n"
    "4 – Não sei ainda, quero ver as opções\n"
    "5 – Não tenho interesse (saio da lista)\n\n"
    "Sem custo e sem compromisso."
)

MENU_SAUDE = ("Perfeito. Sobre plano de saúde e odontológico, nossa equipe já vai te "
              "atender por aqui. Pode perguntar o que precisar.")
MENU_RODRIGO = ("Ótimo. Vou te encaminhar para o Rodrigo, nosso especialista, que já vai "
                "te atender. Se preferir, fale direto: (21) 98854-1324.")
MENU_OPTOUT = "Tudo bem, sem problema. Já removi seu contato da nossa lista. Obrigado!"

cfg_path = Path("config.json")
if not cfg_path.exists():
    print("ERRO: config.json nao encontrado. Rode este script na pasta do bot.")
    raise SystemExit(1)

shutil.copy(cfg_path, "config.json.bak")
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg.setdefault("mensagem", {})
cfg["mensagem"]["inicial"] = INICIAL
cfg["mensagem"]["menu_saude"] = MENU_SAUDE
cfg["mensagem"]["menu_rodrigo"] = MENU_RODRIGO
cfg["mensagem"]["menu_optout"] = MENU_OPTOUT
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("OK — config.json atualizado (backup salvo em config.json.bak).")
print("  - mensagem.inicial: texto novo com menu 1-5")
print("  - menu_saude / menu_rodrigo / menu_optout: respostas automaticas dos numeros")
print()
print("Novo texto da mensagem inicial:")
print("-" * 50)
print(INICIAL)
print("-" * 50)
