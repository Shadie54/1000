# gui/achievements_screen.py
#
# Dvojpanelové okno TROFEJE (rework 2026-11-01, zadanie usera + GPT):
# vľavo rolovateľný zoznam všetkých trofejí (podľa poradia v definitions.py,
# stupňované pod jednu položku), vpravo detail vybranej trofeje — pri
# stupňovaných aj klikateľné kartičky jednotlivých úrovní. Odhaľovanie
# skrytých podmienok (pozri _tier_states/_single_state nižšie) je čisto
# odvodené z uloženého stavu `data["unlocked"]` — žiadny nový ukladaný
# stav, funguje teda aj po reštarte hry.

import os
import re
import sys

import pygame

from gui import display
from gui.canvas import draw_static
from gui import ui_style
from config import SCREEN_WIDTH, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE
from achievements.definitions import ACHIEVEMENTS, get_tier_name
from achievements.storage import load_achievements

# Vzhľad (grafický rework 2026-10-28, gui/ui_style.py)
DIVIDER = (70, 54, 34)
BORDER_DIM = (90, 72, 48)
# Obrys zamknutej karty (_draw_card_icon) — svetlejší než BORDER_DIM
# (ten zostáva pre riadky v ľavom zozname nezmenený): na tmavomodrom
# pozadí trophybg.png (pravý panel) boli obrysy bronzových a
# platinových zamknutých kariet slabo viditeľné (zadanie usera
# 2026-11-01); karta samotná sa nemení, len jej obrys.
LOCKED_CARD_BORDER = (150, 126, 90)
# Názov zamknutej (nevybranej) trofeje v ľavom zozname — svetlejší než
# TEXT_DIM (zadanie usera 2026-11-01: "tlmená karta, ale názov o niečo
# svetlejší", nech má hráč pri nulovom progrese aspoň čitateľný prehľad
# cieľov). Karta/ikona aj podnadpis ("Zamknutá", počet úrovní) ostávajú
# tlmené (TEXT_DIM) — mení sa len farba samotného názvu.
LOCKED_ROW_NAME = (192, 176, 148)
HEADER_H = 158          # nadpis TROFEJE + ozdobná linka + počet + progress bar

# Vlastné pozadie PRAVÉHO panela "DETAIL TROFEJE" (zadanie usera
# 2026-11-01) — ozdobný zlatý rám na tmavomodrom zamate namiesto plnej
# tmavej výplne; pomer strán obrázka (1080×768) je zámerne blízky
# pomeru strán tohto panela, takže sa pri "cover" prekrytí orezáva len
# minimálne.
TROPHY_BG_PATH = os.path.join("assets", "graphics", "trophybg.png")

STATUS_LABELS = {"unlocked": "Získaná", "revealed": "Odhalená", "hidden": "Skrytá"}
TIER_METAL_NAMES = {"bronze": "Bronz", "silver": "Striebro",
                    "gold": "Zlato", "platinum": "Platina"}
HIDDEN_TEXT = "Podmienka získania je zatiaľ skrytá."
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}

_NUMERAL_SUFFIX_RE = re.compile(r"^(.*?)\s+([IVXLCDM]+\.?)$")


def _group_label(first_item_name: str) -> str:
    """Stabilný (nemenný) názov skupiny v zozname, odvodený z mena prvej
    úrovne — odstráni rímsku číslicu alebo '— <stupeň>' na konci, ak tam
    je ('Ani muk I.' -> 'Ani muk', 'Neporaziteľný — Bronz' -> 'Neporaziteľný'),
    inak necháva meno bezo zmeny ('Začíname', 'Odvážny pokus')."""
    if " — " in first_item_name:
        return first_item_name.split(" — ", 1)[0].strip()
    m = _NUMERAL_SUFFIX_RE.match(first_item_name)
    if m:
        return m.group(1).strip()
    return first_item_name


def _tier_states(items: list, unlocked: dict) -> list:
    """Stav každej úrovne skupiny: 'unlocked' (získaná — popis vždy
    dostupný), 'revealed' (nezískaná, ale podmienka viditeľná — buď nie je
    'hidden', alebo ju odhalilo získanie PREDCHÁDZAJÚCEJ úrovne) alebo
    'hidden' (podmienka zatiaľ skrytá). Prvá úroveň skrytej trofeje je
    'hidden', kým ju hráč nezíska — nemá totiž žiadnu predchádzajúcu
    úroveň, ktorá by ju odomkla."""
    states = []
    prev_unlocked = False
    for item in items:
        is_unlocked = unlocked.get(item["id"], False)
        if is_unlocked:
            states.append("unlocked")
        elif not item.get("hidden", False):
            states.append("revealed")
        elif prev_unlocked:
            states.append("revealed")
        else:
            states.append("hidden")
        prev_unlocked = is_unlocked
    return states


class AchievementsScreen:
    """Zoznam trofejí — dvojpanelové rozhranie (vľavo zoznam, vpravo
    detail). Dva spôsoby použitia:
      - z menu: run() — vlastná slučka, pozadie stola (draw_backdrop),
      - počas hry: AchievementsOverlay nižšie — handle_event() + draw_overlay()
        z hernej slučky, pod panelom je stmavená rozohratá hra."""

    def __init__(self, screen: pygame.Surface | None = None, data: dict | None = None):
        # `screen` (logický povrch) sa už nepoužíva — kreslí sa cez Canvas.
        # data: živé dáta trofejí (AchievementTracker.data); inak zo súboru.
        self.canvas = display.canvas()
        self.H = display.logical_height()
        self.clock = pygame.time.Clock()

        self.font_title = self.canvas.font(FONT_SIZE_LARGE + 8)
        self.font_large = self.canvas.font(FONT_SIZE_LARGE)
        self.font_panel_h = self.canvas.font(FONT_SIZE_MEDIUM + 2)
        self.font_row_name = self.canvas.font(FONT_SIZE_MEDIUM)
        self.font_desc = self.canvas.font(FONT_SIZE_MEDIUM - 2)
        self.font_small = self.canvas.font(FONT_SIZE_MEDIUM - 4)
        self.font_tier = self.canvas.font(FONT_SIZE_MEDIUM - 6)

        # Grafika úrovní — nové podklady (2026-11-01): bronz/striebro/zlato/
        # platina + zámka pre nezískané úrovne (nezávisle od stupňa).
        self.trophy_paths = {}
        for tier_name in ("bronze", "silver", "gold", "platinum"):
            path = f"assets/graphics/trophy_{tier_name}.png"
            self.trophy_paths[tier_name] = path if os.path.exists(path) else None
        lock_path = "assets/graphics/lock.png"
        self.lock_path = lock_path if os.path.exists(lock_path) else None

        self.data = data if data is not None else load_achievements()
        self.scroll_offset = 0
        self.max_scroll = 0

        self.PAD = 30
        self.PANEL_X = 60
        self.PANEL_Y = 20
        self.PANEL_W = SCREEN_WIDTH - 120
        self.PANEL_H = self.H - 40

        # Vyhradený priestor pre tlačidlo späť (mimo scrollovateľnej oblasti)
        self.BACK_AREA_H = 80
        self.CONTENT_Y = self.PANEL_Y + HEADER_H
        self.CONTENT_H = self.PANEL_H - HEADER_H - self.BACK_AREA_H

        self.back_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 150,
            self.PANEL_Y + self.PANEL_H - self.BACK_AREA_H + 15,
            300, 50
        )

        # --- Dvojpanelové rozloženie -------------------------------------
        GAP = 24
        INNER_PAD = 20
        SUBHEADER_H = 50
        left_w = int(self.PANEL_W * 0.36)

        self.left_panel_bg = pygame.Rect(
            self.PANEL_X + self.PAD, self.CONTENT_Y,
            left_w - self.PAD, self.CONTENT_H)
        right_x = self.left_panel_bg.right + GAP
        self.right_panel_bg = pygame.Rect(
            right_x, self.CONTENT_Y,
            self.PANEL_X + self.PANEL_W - self.PAD - right_x, self.CONTENT_H)

        self.left_rect = pygame.Rect(
            self.left_panel_bg.x + INNER_PAD,
            self.left_panel_bg.y + SUBHEADER_H,
            self.left_panel_bg.width - 2 * INNER_PAD,
            self.left_panel_bg.height - SUBHEADER_H - INNER_PAD)
        self.right_content = pygame.Rect(
            self.right_panel_bg.x + INNER_PAD,
            self.right_panel_bg.y + SUBHEADER_H,
            self.right_panel_bg.width - 2 * INNER_PAD,
            self.right_panel_bg.height - SUBHEADER_H - INNER_PAD)

        self.row_h = 82
        self._build_rows()

        self.selected_index = 0
        self.selected_tier = 0
        self._select_row(0)

    # ------------------------------------------------------------------
    # Príprava riadkov a výberu
    # ------------------------------------------------------------------

    def _build_rows(self):
        """Zoskupí achievementy — stupňované pod seba, ostatné samostatne.
        Poradie ACHIEVEMENTS v definitions.py určuje poradie zobrazenia aj
        poradie úrovní v rámci skupiny."""
        self.rows = []
        seen_groups = set()

        for a in ACHIEVEMENTS:
            group = a.get("group")
            if group:
                if group in seen_groups:
                    continue
                seen_groups.add(group)
                items = [x for x in ACHIEVEMENTS if x.get("group") == group]
                self.rows.append({"type": "group", "items": items,
                                  "label": _group_label(items[0]["name"])})
            else:
                self.rows.append({"type": "single", "item": a})

        total_h = len(self.rows) * self.row_h
        self.max_scroll = max(0, total_h - self.left_rect.height)

    def _select_row(self, index: int, keep_tier: bool = False):
        if not self.rows:
            return
        index = max(0, min(index, len(self.rows) - 1))
        self.selected_index = index
        row = self.rows[index]
        if row["type"] == "group" and not keep_tier:
            items = row["items"]
            unlocked_idx = [i for i, it in enumerate(items)
                            if self.data["unlocked"].get(it["id"], False)]
            self.selected_tier = unlocked_idx[-1] if unlocked_idx else 0
        elif row["type"] != "group":
            self.selected_tier = 0
        self._ensure_row_visible(index)

    def _ensure_row_visible(self, index: int):
        row_top = index * self.row_h
        row_bottom = row_top + self.row_h
        view_h = self.left_rect.height
        if row_top < self.scroll_offset:
            self.scroll_offset = row_top
        elif row_bottom > self.scroll_offset + view_h:
            self.scroll_offset = row_bottom - view_h
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def _row_slot_rect(self, index: int) -> pygame.Rect:
        y = self.left_rect.y - self.scroll_offset + index * self.row_h
        return pygame.Rect(self.left_rect.x, y, self.left_rect.width, self.row_h)

    def _row_tier_and_unlocked(self, row: dict) -> tuple:
        """Stupeň (farba karty) a stav odomknutia pre riadok zoznamu —
        pri skupine farba NAJVYŠŠEJ odomknutej úrovne (alebo prvej, ak
        ešte žiadna nie je odomknutá — karta sa vtedy vykreslí zamknutá)."""
        if row["type"] == "single":
            item = row["item"]
            return "gold", self.data["unlocked"].get(item["id"], False)
        items = row["items"]
        unlocked_idx = [i for i, it in enumerate(items)
                        if self.data["unlocked"].get(it["id"], False)]
        if unlocked_idx:
            idx = unlocked_idx[-1]
            return get_tier_name(items[idx]["id"]), True
        return get_tier_name(items[0]["id"]), False

    # ------------------------------------------------------------------
    # Rozloženie pravého panela (zdieľané kreslením aj klikaním)
    # ------------------------------------------------------------------

    def _group_layout(self, row: dict) -> dict:
        """Rozloženie "zbierkového režimu" (stupňovaná trofej, spresnené
        2026-11-01 kolo 4 podľa pripomienok k 1. verzii): hlavná karta —
        dominanta detailu, len o niečo menšia než vo "výstavnom" režime
        (predtým pôsobila rovnako veľká ako kartičky úrovní) — vľavo,
        vpravo text vybranej úrovne; TESNE pod nimi (menší odstup než
        predtým) rad kartičiek všetkých úrovní — veľkosť kartičiek
        NEMENENÁ (pri 4 úrovniach takmer ideálna, ďalšie zväčšovanie by
        robilo problémy pri menších rozlíšeniach). Horný blok (karta+text)
        aj spodný rad kartičiek sú súčasťou JEDNEJ kompozície so spoločnou
        šírkou — rad sa centruje POD blokom (nie nezávisle v celom
        paneli), takže už nepôsobia oddelene; celá kompozícia je navyše
        vertikálne vycentrovaná v dostupnom priestore pravého panela."""
        rc = self.right_content
        items = row["items"]
        n = len(items)
        ratio = 341 / 512

        CARD_W = 190                    # dominanta detailu (bolo 150)
        card_h = round(CARD_W / ratio)
        GAP_CARD_TEXT = 28
        TEXT_W = 420

        TIER_W = 130                    # nemenené — pri 4 úrovniach ideálne
        GAP = 22
        tier_h = round(TIER_W / ratio)
        total_tier_w = n * TIER_W + (n - 1) * GAP

        # Spoločná šírka kompozície — horný blok aj rad kartičiek sa
        # centrujú POD TÝMTO istým blokom, nie každý zvlášť v paneli.
        block_w = max(CARD_W + GAP_CARD_TEXT + TEXT_W, total_tier_w)
        block_x = rc.x + max(0, (rc.width - block_w) // 2)

        GAP_CARD_ROW = 26                # 2026-11-01: o niečo voľnejšie
        LABEL_H = self.font_small.get_height()
        GAP_LABEL_ROW = 14               # než hneď po kole 4 (bolo 18/8 — natesno)
        # Rímska číslica + názov kovu pod kartičkou (_draw_tier_card) —
        # odstupy musia presne sedieť s tými tam (inak sa pri vycentrovaní
        # kompozície buď zbytočne stráca miesto, alebo sa text naopak
        # zrazí so selekčným rámikom kartičky).
        CAPTION_H = (14 + self.font_row_name.get_height()
                    + 4 + self.font_tier.get_height())

        total_h = (card_h + GAP_CARD_ROW + LABEL_H + GAP_LABEL_ROW
                  + tier_h + CAPTION_H)
        start_y = rc.y + max(0, (rc.height - total_h) // 2)

        icon_rect = pygame.Rect(block_x, start_y, CARD_W, card_h)
        text_x = icon_rect.right + GAP_CARD_TEXT
        text_rect = pygame.Rect(text_x, start_y,
                                max(1, block_x + block_w - text_x), card_h)

        label_y = start_y + card_h + GAP_CARD_ROW
        tier_y = label_y + LABEL_H + GAP_LABEL_ROW
        tier_start_x = block_x + (block_w - total_tier_w) / 2
        tier_rects = [pygame.Rect(round(tier_start_x + i * (TIER_W + GAP)), tier_y,
                                  TIER_W, tier_h) for i in range(n)]

        return {"icon_rect": icon_rect, "text_rect": text_rect,
               "label_y": label_y, "label_h": LABEL_H,
               "label_center_x": round(tier_start_x + total_tier_w / 2),
               "divider_half_w": block_w / 2,
               "tier_rects": tier_rects}

    def _tier_card_rects(self) -> list:
        if not self.rows:
            return []
        row = self.rows[self.selected_index]
        if row["type"] != "group":
            return []
        return self._group_layout(row)["tier_rects"]

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(60)
            mouse_pos = display.mouse_pos()

            for event in display.get_events():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.handle_event(event) == "close":
                    return

            self._draw(mouse_pos)
            display.present()

    def handle_event(self, event) -> str | None:
        """Klávesy a myš okna trofejí. Vráti "close" pri Esc / Späť."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.back_button.collidepoint(event.pos):
                    return "close"
                if self.left_rect.collidepoint(event.pos):
                    for i in range(len(self.rows)):
                        slot = self._row_slot_rect(i)
                        if slot.bottom < self.left_rect.top or slot.top > self.left_rect.bottom:
                            continue
                        if slot.collidepoint(event.pos):
                            self._select_row(i)
                            break
                elif self.right_content.collidepoint(event.pos):
                    for i, rect in enumerate(self._tier_card_rects()):
                        if rect.collidepoint(event.pos):
                            self.selected_tier = i
                            break
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 50)
            if event.button == 5:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
        return None

    # ------------------------------------------------------------------
    # Kreslenie — vrchná úroveň
    # ------------------------------------------------------------------

    def _draw(self, mouse_pos):
        draw_static(self, self.canvas,
                    ("trofeje", self.scroll_offset, self.selected_index, self.selected_tier),
                    self._draw_static)
        self._draw_back_button(mouse_pos)

    def _draw_static(self):
        ui_style.draw_backdrop(self.canvas)
        self._draw_content()

    def _draw_content(self):
        self._draw_panel_bg()
        self._draw_title()
        self._draw_progress()
        self._draw_left_panel_bg()
        self._draw_rows()
        self._draw_detail_panel()

    def draw_overlay(self, mouse_pos):
        """Kreslenie počas hry — cez stmavenú hernú obrazovku. Pod panelom
        ostáva obraz hry z chvíle otvorenia (vidno z neho len okraje), aby
        sa celý zoznam nekreslil každú snímku (pri 4K ~40 ms)."""
        if getattr(self, "_game_frame", None) is None:
            self._game_frame = self.canvas.target.copy()
        draw_static(self, self.canvas,
                    ("hra", self.scroll_offset, self.selected_index, self.selected_tier),
                    self._draw_over_game)
        self._draw_back_button(mouse_pos)

    def _draw_over_game(self):
        self.canvas.target.blit(self._game_frame, (0, 0))
        self.canvas.overlay_window((0, 0, 0, 200))
        self._draw_content()

    # ------------------------------------------------------------------
    # Hlavička
    # ------------------------------------------------------------------

    def _draw_panel_bg(self):
        panel = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H)
        ui_style.draw_panel(self.canvas, panel)
        line_y = self.PANEL_Y + self.PANEL_H - self.BACK_AREA_H
        self.canvas.line(DIVIDER, (self.PANEL_X + 24, line_y),
                         (self.PANEL_X + self.PANEL_W - 24, line_y), width=1)

    def _draw_title(self):
        ui_style.draw_screen_title(self.canvas, "TROFEJE", self.font_title,
                                   (SCREEN_WIDTH // 2, self.PANEL_Y + 44),
                                   line_half_w=220, line_gap=36)

    def _draw_progress(self):
        c = self.canvas
        total = len(ACHIEVEMENTS)
        unlocked = sum(1 for v in self.data["unlocked"].values() if v)
        pct = unlocked / total if total else 0.0

        label_cy = self.PANEL_Y + 96
        surf = self.font_desc.render(f"Odomknuté {unlocked} z {total}", True,
                                     ui_style.TEXT_DIM)
        c.blit(surf, surf.get_rect(centerx=SCREEN_WIDTH // 2, centery=label_cy))

        BAR_W, BAR_H = 460, 14
        bar_x = SCREEN_WIDTH // 2 - BAR_W // 2
        bar_y = label_cy + 18
        track = pygame.Rect(bar_x, bar_y, BAR_W, BAR_H)
        c.overlay(track, (20, 14, 9, 230), border_radius=BAR_H // 2)
        c.rect(ui_style.GOLD_SOFT, track, width=1, border_radius=BAR_H // 2)
        fill_w = round(BAR_W * pct)
        if fill_w > 0:
            fill = pygame.Rect(bar_x, bar_y, max(BAR_H, fill_w), BAR_H)
            fill.width = min(fill.width, BAR_W)
            c.overlay(fill, (*ui_style.GOLD, 255), border_radius=BAR_H // 2)

        pct_surf = self.font_small.render(f"{round(pct * 100)} %", True, ui_style.GOLD)
        c.blit(pct_surf, pct_surf.get_rect(midleft=(bar_x + BAR_W + 14,
                                                     bar_y + BAR_H // 2)))

    # ------------------------------------------------------------------
    # Ľavý panel — zoznam
    # ------------------------------------------------------------------

    def _draw_left_panel_bg(self):
        ui_style.draw_panel(self.canvas, self.left_panel_bg, "PREHĽAD TROFEJÍ",
                            self.font_panel_h, title_x=20, title_cy=26, divider_y=46)

    def _draw_rows(self):
        clip_rect = self.left_rect
        old_clip = self.canvas.get_clip()
        self.canvas.set_clip(clip_rect)

        for i, row in enumerate(self.rows):
            slot = self._row_slot_rect(i)
            if slot.bottom < clip_rect.top or slot.top > clip_rect.bottom:
                continue
            self._draw_row(row, slot, i == self.selected_index)

        self.canvas.set_clip(old_clip)

    def _draw_row(self, row: dict, slot: pygame.Rect, selected: bool):
        c = self.canvas
        bg = pygame.Rect(slot.x, slot.y + 4, slot.width, self.row_h - 8)
        tier_name, any_unlocked = self._row_tier_and_unlocked(row)

        fill = (56, 40, 20, 215) if any_unlocked else (20, 14, 9, 170)
        if selected:
            # Výraznejšie zvýraznenie vybranej položky než pri bežnej
            # odomknutej trofeji: jasnejšia výplň, hrubší zlatý rám,
            # zvislý akcentový pruh vľavo.
            c.overlay(bg, (255, 214, 140, 30), border_radius=10)
            c.overlay(bg, fill, border_radius=10)
            c.rect(ui_style.GOLD, bg, width=3, border_radius=10)
            accent = pygame.Rect(bg.x, bg.y + 6, 5, bg.height - 12)
            c.overlay(accent, (*ui_style.GOLD, 255), border_radius=3)
        else:
            c.overlay(bg, fill, border_radius=10)
            border = ui_style.GOLD_SOFT if any_unlocked else BORDER_DIM
            c.rect(border, bg, width=1, border_radius=10)

        icon_size = self.row_h - 26
        icon_box = pygame.Rect(0, 0, icon_size, icon_size)
        icon_box.center = (bg.x + 14 + icon_size // 2, bg.centery)
        self._draw_card_icon(tier_name, icon_box, any_unlocked)

        text_x = icon_box.right + 16
        name = row["label"] if row["type"] == "group" else row["item"]["name"]
        name_color = ui_style.GOLD if any_unlocked else LOCKED_ROW_NAME
        name_surf = self.font_row_name.render(name, True, name_color)
        c.blit(name_surf, (text_x, bg.y + 12))

        if row["type"] == "group":
            unlocked_count = sum(1 for it in row["items"]
                                 if self.data["unlocked"].get(it["id"], False))
            sub = f"{unlocked_count} z {len(row['items'])} úrovní"
        else:
            sub = "Získaná" if any_unlocked else "Zamknutá"
        sub_color = ui_style.TEXT if any_unlocked else ui_style.TEXT_DIM
        sub_surf = self.font_small.render(sub, True, sub_color)
        c.blit(sub_surf, (text_x, bg.y + 12 + name_surf.get_height() + 4))

    # ------------------------------------------------------------------
    # Pravý panel — detail
    # ------------------------------------------------------------------

    def _draw_right_panel_bg(self):
        # Jediné počítadlo trofejí je v hlavičke (_draw_progress) —
        # tu sa už žiadne druhé (predtým "X/Y" pozícia v zozname) nekreslí.
        c = self.canvas
        rect = self.right_panel_bg
        if TROPHY_BG_PATH and os.path.exists(TROPHY_BG_PATH):
            # Vlastné pozadie (zadanie usera) namiesto plnej tmavej výplne
            # draw_panel — obrázok "cover" orezaný na rozmer panela, plus
            # jemné stmavenie navrchu kvôli čitateľnosti textu a kariet.
            pr = c.prect(rect)
            c.target.blit(c.background(TROPHY_BG_PATH, pr.size), pr.topleft)
            c.overlay(rect, (10, 8, 14, 110), border_radius=ui_style.PANEL_RADIUS)
            # Samotný obrázok má hore vlastnú ozdobnú kresbu — zlatý text
            # nadpisu by v nej ľahko zanikol, tak pod ním ešte tmavší pás
            # (len hlavička, zvyšok panela nech presvitá viac).
            band = pygame.Rect(rect.x, rect.y, rect.width, 50)
            c.overlay(band, (8, 6, 10, 165))
        else:
            c.overlay(rect, ui_style.PANEL_FILL, border_radius=ui_style.PANEL_RADIUS)
        c.rect(ui_style.GOLD_SOFT, rect, width=2, border_radius=ui_style.PANEL_RADIUS)
        label_shadow = self.font_panel_h.render("DETAIL TROFEJE", True, (0, 0, 0))
        c.blit(label_shadow, (self.right_panel_bg.x + 21, self.right_panel_bg.y + 17))
        label = self.font_panel_h.render("DETAIL TROFEJE", True, ui_style.GOLD)
        c.blit(label, (self.right_panel_bg.x + 20, self.right_panel_bg.y + 16))
        c.line(DIVIDER, (self.right_panel_bg.x + 24, self.right_panel_bg.y + 46),
              (self.right_panel_bg.right - 24, self.right_panel_bg.y + 46), width=1)

    def _draw_detail_panel(self):
        self._draw_right_panel_bg()
        if not self.rows:
            return
        row = self.rows[self.selected_index]
        if row["type"] == "group":
            self._draw_group_detail(row)
        else:
            self._draw_single_detail(row["item"])

    def _draw_status_line(self, text: str, color, locked: bool, x: int, y: int,
                          align: str = "left") -> int:
        """Stav (Získaná/Odhalená/Skrytá/Zamknutá) — pri nezískanej karte
        aj s malou ikonou zámku pred textom (tá istá `lock.png`). Vráti
        výšku riadku, nech volajúci vie posunúť `y` ďalej."""
        c = self.canvas
        text_surf = self.font_desc.render(text, True, color)
        icon_size = text_surf.get_height()
        gap = 6
        show_icon = locked and self.lock_path is not None
        total_w = (icon_size + gap if show_icon else 0) + text_surf.get_width()
        start_x = (x - total_w // 2) if align == "center" else x
        cx = start_x
        if show_icon:
            img = c.image(self.lock_path, (icon_size, icon_size), smooth=True)
            c.blit(img, (cx, y))
            cx += icon_size + gap
        c.blit(text_surf, (cx, y))
        return text_surf.get_height()

    def _draw_single_detail(self, item: dict):
        """"Výstavný režim" (samostatná trofej, zadanie 2026-11-01 kolo 3):
        veľká karta vycentrovaná v paneli, pod ňou názov/stav/podmienka,
        celá kompozícia vertikálne vycentrovaná (nielen pritlačená hore).
        Žiadny prepínač úrovní — samostatná trofej nemá viac stupňov."""
        c = self.canvas
        rc = self.right_content
        is_unlocked = self.data["unlocked"].get(item["id"], False)
        show_desc = is_unlocked or not item.get("hidden", False)
        status_text = "Získaná" if is_unlocked else "Zamknutá"
        status_color = ui_style.GOLD if is_unlocked else ui_style.TEXT_DIM
        text = item["description"] if show_desc else HIDDEN_TEXT
        text_color = ui_style.TEXT if show_desc else ui_style.TEXT_DIM

        ratio = 341 / 512
        CARD_W = 210
        card_h = round(CARD_W / ratio)

        TEXT_W = min(rc.width, 520)
        line_h = self.font_desc.get_height() + 6
        lines = self._wrap_text(text, self.font_desc, TEXT_W)[:4]
        desc_h = len(lines) * line_h

        name_h = self.font_large.get_height()
        status_h = self.font_desc.get_height()
        GAP_CARD_NAME, GAP_NAME_STATUS, GAP_STATUS_DESC = 22, 8, 16

        total_h = (card_h + GAP_CARD_NAME + name_h + GAP_NAME_STATUS
                  + status_h + GAP_STATUS_DESC + desc_h)
        start_y = rc.y + max(0, (rc.height - total_h) // 2)

        card_box = pygame.Rect(0, start_y, CARD_W, card_h)
        card_box.centerx = rc.centerx
        self._draw_card_icon("gold", card_box, is_unlocked)

        y = card_box.bottom + GAP_CARD_NAME
        name_surf = self.font_large.render(item["name"], True, ui_style.GOLD)
        c.blit(name_surf, name_surf.get_rect(centerx=rc.centerx, top=y))
        y += name_h + GAP_NAME_STATUS

        y += self._draw_status_line(status_text, status_color, not is_unlocked,
                                    rc.centerx, y, align="center") + GAP_STATUS_DESC

        for i, line in enumerate(lines):
            surf = self.font_desc.render(line, True, text_color)
            c.blit(surf, surf.get_rect(centerx=rc.centerx, top=y + i * line_h))

    def _draw_group_detail(self, row: dict):
        """"Zbierkový režim" (stupňovaná trofej): hlavná karta + text
        vybranej úrovne vedľa seba, pod tým rad kartičiek všetkých úrovní
        (geometria z `_group_layout`, zdieľaná aj s klikaním)."""
        c = self.canvas
        items = row["items"]
        tier = min(self.selected_tier, len(items) - 1)
        item = items[tier]
        is_unlocked = self.data["unlocked"].get(item["id"], False)
        tier_name = get_tier_name(item["id"])
        states = _tier_states(items, self.data["unlocked"])
        state = states[tier]

        layout = self._group_layout(row)
        self._draw_card_icon(tier_name, layout["icon_rect"], is_unlocked)

        rect = layout["text_rect"]
        name_surf = self.font_large.render(row["label"], True, ui_style.GOLD)
        c.blit(name_surf, (rect.x, rect.y))
        y = rect.y + name_surf.get_height() + 8

        roman = ROMAN.get(tier + 1, str(tier + 1))
        metal = TIER_METAL_NAMES.get(tier_name, "")
        level_label = f"Úroveň {roman}. · {metal}" if metal else f"Úroveň {roman}."
        lvl_surf = self.font_row_name.render(level_label, True, ui_style.TEXT)
        c.blit(lvl_surf, (rect.x, y))
        y += lvl_surf.get_height() + 8

        status_color = {"unlocked": ui_style.GOLD, "revealed": ui_style.TEXT,
                        "hidden": ui_style.TEXT_DIM}[state]
        y += self._draw_status_line(STATUS_LABELS[state], status_color,
                                    state != "unlocked", rect.x, y) + 12

        c.line(DIVIDER, (rect.x, y), (rect.right, y), width=1)
        y += 16

        show_desc = state in ("unlocked", "revealed")
        text = item["description"] if show_desc else HIDDEN_TEXT
        text_color = ui_style.TEXT if show_desc else ui_style.TEXT_DIM
        self._draw_wrapped(text, rect.x, y, rect.width, max(0, rect.bottom - y), text_color)

        ui_style.draw_divider_label(
            c, "ÚROVNE TROFEJE", self.font_small,
            (layout["label_center_x"], layout["label_y"] + layout["label_h"] // 2),
            half_w=layout["divider_half_w"])

        for i, (it, cr) in enumerate(zip(items, layout["tier_rects"])):
            self._draw_tier_card(it, cr, states[i], selected=(i == tier), index=i)

    def _draw_tier_card(self, item: dict, rect: pygame.Rect, state: str,
                        selected: bool, index: int):
        c = self.canvas
        tier_name = get_tier_name(item["id"])
        self._draw_card_icon(tier_name, rect, state == "unlocked")
        if selected:
            # Samostatný VONKAJŠÍ výberový rám s medzerou od karty — pri
            # odomknutej (už zlato orámovanej) karte by rám v rovnakých
            # hraniciach s výberom splýval s jej vlastným okrajom.
            c.rect(ui_style.GOLD, rect.inflate(10, 10), width=3, border_radius=9)
        if state == "unlocked":
            self._draw_check_badge((rect.x + 13, rect.y + 13), 10)

        color = ui_style.GOLD if state == "unlocked" else ui_style.TEXT_DIM
        # Rímska číslica podľa POZÍCIE v skupine (nie z mena) — niektoré
        # skupiny (napr. Začíname/Rozbehnutý/Stará škola/Legenda) ju
        # v názve vôbec nemajú, popisok úrovne má byť ale vždy rovnaký.
        roman = ROMAN.get(index + 1, str(index + 1))
        metal = TIER_METAL_NAMES.get(tier_name, "")
        # +14 (nie len +6) — kartička má pri výbere rámik inflatnutý o
        # 5px navyše (rect.inflate(10, 10)), text sa doň predtým takmer
        # dotýkal.
        y = rect.bottom + 14
        if roman:
            r_surf = self.font_row_name.render(roman, True, color)
            c.blit(r_surf, r_surf.get_rect(centerx=rect.centerx, top=y))
            y += r_surf.get_height() + 4
        if metal:
            m_surf = self.font_tier.render(metal, True, color)
            c.blit(m_surf, m_surf.get_rect(centerx=rect.centerx, top=y))

    def _draw_check_badge(self, center: tuple, radius: int):
        c = self.canvas
        c.circle(ui_style.GOLD, center, radius)
        c.circle((20, 14, 8), center, radius, width=2)
        cx, cy = center
        p1 = (cx - radius * 0.45, cy)
        p2 = (cx - radius * 0.05, cy + radius * 0.4)
        p3 = (cx + radius * 0.5, cy - radius * 0.35)
        c.line((20, 14, 8), p1, p2, width=2)
        c.line((20, 14, 8), p2, p3, width=2)

    # ------------------------------------------------------------------
    # Spoločné vizuálne prvky
    # ------------------------------------------------------------------

    def _draw_card_icon(self, tier_name: str, box: pygame.Rect, unlocked: bool):
        """Trofejová karta (pomer strán 341:512 VŽDY zachovaný — vykreslí
        sa proporcionálne a vystredene v `box`, nikdy sa nedeformuje) v
        ľavom zozname, hlavnom detaile aj kartičkách úrovní.

        Odomknutá = plná farba danej úrovne. Zamknutá = TÁ ISTÁ kovová
        karta (rovnaké rozmery), len stmavená a prekrytá ikonou zámku —
        odhalenie podmienky túto kresbu neovplyvňuje, mení sa výhradne
        podľa skutočného stavu odomknutia danej úrovne."""
        c = self.canvas
        ratio = 341 / 512
        if box.width / box.height > ratio:
            card_h = box.height
            card_w = round(card_h * ratio)
        else:
            card_w = box.width
            card_h = round(card_w / ratio)
        card_rect = pygame.Rect(0, 0, max(1, card_w), max(1, card_h))
        card_rect.center = box.center

        path = self.trophy_paths.get(tier_name)
        if path:
            img = c.image(path, (card_rect.width, card_rect.height), smooth=True)
            c.blit(img, card_rect.topleft)
        else:
            c.overlay(card_rect, (30, 22, 14, 230), border_radius=6)

        if unlocked:
            c.rect(ui_style.GOLD, card_rect, width=2, border_radius=6)
        else:
            c.overlay(card_rect, (0, 0, 0, 165), border_radius=6)
            c.rect(LOCKED_CARD_BORDER, card_rect, width=2, border_radius=6)
            if self.lock_path:
                lock_side = max(14, int(min(card_rect.width, card_rect.height) * 0.42))
                lock_rect = pygame.Rect(0, 0, lock_side, lock_side)
                lock_rect.center = card_rect.center
                limg = c.image(self.lock_path, (lock_rect.width, lock_rect.height),
                              smooth=True)
                c.blit(limg, lock_rect.topleft)
            else:
                q_font = c.font(int(min(card_rect.width, card_rect.height) * 0.4))
                q_surf = q_font.render("?", True, ui_style.TEXT_DIM)
                c.blit(q_surf, q_surf.get_rect(center=card_rect.center))
        return card_rect

    def _draw_wrapped(self, text: str, x: int, y: int, max_w: int,
                      max_h: int, color):
        lines = self._wrap_text(text, self.font_desc, max_w)
        line_h = self.font_desc.get_height() + 6
        max_lines = max(1, int(max_h // line_h))
        for i, line in enumerate(lines[:max_lines]):
            surf = self.font_desc.render(line, True, color)
            self.canvas.blit(surf, (x, y + i * line_h))

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def _draw_back_button(self, mouse_pos):
        ui_style.draw_button(self.canvas, self.back_button, "← Späť",
                             self.font_large, 3,
                             self.back_button.collidepoint(mouse_pos))

    def __repr__(self):
        return "AchievementsScreen()"


class AchievementsOverlay:
    """Trofeje počas hry (tlačidlo Trofeje na hernej obrazovke) — rovnaký
    vzhľad ako obrazovka Trofeje v menu. Hra pod ním beží ďalej rovnako
    ako pod prehľadom Pravidlá."""

    def __init__(self, tracker=None):
        self.tracker = tracker
        self.view: AchievementsScreen | None = None

    @property
    def visible(self) -> bool:
        return self.view is not None

    @property
    def covers_screen(self) -> bool:
        """True keď už má obraz hry pod sebou — kreslí celé okno sám."""
        return getattr(self.view, "_game_frame", None) is not None

    def show(self):
        # Živé dáta trackera — trofej odomknutá v tejto hre je hneď vidieť
        data = self.tracker.data if self.tracker is not None else None
        self.view = AchievementsScreen(data=data)

    def hide(self):
        self.view = None

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def handle_event(self, event) -> bool:
        """True = udalosť spracovaná (klik cez overlay sa do hry nedostane)."""
        if self.view is None or event.type == pygame.QUIT:
            return False
        if self.view.handle_event(event) == "close":
            self.hide()
            return True
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP)

    def draw(self):
        if self.view is not None:
            self.view.draw_overlay(display.mouse_pos())
