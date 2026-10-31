"""Nadväznosť kariet a slučky variantu hlásenia v prvom štichu."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['TISIC_RESOLUTION']=sys.argv[1] if len(sys.argv)>1 else '1920x1080'
os.environ['TISIC_DESKTOP']=os.environ['TISIC_RESOLUTION']
import pygame
from gui import display
from gui.info_overlay import InfoOverlay
from gui.trump_demo import FIRST_HANDS,FIRST_TRICK,LATER_TRICK,FIRST_CHANGE
from game.card import Card
from game.hand import Hand
from game.trick import Trick

def main():
    assert all(len(h)==5 for h in FIRST_HANDS)
    assert len({n for h in FIRST_HANDS for n in h})==15
    hands=[list(h) for h in FIRST_HANDS]
    for plays,winner in ((FIRST_TRICK,1),(LATER_TRICK,0),(FIRST_CHANGE,1)):
        trick=Trick([None]*3,plays[0][0],'acorn');played=[];lead=None
        for player,name in plays:
            h=Hand();h.add_cards([Card(*n.split('-')) for n in hands[player]])
            assert name+'.png' in [c.image_name for c in h.get_playable_cards(lead,'acorn',played)]
            card=Card(*name.split('-'));trick.play_card(player,card);played.append((player,card))
            lead=lead or card.suit;hands[player].remove(name)
        assert trick.get_winner_index()==winner
    assert hands==[['acorn-king','leaf-under'],['bell-king','bell-over'],['leaf-king','bell-nine']]
    display.get_surface();o=InfoOverlay(display.canvas());o.show();o.active_tab='pravidla';o.select_step(3)
    o.tricks_step.select_tab(2);d=o.first_trump_demo
    original=d._card;cards=[]
    d._card=lambda name,pos,*a,**kw:cards.append((name,pos,kw))
    snapshots=[('effect',4,{'heart-seven','acorn-king','acorn-ten'},5,5),
               ('win',6,{'heart-seven','acorn-king','acorn-ten'},4,4),
               ('win',12.5,{'heart-seven','acorn-king'},3,3),
               ('change',5.8,{'acorn-king'},2,2),
               ('change',12.5,{'acorn-king'},1,2)]
    for key,t,faces,n1,n2 in snapshots:
        cards.clear();d.scene=d.keys.index(key);d._elapsed=lambda t=t:t;d.draw((0,0))
        assert sum(n=='card-back' and pos[0]<d.center[0] for n,pos,kw in cards)==n1
        assert sum(n=='card-back' and pos[0]>d.center[0] for n,pos,kw in cards)==n2
        # Zostávajúce líca hráča majú pôvodné pozície, bez návratu už zahraných kariet.
        for name in faces | {"leaf-under"}:
            assert any(n==name and pos==d._first_origin(0,name) for n,pos,kw in cards)
    d._card=original;del d._elapsed
    ticks=pygame.time.get_ticks
    try:
        for index in range(1,6):
            pygame.time.get_ticks=lambda:0;d.select(index);duration=d.SCENE_LEN
            pygame.time.get_ticks=lambda:round(duration*2000+500)
            assert abs(d._elapsed()-.5)<.001 and d.scene==index
            d.toggle_play();assert not d.playing
            d.toggle_play();assert d.playing
    finally:pygame.time.get_ticks=ticks
    for scene in range(6):
        d.scene=scene
        for t in (0,1.5,3.5,5.9,6.1,8.5,12.5):
            d._elapsed=lambda t=t:t;d.draw((0,0))
    del d._elapsed
    assert not o.layout_problems()
    print('OK: tri nadväzujúce štichy, ubúdanie kariet, stabilné sloty, slučky a rozloženie.')

if __name__=='__main__':main()
