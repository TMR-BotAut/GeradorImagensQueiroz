#!/usr/bin/env python3
"""
Gerador de carrossel para Instagram — Queiroz Seguros.

Renderiza slides 1080x1080 usando FundoFeed.jpeg como background e exporta
PNGs numerados (slide_01.png, slide_02.png, ...).

Uso:
    python3 gerar_carrossel.py
    python3 gerar_carrossel.py --background FundoFeed.jpeg --output slides_out
    python3 gerar_carrossel.py --content meu_carrossel.json

O conteúdo padrão (abaixo, em CONTEUDO_PADRAO) já traz o carrossel sobre
Seguro de Responsabilidade Civil. Para gerar outro carrossel, crie um JSON
com a mesma estrutura e passe via --content.

Marcação de destaque: dentro de qualquer texto, envolva a palavra ou frase
com **duplo asterisco** para pintá-la de laranja (#E8872E).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ----------------------------------------------------------------------------
# Constantes de layout / marca
# ----------------------------------------------------------------------------

CANVAS_SIZE = 1080
SAFE_MARGIN = 80                                   # margem mínima nas 4 bordas
BOTTOM_EXCLUSION = int(CANVAS_SIZE * 0.15)         # 15% inferior reservado à logo
TEXT_TOP = SAFE_MARGIN
TEXT_BOTTOM = CANVAS_SIZE - max(SAFE_MARGIN, BOTTOM_EXCLUSION)
TEXT_LEFT = SAFE_MARGIN
TEXT_RIGHT = CANVAS_SIZE - SAFE_MARGIN
MAX_TEXT_WIDTH = TEXT_RIGHT - TEXT_LEFT
USABLE_HEIGHT = TEXT_BOTTOM - TEXT_TOP

COLOR_WHITE = (255, 255, 255, 255)
COLOR_ORANGE = (0xE8, 0x87, 0x2E, 255)
COLOR_SHADOW = (0, 0, 0, 130)

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
VARIABLE_FONT_PATH = os.path.join(FONT_DIR, "Montserrat-VariableFont_wght.ttf")
VARIABLE_FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/"
    "Montserrat%5Bwght%5D.ttf"
)
# Se o usuário preferir, pode colocar arquivos estáticos com esses nomes em fonts/
STATIC_FONT_FILES = {
    400: "Montserrat-Regular.ttf",
    500: "Montserrat-Medium.ttf",
    600: "Montserrat-SemiBold.ttf",
    700: "Montserrat-Bold.ttf",
    800: "Montserrat-ExtraBold.ttf",
    900: "Montserrat-Black.ttf",
}

WEIGHT_HOOK = 800
WEIGHT_TITLE = 700
WEIGHT_BODY = 500
WEIGHT_BULLET = 500
WEIGHT_CTA_MAIN = 800
WEIGHT_HANDLE = 700


# ----------------------------------------------------------------------------
# Fontes
# ----------------------------------------------------------------------------

def _ensure_variable_font() -> None:
    if os.path.exists(VARIABLE_FONT_PATH):
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    print(f"[fontes] Baixando Montserrat (variable font) em {VARIABLE_FONT_PATH} ...")
    try:
        urllib.request.urlretrieve(VARIABLE_FONT_URL, VARIABLE_FONT_PATH)
    except Exception as exc:  # noqa: BLE001 - queremos mensagem clara, não crash silencioso
        raise RuntimeError(
            "Não foi possível baixar a fonte Montserrat automaticamente "
            f"({exc}). Baixe manualmente em https://fonts.google.com/specimen/Montserrat "
            f"e coloque os arquivos .ttf na pasta '{FONT_DIR}' "
            "(ex.: Montserrat-Regular.ttf, Montserrat-Bold.ttf, Montserrat-ExtraBold.ttf)."
        ) from exc


@lru_cache(maxsize=None)
def get_font(weight: int, size: int) -> ImageFont.FreeTypeFont:
    """Retorna a fonte Montserrat no peso/tamanho pedido, com cache."""
    static_path = os.path.join(FONT_DIR, STATIC_FONT_FILES.get(weight, ""))
    if os.path.exists(static_path):
        return ImageFont.truetype(static_path, size)

    _ensure_variable_font()
    font = ImageFont.truetype(VARIABLE_FONT_PATH, size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass  # fonte sem suporte a variação: segue com o peso default
    return font


# ----------------------------------------------------------------------------
# Modelo de conteúdo dos slides
# ----------------------------------------------------------------------------

@dataclass
class Slide:
    tipo: str                              # "hook" | "body" | "list" | "question" | "cta"
    titulo: Optional[str] = None
    corpo: Optional[str] = None
    bullets: List[str] = field(default_factory=list)
    cta_principal: Optional[str] = None
    cta_secundario: Optional[str] = None
    handle: Optional[str] = None


CONTEUDO_PADRAO: List[Slide] = [
    Slide(
        tipo="hook",
        corpo="Você tem uma empresa?\nEntão precisa conhecer o seguro que muita "
              "gente só descobre quando **já é tarde**.",
    ),
    Slide(
        tipo="body",
        titulo="O risco que ninguém planeja",
        corpo="Todo empreendedor se preocupa com vendas, impostos e fluxo de caixa. "
              "Mas existe um risco que **quase ninguém** coloca no planejamento.",
    ),
    Slide(
        tipo="body",
        titulo="E se sua empresa causar um dano?",
        corpo="Se sua empresa causar um **prejuízo** a um cliente ou a outra pessoa, "
              "você pode ter que responder por esse dano — e muita gente só descobre "
              "isso quando o problema **já aconteceu**.",
    ),
    Slide(
        tipo="body",
        titulo="Existe uma proteção pra isso",
        corpo="Ela se chama **Seguro de Responsabilidade Civil**. Mesmo assim, a "
              "maioria dos pequenos empresários nunca pediu uma cotação — porque nem "
              "sabia que ele existia.",
    ),
    Slide(
        tipo="list",
        titulo="Quem protege o patrimônio da empresa?",
        corpo="Você já deve ter:",
        bullets=["Seguro do carro", "Seguro da loja", "Seguro dos equipamentos"],
    ),
    Slide(
        tipo="question",
        corpo="Mas quem protege a empresa se ela precisar responder por um "
              "**dano a terceiros**?",
    ),
    Slide(
        tipo="body",
        titulo="O valor pode te surpreender",
        corpo="O Seguro de Responsabilidade Civil ajuda a proteger a empresa nessas "
              "situações, conforme as coberturas contratadas — e muitas vezes o valor "
              "**surpreende positivamente** quem faz uma cotação.",
    ),
    Slide(
        tipo="question",
        corpo="Se isso acontecesse amanhã com a sua empresa... você estaria "
              "**protegido**?\nSe a resposta for \"não sei\", vale a pena descobrir.",
    ),
    Slide(
        tipo="cta",
        cta_principal="Compartilhe com um empreendedor de **Teresópolis**.",
        cta_secundario="Ele provavelmente também não sabe que esse seguro existe.",
        handle="@queirozseguros",
    ),
]


def carregar_conteudo(path: Optional[str]) -> List[Slide]:
    if not path:
        return CONTEUDO_PADRAO
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return [Slide(**item) for item in dados]


# ----------------------------------------------------------------------------
# Parsing de markup **destaque** e quebra de linha
# ----------------------------------------------------------------------------

@dataclass
class Token:
    texto: str
    destaque: bool


def parse_markup(texto: str) -> List[Token]:
    """Converte texto com **destaque** em tokens de palavra, respeitando
    espaçamento original (ex.: "**tarde**." vira uma única palavra "tarde.",
    sem espaço artificial antes da pontuação)."""
    tokens: List[Token] = []
    for linha_idx, linha in enumerate(texto.split("\n")):
        if linha_idx > 0:
            tokens.append(Token("\n", False))

        chars: List[tuple] = []
        for m in re.finditer(r"\*\*(.+?)\*\*|([^*]+)", linha):
            if m.group(1) is not None:
                chars.extend((ch, True) for ch in m.group(1))
            else:
                chars.extend((ch, False) for ch in m.group(2))

        i, n = 0, len(chars)
        while i < n:
            while i < n and chars[i][0].isspace():
                i += 1
            if i >= n:
                break
            inicio = i
            while i < n and not chars[i][0].isspace():
                i += 1
            palavra_chars = chars[inicio:i]
            palavra = "".join(ch for ch, _ in palavra_chars)
            destaque = any(d for _, d in palavra_chars)
            tokens.append(Token(palavra, destaque))
    return tokens


@dataclass
class LinePiece:
    texto: str
    font: ImageFont.FreeTypeFont
    color: tuple
    largura: float


def montar_linhas(
    draw: ImageDraw.ImageDraw,
    tokens: List[Token],
    weight: int,
    size: int,
    max_width: int,
) -> List[List[LinePiece]]:
    font_normal = get_font(weight, size)
    font_destaque = get_font(max(weight, WEIGHT_TITLE), size)
    espaco = draw.textlength(" ", font=font_normal)

    linhas: List[List[LinePiece]] = [[]]
    largura_atual = 0.0

    for tok in tokens:
        if tok.texto == "\n":
            linhas.append([])
            largura_atual = 0.0
            continue

        fonte = font_destaque if tok.destaque else font_normal
        cor = COLOR_ORANGE if tok.destaque else COLOR_WHITE
        largura_palavra = draw.textlength(tok.texto, font=fonte)

        precisa_espaco = len(linhas[-1]) > 0
        largura_extra = (espaco if precisa_espaco else 0) + largura_palavra

        if largura_atual + largura_extra > max_width and linhas[-1]:
            linhas.append([])
            largura_atual = 0.0
            precisa_espaco = False
            largura_extra = largura_palavra

        linhas[-1].append(LinePiece(tok.texto, fonte, cor, largura_palavra))
        largura_atual += largura_extra

    return linhas


def altura_linhas(linhas: List[List[LinePiece]], size: int, line_spacing: float) -> float:
    if not linhas:
        return 0.0
    altura_linha = size * line_spacing
    return altura_linha * len(linhas)


def desenhar_linhas(
    draw: ImageDraw.ImageDraw,
    linhas: List[List[LinePiece]],
    top_y: float,
    size: int,
    line_spacing: float,
    align: str = "left",
    box_left: int = TEXT_LEFT,
    box_width: int = MAX_TEXT_WIDTH,
    sombra: bool = True,
) -> float:
    altura_linha = size * line_spacing
    y = top_y
    espaco_ref = draw.textlength(" ", font=linhas[0][0].font) if linhas and linhas[0] else 0

    for linha in linhas:
        largura_total = sum(p.largura for p in linha) + espaco_ref * max(0, len(linha) - 1)
        if align == "center":
            x = box_left + (box_width - largura_total) / 2
        else:
            x = box_left

        for peca in linha:
            if sombra:
                draw.text((x + 2, y + 3), peca.texto, font=peca.font, fill=COLOR_SHADOW)
            draw.text((x, y), peca.texto, font=peca.font, fill=peca.color)
            x += peca.largura + espaco_ref

        y += altura_linha

    return y


# ----------------------------------------------------------------------------
# Background e overlay de legibilidade
# ----------------------------------------------------------------------------

def carregar_background(path: str) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    escala = CANVAS_SIZE / min(w, h)
    novo_w, novo_h = round(w * escala), round(h * escala)
    img = img.resize((novo_w, novo_h), Image.LANCZOS)
    left = (novo_w - CANVAS_SIZE) // 2
    top = (novo_h - CANVAS_SIZE) // 2
    return img.crop((left, top, left + CANVAS_SIZE, top + CANVAS_SIZE))


def aplicar_overlay_legibilidade(base: Image.Image, top: int, bottom: int) -> Image.Image:
    """Escurece sutilmente a faixa onde o texto será desenhado, garantindo
    contraste mesmo em áreas mais claras do fundo."""
    overlay = Image.new("L", base.size, 0)
    od = ImageDraw.Draw(overlay)
    faixa_top = max(0, top - 60)
    faixa_bottom = min(base.height, bottom + 40)
    od.rectangle([0, faixa_top, base.width, faixa_bottom], fill=70)
    overlay = overlay.filter(ImageFilter.GaussianBlur(60))
    preto = Image.new("RGB", base.size, (0, 0, 0))
    return Image.composite(preto, base, overlay)


# ----------------------------------------------------------------------------
# Renderização por tipo de slide
# ----------------------------------------------------------------------------

def _fit_and_place(
    draw: ImageDraw.ImageDraw,
    blocos_builder,
    anchor: float,
) -> None:
    """blocos_builder(size) -> (altura_total, desenhar_fn(top_y)).
    Reduz o tamanho da fonte até caber em USABLE_HEIGHT, depois posiciona
    o bloco respeitando a regra dos terços (âncora vertical) e as margens."""
    size_scale = 1.0
    for _ in range(8):
        altura_total, _ = blocos_builder(size_scale)
        if altura_total <= USABLE_HEIGHT:
            break
        size_scale *= 0.92

    altura_total, desenhar_fn = blocos_builder(size_scale)
    top_y = anchor - altura_total * 0.35
    top_y = max(TEXT_TOP, min(top_y, TEXT_BOTTOM - altura_total))
    desenhar_fn(top_y)


def render_hook(draw: ImageDraw.ImageDraw, slide: Slide) -> None:
    base_size = 76

    def build(scale):
        size = round(base_size * scale)
        tokens = parse_markup(slide.corpo or "")
        linhas = montar_linhas(draw, tokens, WEIGHT_HOOK, size, MAX_TEXT_WIDTH)
        altura = altura_linhas(linhas, size, 1.18)
        return altura, lambda top_y: desenhar_linhas(
            draw, linhas, top_y, size, 1.18, align="left"
        )

    _fit_and_place(draw, build, anchor=CANVAS_SIZE / 3)


def render_question(draw: ImageDraw.ImageDraw, slide: Slide) -> None:
    base_size = 58

    def build(scale):
        size = round(base_size * scale)
        tokens = parse_markup(slide.corpo or "")
        linhas = montar_linhas(draw, tokens, WEIGHT_TITLE, size, MAX_TEXT_WIDTH)
        altura = altura_linhas(linhas, size, 1.22)
        return altura, lambda top_y: desenhar_linhas(
            draw, linhas, top_y, size, 1.22, align="left"
        )

    _fit_and_place(draw, build, anchor=CANVAS_SIZE / 3)


def render_body(draw: ImageDraw.ImageDraw, slide: Slide) -> None:
    title_size = 50
    body_size = 38
    gap = 28

    def build(scale):
        t_size = round(title_size * scale)
        b_size = round(body_size * scale)
        gap_s = round(gap * scale)

        linhas_titulo = montar_linhas(
            draw, parse_markup(slide.titulo or ""), WEIGHT_TITLE, t_size, MAX_TEXT_WIDTH
        )
        altura_titulo = altura_linhas(linhas_titulo, t_size, 1.2)

        linhas_corpo = montar_linhas(
            draw, parse_markup(slide.corpo or ""), WEIGHT_BODY, b_size, MAX_TEXT_WIDTH
        )
        altura_corpo = altura_linhas(linhas_corpo, b_size, 1.4)

        altura_total = altura_titulo + gap_s + altura_corpo

        def desenhar(top_y):
            y = desenhar_linhas(draw, linhas_titulo, top_y, t_size, 1.2, align="left")
            y = top_y + altura_titulo + gap_s
            desenhar_linhas(draw, linhas_corpo, y, b_size, 1.4, align="left")

        return altura_total, desenhar

    _fit_and_place(draw, build, anchor=CANVAS_SIZE / 3)


def render_list(draw: ImageDraw.ImageDraw, slide: Slide) -> None:
    title_size = 48
    intro_size = 36
    bullet_size = 36
    gap = 22
    bullet_gap = 16
    bullet_indent = 34

    def build(scale):
        t_size = round(title_size * scale)
        i_size = round(intro_size * scale)
        bu_size = round(bullet_size * scale)
        gap_s = round(gap * scale)
        bgap_s = round(bullet_gap * scale)

        linhas_titulo = montar_linhas(
            draw, parse_markup(slide.titulo or ""), WEIGHT_TITLE, t_size, MAX_TEXT_WIDTH
        )
        altura_titulo = altura_linhas(linhas_titulo, t_size, 1.2)

        linhas_intro = montar_linhas(
            draw, parse_markup(slide.corpo or ""), WEIGHT_BODY, i_size, MAX_TEXT_WIDTH
        )
        altura_intro = altura_linhas(linhas_intro, i_size, 1.3) if slide.corpo else 0

        bullets_linhas = [
            montar_linhas(
                draw, parse_markup(b), WEIGHT_BULLET, bu_size, MAX_TEXT_WIDTH - bullet_indent
            )
            for b in slide.bullets
        ]
        altura_bullets = sum(
            altura_linhas(bl, bu_size, 1.3) + bgap_s for bl in bullets_linhas
        )

        altura_total = altura_titulo + (gap_s + altura_intro if slide.corpo else 0) + gap_s + altura_bullets

        def desenhar(top_y):
            y = top_y
            desenhar_linhas(draw, linhas_titulo, y, t_size, 1.2, align="left")
            y += altura_titulo
            if slide.corpo:
                y += gap_s
                desenhar_linhas(draw, linhas_intro, y, i_size, 1.3, align="left")
                y += altura_intro
            y += gap_s
            font_bullet = get_font(bu_size and WEIGHT_BULLET, bu_size)
            raio = bu_size * 0.11
            for bl in bullets_linhas:
                cy = y + bu_size * 0.55
                draw.ellipse(
                    [TEXT_LEFT, cy - raio, TEXT_LEFT + raio * 2, cy + raio],
                    fill=COLOR_ORANGE,
                )
                desenhar_linhas(
                    draw, bl, y, bu_size, 1.3, align="left",
                    box_left=TEXT_LEFT + bullet_indent,
                    box_width=MAX_TEXT_WIDTH - bullet_indent,
                )
                y += altura_linhas(bl, bu_size, 1.3) + bgap_s

        return altura_total, desenhar

    _fit_and_place(draw, build, anchor=CANVAS_SIZE / 3)


def render_cta(draw: ImageDraw.ImageDraw, slide: Slide) -> None:
    principal_size = 54
    secundario_size = 34
    handle_size = 40
    gap = 24

    def build(scale):
        p_size = round(principal_size * scale)
        s_size = round(secundario_size * scale)
        h_size = round(handle_size * scale)
        gap_s = round(gap * scale)

        linhas_p = montar_linhas(
            draw, parse_markup(slide.cta_principal or ""), WEIGHT_CTA_MAIN, p_size, MAX_TEXT_WIDTH
        )
        altura_p = altura_linhas(linhas_p, p_size, 1.2)

        linhas_s = montar_linhas(
            draw, parse_markup(slide.cta_secundario or ""), WEIGHT_BODY, s_size, MAX_TEXT_WIDTH
        )
        altura_s = altura_linhas(linhas_s, s_size, 1.3) if slide.cta_secundario else 0

        linhas_h = montar_linhas(
            draw, parse_markup(f"**{slide.handle}**" if slide.handle else ""),
            WEIGHT_HANDLE, h_size, MAX_TEXT_WIDTH,
        )
        altura_h = altura_linhas(linhas_h, h_size, 1.2) if slide.handle else 0

        altura_total = (
            altura_p
            + (gap_s + altura_s if slide.cta_secundario else 0)
            + (gap_s * 1.6 + altura_h if slide.handle else 0)
        )

        def desenhar(top_y):
            y = top_y
            desenhar_linhas(draw, linhas_p, y, p_size, 1.2, align="center")
            y += altura_p
            if slide.cta_secundario:
                y += gap_s
                desenhar_linhas(draw, linhas_s, y, s_size, 1.3, align="center")
                y += altura_s
            if slide.handle:
                y += gap_s * 1.6
                desenhar_linhas(draw, linhas_h, y, h_size, 1.2, align="center")

        return altura_total, desenhar

    _fit_and_place(draw, build, anchor=CANVAS_SIZE / 2)


RENDERERS = {
    "hook": render_hook,
    "question": render_question,
    "body": render_body,
    "list": render_list,
    "cta": render_cta,
}


# ----------------------------------------------------------------------------
# Pipeline principal
# ----------------------------------------------------------------------------

def gerar_carrossel(background_path: str, slides: List[Slide], output_dir: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    background = carregar_background(background_path)
    background = aplicar_overlay_legibilidade(background, TEXT_TOP, TEXT_BOTTOM)

    caminhos = []
    for i, slide in enumerate(slides, start=1):
        img = background.copy()
        draw = ImageDraw.Draw(img)

        renderer = RENDERERS.get(slide.tipo)
        if renderer is None:
            raise ValueError(f"Tipo de slide desconhecido: {slide.tipo!r}")
        renderer(draw, slide)

        nome = f"slide_{i:02d}.png"
        caminho = os.path.join(output_dir, nome)
        img.save(caminho, "PNG")
        caminhos.append(caminho)
        print(f"[ok] {caminho}")

    return caminhos


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera carrossel de Instagram para a Queiroz Seguros.")
    parser.add_argument(
        "--background", default="FundoFeed.jpeg",
        help="Caminho da imagem de fundo (padrão: FundoFeed.jpeg)",
    )
    parser.add_argument(
        "--output", default="slides_output",
        help="Pasta de saída dos PNGs (padrão: slides_output)",
    )
    parser.add_argument(
        "--content", default=None,
        help="JSON com lista de slides (mesma estrutura de CONTEUDO_PADRAO). "
             "Se omitido, usa o carrossel padrão sobre Seguro de Responsabilidade Civil.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.background):
        print(
            f"[erro] Imagem de fundo não encontrada em '{args.background}'. "
            "Coloque o arquivo FundoFeed.jpeg na raiz do projeto ou informe "
            "o caminho correto com --background.",
            file=sys.stderr,
        )
        sys.exit(1)

    slides = carregar_conteudo(args.content)
    gerar_carrossel(args.background, slides, args.output)


if __name__ == "__main__":
    main()
