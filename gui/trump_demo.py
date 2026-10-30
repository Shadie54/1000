# gui/trump_demo.py
#
# Podzáložka „Hlásenie tromfu“ v kroku Štichy a tromfy (okno Pravidlá
# a bodovanie, 2026-10-30). Zatiaľ len zástupný obsah v rovnakom
# animačnom priestore ako ukážka štichov — animované vysvetlenie a texty
# pravidiel hlásenia tromfu pripravíme samostatne (podklad:
# InfoOverlay.TRUMP_BULLETS / TRUMP_BULLETS_FIRST_TRICK). Budúce scény
# pôjdu sem ako podtrieda TrickRulesDemo (rovnaké ovládanie a časovanie).

import pygame

from gui import ui_style
from gui.rules_demo import TrickRulesDemo, NAME_DIM, _ease


class TrumpPlaceholder(TrickRulesDemo):
    TITLE = "HLÁSENIE TROMFU"
    SCENES = (("Hlásenie tromfu", ""),)

    def handle_click(self, pos) -> bool:
        return False

    def draw(self, mouse_pos):
        c = self.canvas
        t = (pygame.time.get_ticks() - self._t0) / 1000.0
        fade = _ease(t / 0.4)
        self._draw_header()
        self._draw_stage()
        st = self.stage
        # kráľ a horník — len obrázok, bez textu pravidiel
        w = round(self.cw * 1.05)
        g = round(14 * self.k)
        cy = st.centery - round(40 * self.k)
        for j, rank in enumerate(("king", "over")):
            x = st.centerx + (j * 2 - 1) * (w + g) // 2
            self._card(f"acorn-{rank}", (x, cy), scale=w / self.cw, alpha=fade)
        h = round(w / (181 / 293))
        y = cy + h // 2 + round(26 * self.k)
        title = self.font_title.render("Hlásenie tromfu", True, ui_style.GOLD)
        c.blit(title, title.get_rect(centerx=st.centerx, top=y))
        y += title.get_height() + 8
        info = self.font_text.render("Animované vysvetlenie bude doplnené.", True, NAME_DIM)
        c.blit(info, info.get_rect(centerx=st.centerx, top=y))
