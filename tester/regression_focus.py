"""Navigácia a rozloženie sústredenej animácie bez viditeľného okna."""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['TISIC_RESOLUTION'] = sys.argv[1] if len(sys.argv) > 1 else '1920x1080'
os.environ['TISIC_DESKTOP'] = os.environ['TISIC_RESOLUTION']
import pygame
from gui import display
from gui.info_overlay import InfoOverlay

def click(o, rect):
    o.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

def main():
    display.get_surface()
    o = InfoOverlay(display.canvas())
    o.show()
    o.active_tab = 'pravidla'
    original_height = o.rules_demo.stage.height
    assert not o.focused and o.chapter==-1
    # Všetkých šesť kapitol má text vo svojich paneloch, vrátane úvodného cieľa.
    for chapter in range(-1,5):
        o.chapter=chapter
        o._checks=[]
        o._draw_rules()
        assert all(panel.inflate(-8,-8).contains(content)
                   for name,panel,content in o._checks)
    o.chapter=-1
    for i in range(5):
        click(o, o._chapter_rects()[i+1])
        assert not o.focused and o.chapter==i
        click(o, o._chapter_open_rect())
        if i == 0:
            # Rozdanie nemá animovanú ukážku — tlačidlo sa nezobrazuje,
            # klik v tej oblasti (teraz súčasť galérie) nič neotvorí.
            assert not o.focused and o.chapter == i
            continue
        if i == 4:
            # Bodovanie: tlačidlo „Prejsť na prehľad bodovania“ neotvára
            # ukážku, len prepne záložku (redizajn 2026-11-01).
            assert not o.focused and o.active_tab == 'bodovanie' and o.chapter == i
            continue
        assert o.focused and o.step == i
        assert o.rules_demo.stage.height > original_height + 200
        o.draw()
        d = o.step_demos.get(i)
        if d:
            demos = d.demos if hasattr(d, 'demos') else (d,)
            for j, item in enumerate(demos):
                if hasattr(d, 'tab_rects'):
                    click(o, d.tab_rects[j])
                    assert d.tab == j
                click(o, item.btn_next)
                assert item.scene == 1
                click(o, item.btn_prev)
                assert item.scene == 0
                click(o, item.dots[1])
                assert item.scene == 1
                playing = item.playing
                click(o, item.btn_play)
                assert item.playing != playing
                click(o, item.btn_play)
                assert item.playing == playing
            scene = demos[-1].scene
        click(o, o.btn_back)
        assert not o.focused and o.visible and o.chapter==i
        click(o, o._chapter_rects()[i+1])
        assert not o.focused and o.chapter==i
        click(o, o._chapter_open_rect())
        if d:
            assert demos[-1].scene == scene
        o.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert not o.focused and o.visible and o.chapter==i
    click(o, o.tab_rects['bodovanie'])
    assert o.active_tab == 'bodovanie'
    click(o, o.tab_rects['pravidla'])
    o.select_step(3)
    # Návrat na prehľad zmrazí čas bez zmeny scény a prehrávania.
    d = o.tricks_step.current
    ticks = pygame.time.get_ticks
    try:
        pygame.time.get_ticks = lambda: 10000
        d._t0 = 8000
        state = (d.scene, d.playing, d.hold_at)
        o._set_focused(False)
        pygame.time.get_ticks = lambda: 40000
        o.select_step(3)
        assert d._t0 == 38000 and (d.scene, d.playing, d.hold_at) == state
    finally:
        pygame.time.get_ticks = ticks
    problems = o.layout_problems()
    assert not problems, '\n'.join(problems)
    o.draw()
    if len(sys.argv) > 2:
        pygame.image.save(o.canvas.target, sys.argv[2])
    print('OK: fokus, 5 fáz, 3 podzáložky, návrat, prehrávanie a rozloženie.')

if __name__ == '__main__':
    main()
