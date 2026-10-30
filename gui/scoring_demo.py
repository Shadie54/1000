# gui/scoring_demo.py
#
# Krok „Bodovanie“ v Priebehu kola (okno Pravidlá a bodovanie, záložka
# Pravidlá). Kostra animovaného vysvetlenia bodovania (2026-10-29): štyri
# scény, každá ukáže jeden blok z Prehľadu bodovania — kreslí ho TEN ISTÝ
# kód ako záložka Prehľad bodovania (metódy InfoOverlay._draw_card_values,
# _draw_trump_values, _draw_obligation, _draw_others), žiadne kópie.
# Ovládanie (Predchádzajúce / Ďalšie / bodky / Prehrať) a časovanie scén
# preberá z ukážky štichov (TrickRulesDemo).
#
# Ďalšia etapa: vlastné animácie scén (zvýraznenie kariet s bodmi, spojenie
# kráľa a horníka, počítadlo povinnosti, zaokrúhlenie bodov) — každá scéna
# je samostatná metóda _sceneN, čas t v scéne je k dispozícii.

import pygame

from gui import ui_style
from gui.rules_demo import TrickRulesDemo, _ease, _wrap

FADE_STEPS = 16                 # prechod scén — tmavnutie v 16 krokoch


class ScoringDemo(TrickRulesDemo):
    TITLE = "BODOVANIE"
    # Scéna: názov sekcie (ako v Prehľade bodovania), vysvetlenie nad ňou
    SCENES = (
        ("1. HODNOTY KARIET",
         "Za karty v zobratých štichoch získaš ich body. Hodnota závisí "
         "od karty, nie od farby."),
        ("2. TROMFOVÉ HLÁŠKY",
         "Kráľ a horník rovnakej farby. Body za hlášku získaš, keď tromf nahlásiš."),
        ("3. POVINNOSŤ", None),
        ("4. OSTATNÍ HRÁČI", None),
    )
    SCENE_LEN = 9.0
    HOLD_AT = 1.0               # ručne zvolená scéna ostane stáť

    def __init__(self, canvas, blocks):
        # blocks — InfoOverlay: kreslí bloky Prehľadu bodovania do obdĺžnika
        from gui.info_overlay import SuitCycle
        self.blocks = blocks
        self.cycle = SuitCycle()            # karty v 1. scéne menia farbu
        super().__init__(canvas)

    def reset(self):
        super().reset()
        self.cycle.reset()

    def select(self, index: int):
        super().select(index)
        self.cycle.reset()

    # --- rozloženie -------------------------------------------------------

    def scene_rects(self, index: int):
        """(oblasť vysvetlenia alebo None, oblasť sekcie) pre scénu."""
        st = self.stage
        b = self.blocks
        _title, line = self.SCENES[index]
        text = None
        top = st.y
        if line:
            n = len(_wrap(line, self.font_text, st.width - 40))
            text = pygame.Rect(st.x, st.y + 4, st.width,
                               n * (self.font_text.get_height() + 4) + 8)
            top = text.bottom + 10
        avail = st.bottom - top
        need = {0: avail, 1: avail,
                2: b._obligation_height(st.width),
                3: b._others_height(st.width)}[index]
        h = min(avail, need)
        sec = pygame.Rect(st.x, top + (avail - h) // 2, st.width, h)
        return text, sec

    # --- kreslenie --------------------------------------------------------

    def draw(self, mouse_pos):
        t = self._elapsed()
        self._draw_header()
        with self.blocks.unchecked():
            self.draw_scene(self.scene)
        # prechod do ďalšej scény / nábeh scény — tmavnutie obsahu
        dark = 0.0
        if self.playing and t > self.SCENE_LEN - 1:
            dark = _ease(t - (self.SCENE_LEN - 1))
        if t < 0.4:
            dark = max(dark, 1 - _ease(t / 0.4))
        if dark > 0:
            a = round(dark * FADE_STEPS) * 255 // FADE_STEPS
            if a:
                fill = self.blocks.SECTION_FILL[:3]
                self.canvas.overlay(self.stage.inflate(4, 4), (*fill, a))
        self._draw_controls(mouse_pos)

    def draw_scene(self, index: int):
        """Nakreslí scénu (aj pre kontrolu presahov v layout_problems)."""
        c = self.canvas
        b = self.blocks
        title, line = self.SCENES[index]
        text, sec = self.scene_rects(index)
        if text is not None:
            lh = self.font_text.get_height() + 4
            y = text.y + 4
            for ln in _wrap(line, self.font_text, text.width - 40):
                s = self.font_text.render(ln, True, ui_style.TEXT)
                r = s.get_rect(centerx=text.centerx, top=y)
                c.blit(s, r)
                b._fit("bodovanie/vysvetlenie", self.stage, r)
                y += lh
        b._section(sec, title)
        if index == 0:
            row = b._draw_card_values(sec)
            self.cycle.draw(c, row, lambda suit: b._draw_card_row(sec, suit))
        elif index == 1:
            b._draw_trump_values(sec)
        elif index == 2:
            b._draw_obligation(sec)
        else:
            b._draw_others(sec)
        b._fit("bodovanie/sekcia", self.stage.inflate(8, 8), sec)
