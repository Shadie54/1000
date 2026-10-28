# gui/canvas.py
#
# Vykresľovacia vrstva pre rework rozlíšení (claude/13_RESOLUTION_REWORK_
# ANALYSIS.md, krok 4) — prevzaté z hry CHUJ.
#
# Obrazovky kreslia v LOGICKÝCH súradniciach (šírka 1920, výška 1080…1200,
# rovnaké čísla ako doteraz), Canvas ich prevedie na fyzické pixely okna:
#   - text sa vykreslí fontom vo fyzickej veľkosti (ostrý aj na 4K),
#   - karty sa zmenšia z najmenšieho dostatočne veľkého assetu
#     (cards-small/medium/large) cez smoothscale,
#   - povrchy z font.render()/card()/image() sú LSurf — fyzické pixely,
#     ale get_width()/get_rect() hlásia logické rozmery, takže bežný kód
#     `surf.get_rect(center=rect.center)` funguje bez zmeny.
#
# Pixelová zhoda pri 1920×1080: pri mierke 1 sa správa presne ako pôvodný
# kód (rovnaké fonty, overlaye, čiary). Obrázky, ktoré pôvodný kód
# zmenšoval cez transform.scale (karty v pozadí menu, logo, trofeje),
# sa pri mierke 1 škálujú rovnako (`smooth=False`), pri inej mierke vždy
# cez smoothscale.
#
# Použitie v obrazovke: self.canvas = display.canvas(); kresliť cez
# self.canvas.*; na konci snímky display.present().

import math
import os

import pygame

from config import (
    CARDS_SMALL_PATH, CARDS_MEDIUM_PATH, CARDS_LARGE_PATH,
    CARD_SIZE_SMALL, CARD_SIZE_MEDIUM, CARD_SIZE_LARGE, get_font,
)

# (fyzická šírka assetu, priečinok) — od najmenšieho
_CARD_SOURCES = (
    (CARD_SIZE_SMALL[0], CARDS_SMALL_PATH),
    (CARD_SIZE_MEDIUM[0], CARDS_MEDIUM_PATH),
    (CARD_SIZE_LARGE[0], CARDS_LARGE_PATH),
)


class LSurf:
    """Proxy povrch: fyzické pixely (`phys`), rozmery hlási LOGICKÉ."""

    def __init__(self, phys: pygame.Surface, lw: int, lh: int):
        self.phys = phys
        self.lw, self.lh = lw, lh

    def get_width(self) -> int:
        return self.lw

    def get_height(self) -> int:
        return self.lh

    def get_size(self) -> tuple[int, int]:
        return (self.lw, self.lh)

    def get_rect(self, **kwargs) -> pygame.Rect:
        rect = pygame.Rect(0, 0, self.lw, self.lh)
        for key, value in kwargs.items():
            setattr(rect, key, value)
        return rect

    def copy(self) -> "LSurf":
        return LSurf(self.phys.copy(), self.lw, self.lh)

    def set_alpha(self, alpha: int | None):
        self.phys.set_alpha(alpha)


class ScaledFont:
    """Font vo fyzickej veľkosti round(size·s); metriky vracia logické.
    Fyzický font sa berie z config.get_font() (rovnaké písmo)."""

    def __init__(self, logical_size: int, scale: float):
        self.scale = scale
        self.logical_size = logical_size
        self.font = get_font(max(1, round(logical_size * scale)))

    def render(self, text: str, antialias: bool, color, background=None) -> LSurf:
        surf = self.font.render(text, antialias, color, background)
        w, h = surf.get_size()
        return LSurf(surf, math.ceil(w / self.scale), math.ceil(h / self.scale))

    def size(self, text: str) -> tuple[float, float]:
        w, h = self.font.size(text)
        return (w / self.scale, h / self.scale)

    def get_height(self) -> float:
        return self.font.get_height() / self.scale

    def get_linesize(self) -> float:
        return self.font.get_linesize() / self.scale


def _hires_variant(path: str, tw: int, th: int) -> str:
    """Pozadie vo vyššom rozlíšení, ak ho okno potrebuje a existuje:
    k "table.jpg" patrí "table_4k.jpg" (rovnaký obrázok, napr. 3840×2160).
    Použije sa len pri okne väčšom než Full HD — inak sa šetrí pamäť aj
    čas načítania. Pridanie variantu nevyžaduje zmenu kódu (z CHUJ)."""
    if tw <= 1920 * 1.05 and th <= 1200 * 1.05:
        return path
    base, ext = os.path.splitext(path)
    hires = f"{base}_4k{ext}"
    return hires if os.path.exists(hires) else path


class PhysRect(pygame.Rect):
    """Fyzický obdĺžnik orezania (z Canvas.get_clip) — set_clip ho
    neprepočítava, len obnoví."""


class Canvas:
    """Kreslí v logických súradniciach na fyzický povrch `target` v mierke
    `scale` s posunom (ox, oy) — posun = pásma pri 21:9 a pod.

    Všetky cache (fonty, obrázky, overlaye) patria jednej mierke. Pri
    zmene rozlíšenia sa vytvorí nový Canvas, starý zanikne aj s cache."""

    def __init__(self, target: pygame.Surface, scale: float,
                 ox: int = 0, oy: int = 0):
        self.target = target
        self.s = scale
        self.ox, self.oy = ox, oy
        self._fonts: dict = {}
        self._images: dict = {}
        self._overlays: dict = {}
        self.cache_overlays = True

    # --- prevody --------------------------------------------------------

    def px(self, x: float, y: float) -> tuple[int, int]:
        return (round(x * self.s) + self.ox, round(y * self.s) + self.oy)

    def prect(self, rect) -> pygame.Rect:
        """Logický obdĺžnik → fyzický. Zaokrúhľujú sa oba rohy (nie
        šírka), aby susedné prvky nemali medzi sebou 1px škáry."""
        x, y, w, h = rect
        x0, y0 = self.px(x, y)
        x1, y1 = self.px(x + w, y + h)
        return pygame.Rect(x0, y0, max(1, x1 - x0), max(1, y1 - y0))

    def pw(self, width: float) -> int:
        """Hrúbka čiary: 0 ostáva 0 (= vyplnené), inak aspoň 1 px."""
        return max(1, round(width * self.s)) if width else 0

    def _scale(self, img: pygame.Surface, size, smooth: bool) -> pygame.Surface:
        if img.get_size() == tuple(size):
            return img
        if smooth or self.s != 1:
            return pygame.transform.smoothscale(img, size)
        return pygame.transform.scale(img, size)

    # --- zdroje ---------------------------------------------------------

    def font(self, size: int) -> ScaledFont:
        font = self._fonts.get(size)
        if font is None:
            font = self._fonts[size] = ScaledFont(size, self.s)
        return font

    def card(self, image_name: str, angle: float = 0,
             lsize: tuple[int, int] = CARD_SIZE_MEDIUM,
             smooth: bool = True) -> LSurf:
        """Karta (napr. "heart-ace.png" alebo "card-back.png") v logickej
        veľkosti `lsize`, voliteľne otočená. Zdroj = najmenší asset aspoň
        taký široký ako potrebná fyzická šírka, inak najväčší. Pri mierke
        1 sa vždy berie cards-medium (ako pôvodný kód)."""
        key = ("card", image_name, angle, lsize, smooth)
        cached = self._images.get(key)
        if cached is not None:
            return cached
        pw, ph = round(lsize[0] * self.s), round(lsize[1] * self.s)
        if self.s == 1:
            src_dir = CARDS_MEDIUM_PATH
        else:
            src_dir = _CARD_SOURCES[-1][1]
            for width, path in _CARD_SOURCES:
                if width >= pw:
                    src_dir = path
                    break
        path = os.path.join(src_dir, image_name)
        if not os.path.exists(path):
            # chýbajúci asset v danej veľkosti → stredné karty
            path = os.path.join(CARDS_MEDIUM_PATH, image_name)
        img = pygame.image.load(path).convert_alpha()
        img = self._scale(img, (pw, ph), smooth)
        lw, lh = lsize
        if angle:
            img = pygame.transform.rotate(img, angle)
            if angle % 90 == 0:
                if angle % 180:
                    lw, lh = lh, lw
            else:
                # Ľubovoľný uhol (karty v pozadí menu): logický rozmer
                # otočeného obrázka = fyzický / mierka.
                lw = round(img.get_width() / self.s)
                lh = round(img.get_height() / self.s)
        result = self._images[key] = LSurf(img, lw, lh)
        return result

    def image(self, path: str, lsize: tuple[int, int],
              smooth: bool = True, alpha: bool = True) -> LSurf:
        """Ľubovoľný obrázok (ikony, logo, trofeje) v logickej veľkosti."""
        key = ("img", path, lsize, smooth, alpha)
        cached = self._images.get(key)
        if cached is not None:
            return cached
        img = pygame.image.load(path)
        img = img.convert_alpha() if alpha else img.convert()
        phys = (max(1, round(lsize[0] * self.s)), max(1, round(lsize[1] * self.s)))
        img = self._scale(img, phys, smooth)
        result = self._images[key] = LSurf(img, *lsize)
        return result

    def image_size(self, path: str) -> tuple[int, int]:
        """Pôvodný rozmer obrázka (napr. kvôli pomeru strán loga)."""
        key = ("size", path)
        size = self._images.get(key)
        if size is None:
            size = self._images[key] = pygame.image.load(path).get_size()
        return size

    def background(self, path: str, phys_size: tuple[int, int]) -> pygame.Surface:
        """Pozadie „cover" pre celé okno (vrátane pásiem): zachová pomer
        strán a presah oreže — žiadne naťahovanie."""
        key = ("bg", path, phys_size)
        cached = self._images.get(key)
        if cached is not None:
            return cached
        tw, th = phys_size
        img = pygame.image.load(_hires_variant(path, tw, th)).convert()
        iw, ih = img.get_size()
        if (iw, ih) != (tw, th):
            k = max(tw / iw, th / ih)
            sw, sh = math.ceil(iw * k), math.ceil(ih * k)
            if self.s == 1 and (tw, th) == (1920, 1080):
                # Pôvodný kód: transform.scale na rozmer obrazovky
                img = pygame.transform.scale(img, (tw, th))
            else:
                img = pygame.transform.smoothscale(img, (sw, sh))
                crop = pygame.Rect((sw - tw) // 2, (sh - th) // 2, tw, th)
                img = img.subsurface(crop).copy()
        result = self._images[key] = img
        return result

    def new_surface(self, lsize: tuple[int, int], alpha: bool = True) -> LSurf:
        """Prázdny povrch v logickej veľkosti (fyzicky lsize·s)."""
        phys = (max(1, round(lsize[0] * self.s)), max(1, round(lsize[1] * self.s)))
        surf = pygame.Surface(phys, pygame.SRCALPHA) if alpha else pygame.Surface(phys)
        return LSurf(surf, *lsize)

    # --- kreslenie ------------------------------------------------------

    def blit(self, lsurf: LSurf, pos, special_flags: int = 0):
        if not isinstance(lsurf, LSurf):
            raise TypeError("Canvas.blit očakáva LSurf (z canvas.font/card/"
                            "image), nie pygame.Surface v logických px")
        if hasattr(pos, "topleft"):
            pos = pos.topleft
        self.target.blit(lsurf.phys, self.px(*pos), special_flags=special_flags)

    def rect(self, color, rect, width: float = 0, border_radius: float = 0):
        pygame.draw.rect(self.target, color, self.prect(rect), self.pw(width),
                         border_radius=round(border_radius * self.s))

    def line(self, color, p1, p2, width: float = 1):
        pygame.draw.line(self.target, color, self.px(*p1), self.px(*p2),
                         self.pw(width))

    def circle(self, color, center, radius: float, width: float = 0):
        pygame.draw.circle(self.target, color, self.px(*center),
                           max(1, round(radius * self.s)), self.pw(width))

    def polygon(self, color, points):
        pygame.draw.polygon(self.target, color, [self.px(*p) for p in points])

    def get_clip(self) -> PhysRect:
        return PhysRect(self.target.get_clip())

    def set_clip(self, rect):
        """Logický obdĺžnik, None = bez orezania, alebo fyzický Rect
        vrátený z get_clip()."""
        if rect is None:
            self.target.set_clip(None)
        elif isinstance(rect, PhysRect):
            self.target.set_clip(rect)
        else:
            self.target.set_clip(self.prect(rect))

    def overlay_window(self, rgba):
        """Polopriehľadná vrstva cez CELÉ okno vrátane pásiem (stmavenie
        pozadia v menu a pod.) — logický obdĺžnik by pásma vynechal."""
        size = self.target.get_size()
        key = ("window", size, tuple(rgba))
        surf = self._overlays.get(key)
        if surf is None:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            surf.fill(rgba)
            self._overlays[key] = surf
        self.target.blit(surf, (0, 0))

    def fill_window(self, color):
        self.target.fill(color)

    def overlay(self, rect, rgba, border_radius: float = 0):
        """Polopriehľadný obdĺžnik. Povrch sa cachuje — pôvodný kód
        alokoval nový SRCALPHA povrch každú snímku (pri 4K drahé)."""
        prect = self.prect(rect)
        key = (prect.size, tuple(rgba), border_radius)
        surf = self._overlays.get(key) if self.cache_overlays else None
        if surf is None:
            surf = pygame.Surface(prect.size, pygame.SRCALPHA)
            if border_radius:
                pygame.draw.rect(surf, rgba, surf.get_rect(),
                                 border_radius=round(border_radius * self.s))
            else:
                surf.fill(rgba)
            if self.cache_overlays:
                self._overlays[key] = surf
        self.target.blit(surf, prect.topleft)


TABLE_BG_PATH = os.path.join("assets", "graphics", "table.jpg")


def draw_backdrop(canvas: Canvas, dim_rgba=None, bg_path: str = TABLE_BG_PATH):
    """Pozadie obrazoviek menu: stôl „cover" cez celé okno (aj pásma) a
    voliteľné stmavenie. Náhrada za pôvodné transform.scale na rozmer
    obrazovky + SRCALPHA povrch cez celú obrazovku každú snímku."""
    if os.path.exists(bg_path):
        canvas.target.blit(canvas.background(bg_path, canvas.target.get_size()),
                           (0, 0))
    else:
        canvas.fill_window((45, 28, 15))
    if dim_rgba:
        canvas.overlay_window(dim_rgba)


class StaticLayer:
    """Cache statickej vrstvy obrazovky (výkon pri 4K). Obrazovka si
    vrstvu prekreslí len keď sa zmení `key` (hash viditeľného stavu);
    inak sa celá vrstva len blitne a navrch sa kreslí to, čo sa hýbe.

        if layer.needs_redraw(state_key):
            with layer.drawing(canvas, state_key):
                ...kresli statický obsah cez canvas...
        layer.blit_to(window)
    """

    def __init__(self, size: tuple[int, int]):
        self.surface = pygame.Surface(size).convert()
        self._key = object()

    def needs_redraw(self, key) -> bool:
        return key != self._key

    def drawing(self, canvas: Canvas, key=None):
        layer = self

        class _Ctx:
            def __enter__(self_inner):
                self_inner.prev = canvas.target
                canvas.target = layer.surface
                return canvas

            def __exit__(self_inner, *exc):
                canvas.target = self_inner.prev
                if exc[0] is None:
                    layer._key = key
                return False

        return _Ctx()

    def invalidate(self):
        self._key = object()

    def blit_to(self, target: pygame.Surface):
        target.blit(self.surface, (0, 0))


def draw_static(owner, canvas: Canvas, key, draw_fn):
    """Nakreslí statickú časť obrazovky cez StaticLayer uloženú na
    `owner` (atribút _static_layer): draw_fn() sa zavolá len pri zmene
    `key`, inak sa skopíruje hotová vrstva (jeden blit namiesto
    stmavenia celého okna, desiatok kariet a pod. — výkon pri 4K).
    Výsledok je pixel po pixeli rovnaký ako priame kreslenie."""
    size = canvas.target.get_size()
    layer = getattr(owner, "_static_layer", None)
    if layer is None or layer.surface.get_size() != size:
        layer = owner._static_layer = StaticLayer(size)
    if layer.needs_redraw(key):
        with layer.drawing(canvas, key):
            draw_fn()
    layer.blit_to(canvas.target)
