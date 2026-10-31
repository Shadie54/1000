"""Všetky scény opakujú vlastný obsah; výber scény je vždy ručný."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['TISIC_RESOLUTION']='1920x1080';os.environ['TISIC_DESKTOP']='1920x1080'
import pygame
from gui import display
from gui.info_overlay import InfoOverlay

def main():
    display.get_surface();o=InfoOverlay(display.canvas())
    demos=(o.rules_demo,o.trump_demo,o.first_trump_demo,o.bidding_demo,o.talon_demo,o.scoring_demo)
    ticks=pygame.time.get_ticks
    try:
        for d in demos:
            for scene in range(len(d.SCENES)):
                pygame.time.get_ticks=lambda:0
                d.select(scene);assert d.playing and d.hold_at is None
                duration=d.SCENE_LEN
                pygame.time.get_ticks=lambda:round(duration*3000+500)
                assert abs(d._elapsed()-.5)<.001 and d.scene==scene
                # Pauza tesne pred koncom nesmie pri pokračovaní posunúť ani vrátiť čas.
                pygame.time.get_ticks=lambda:round(duration*4000-100)
                before=d._elapsed();d.toggle_play();assert not d.playing
                pygame.time.get_ticks=lambda:round(duration*4000+5000)
                assert abs(d._elapsed()-before)<.001
                d.toggle_play();assert d.playing and abs(d._elapsed()-before)<.001
                pygame.time.get_ticks=lambda:round(duration*4000+5200)
                assert abs(d._elapsed()-.1)<.002 and d.scene==scene
            pygame.time.get_ticks=lambda:0
            d.reset();assert d.scene==0 and d.playing
    finally:pygame.time.get_ticks=ticks
    print('OK: všetky scény, vlastné slučky, presná pauza, pokračovanie a reset.')
if __name__=='__main__':main()
