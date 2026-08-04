# GeradorImagensQueiroz
Criar story e post para insta da seguradora, modo padrão ou criativo

## Gerador de carrossel (Python)

`gerar_carrossel.py` gera carrosséis 1080x1080 para o feed, usando
`FundoFeed.jpeg` como fundo (a logo já está no arquivo) e a fonte Montserrat.

```bash
pip install -r requirements.txt
python3 gerar_carrossel.py
```

Os PNGs numerados (`slide_01.png`, `slide_02.png`, ...) são salvos em
`slides_output/`. Na primeira execução o script baixa a fonte Montserrat
automaticamente para `fonts/`.

Para gerar outro carrossel, crie um JSON com a mesma estrutura de
`CONTEUDO_PADRAO` (em `gerar_carrossel.py`) e rode:

```bash
python3 gerar_carrossel.py --content meu_carrossel.json
```

Dentro de qualquer texto, `**palavra**` destaca a palavra em laranja.
