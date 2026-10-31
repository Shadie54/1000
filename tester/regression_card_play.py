"""Viditeľný pôvod, otočenie a odobratie karty v tutoriáli."""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['TISIC_RESOLUTION'] = sys.argv[1] if len(sys.argv)>1 else '1920x1080'
os.environ['TISIC_DESKTOP'] = os.environ['TISIC_RESOLUTION']
import pygame
from gui import display
from gui.info_overlay import InfoOverlay
from gui.rules_demo import CARD_RATIO
from gui.trump_demo import CLASSIC_TRICK

def main():
    display.get_surface()
    o = InfoOverlay(display.canvas())
    o.show();o.active_tab='pravidla';o.select_step(3)
    for d in o.tricks_step.demos:
        original=d._card
        calls=[]
        d._card=lambda name,pos,*args,**kw:calls.append((name,pos,args,kw))
        for player in (0,1,2):
            for t in (0,.5,1.25,1.49,1.51,1.75,2):
                calls.clear()
                k=d._play_from_hand(player,'leaf-king',t,1,.5,1)
                fronts=[c for c in calls if c[0]=='leaf-king']
                if player==0 or k>=.5: assert len(fronts)==1
                else: assert not fronts
                if t<=1:
                    assert calls[-1][1]==(d.hand_pos(0,1) if player==0 else d.seat[player])
                if t>=1.5:
                    assert calls[-1][1]==d.spot[player]
                    assert sum(c[0]=='card-back' for c in calls)==(0 if player==0 else 2)
        calls.clear()
        d._hand(('leaf-king','leaf-ace'),1,moved='leaf-king',moved_k=1)
        assert [c[0] for c in calls]==['leaf-ace']
        d._card=original
        # Ruky a cieľové karty zostávajú vľavo od vysvetlení aj v nízkom okne.
        for i,pos in d.spot.items():
            rect=pygame.Rect(0,0,d.cw,round(d.cw/CARD_RATIO));rect.center=pos
            assert d.stage.contains(rect) and rect.right<d.text_x
            if i==0:
                hand_top=d.seat[0][1]-.4*d.cw/CARD_RATIO
                assert rect.bottom<hand_top
        d._elapsed=lambda:3.5
        for scene in range(len(d.SCENES)):
            d.scene=scene;d.draw((0,0))
    # Poradie scenára zostáva totožné; karta každého hráča odchádza až na jeho ťahu.
    d=o.trump_demo;calls=[];original=d._play_from_hand
    d._play_from_hand=lambda *a,**kw:calls.append((a,kw))
    d._trick(CLASSIC_TRICK,3.5,1,0)
    assert [a[0] for a,kw in calls]==[p for p,n in CLASSIC_TRICK]
    assert [a[3] for a,kw in calls]==[1,1.45,1.9]
    assert calls[1][1]['mark']=='ok'
    d._play_from_hand=original
    assert not o.bidding_demo._visible_hands()
    assert not o.talon_demo._visible_hands()
    assert not o.scoring_demo._visible_hands()
    print('OK: pôvod, otočenie, odobratie, poradie, výsledok a oddelenie ostatných fáz.')

if __name__=='__main__':main()
