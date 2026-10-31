"""Pravidlá, časové udalosti a reset klasického Hlásenia tromfu."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['TISIC_RESOLUTION']=sys.argv[1] if len(sys.argv)>1 else '1920x1080'
os.environ['TISIC_DESKTOP']=os.environ['TISIC_RESOLUTION']
import pygame
from gui import display
from gui.info_overlay import InfoOverlay
from gui.trump_demo import CLASSIC_HAND, CLASSIC_OPENING, CLASSIC_CHANGE, CHANGE_HAND, PAIR, AFTER_FIRST_HAND
from game.card import Card
from game.hand import Hand
from game.trick import Trick

def check_trick(plays, hands, trump, winner):
    trick=Trick([None]*3,plays[0][0],trump)
    lead=None;played=[]
    for player,name in plays:
        hand=Hand();hand.add_cards([Card(*n.split('-')) for n in hands[player]])
        allowed=hand.get_playable_cards(lead,trump,played)
        card=Card(*name.split('-'))
        assert name+'.png' in [c.image_name for c in allowed],name
        trick.play_card(player,card);played.append((player,card))
        lead=lead or card.suit
    assert trick.get_winner_index()==winner

def main():
    assert CLASSIC_HAND==('leaf-ace','acorn-king','acorn-over','heart-ten')
    assert AFTER_FIRST_HAND == ("acorn-king", "acorn-over", "heart-ten")
    assert CLASSIC_CHANGE[0] == (0, "acorn-over")
    assert "acorn-seven" not in CHANGE_HAND
    check_trick(CLASSIC_OPENING,[CLASSIC_HAND,('leaf-king','heart-seven','bell-nine'),
                ('leaf-seven','heart-nine','bell-under')],None,0)
    check_trick(CLASSIC_CHANGE,[CHANGE_HAND,('acorn-ace','bell-king','bell-over'),
                ('acorn-nine','leaf-seven','heart-seven')],'acorn',1)
    from game.player import Player
    from game.round import Round
    players=[Player(str(i),index=i) for i in range(3)]
    rnd=Round(players,0,False);rnd.start_bidding();rnd.bidding.finalize()
    players[0].hand.add_cards([Card(*n.split('-')) for n in PAIR]);rnd.start_trick()
    assert not rnd.can_declare_trump(0,'acorn')
    rnd.trick_number=1
    assert rnd.can_declare_trump(0,'acorn')
    rnd.declare_trump(0,'acorn')
    players[1].hand.add_cards([Card('bell','king'),Card('bell','over')])
    rnd.current_leader_index=1;rnd.start_trick()
    assert rnd.can_declare_trump(1,'bell')
    rnd.declare_trump(1,'bell')
    assert players[0].declared_trumps_points==100 and players[1].declared_trumps_points==60
    display.get_surface();o=InfoOverlay(display.canvas());o.show();o.active_tab='pravidla';o.select_step(3)
    o.tricks_step.select_tab(1);d=o.trump_demo
    for key in d.keys:
        d.scene=d.keys.index(key)
        duration=d.SCENE_LEN
        # Kreslenie dopredu aj dozadu: bubliny a stav nezávisia od predchádzajúcej snímky.
        for t in (0,.5,1.3,2.7,3.3,4.1,4.6,5.4,5.8,7.5,8.4,9.6,10.6,12.5,duration-.5,2,0):
            d._elapsed=lambda t=t:t
            d.draw((0,0))
            state=d._classic_state(t)
            if key=='classic':
                assert state['trump'] is None and state['player_points']==0
                assert state['trick']==(1 if t<10.5 else 2)
            if key=='change':
                assert state['trump']==('acorn' if t<8.3 else 'bell')
                assert state['player_points']==100
                assert state['computer_points']==(0 if t<8.3 else 60)
                assert state['trick']==(2 if t<6 else 3)
                if 8.3<=t<12.3:
                    assert len(d._tutorial_bubble.bubbles)==1
                    assert d._tutorial_bubble.bubbles[0]['player_index']==1
            if key=='declare':
                assert state['buttons']==(1<=t<4.5)
                assert state['trump'] is None and state['player_points']==0
        del d._elapsed
        d.select(d.scene)
        assert d.hold_at is None and d.playing
    ticks = pygame.time.get_ticks
    try:
        for index in range(1,5):
            pygame.time.get_ticks=lambda:0
            d.select(index)
            duration=d.SCENE_LEN
            assert d.playing
            pygame.time.get_ticks=lambda:round(duration*2000+500)
            assert abs(d._elapsed()-.5)<.001 and d.scene==index
            d.toggle_play()
            pygame.time.get_ticks=lambda:round(duration*2000+5500)
            assert abs(d._elapsed()-.5)<.001 and not d.playing
            d.toggle_play()
            assert d.playing and d.scene==index
    finally:
        pygame.time.get_ticks=ticks
    # V 3/5 karta iba vystúpi z ruky; v 5/5 je horník od začiatku na stole.
    d.scene=d.keys.index('declare')
    cards=[];original=d._card
    d._card=lambda name,pos,*a,**kw: cards.append((name,pos,kw))
    d._elapsed=lambda:3.5
    d.draw((0,0))
    hornik=[c for c in cards if c[0]=='acorn-over']
    assert len(hornik)==1 and hornik[0][1][1]<d.hand_pos(1,3)[1]
    assert not hornik[0][2].get('mark')
    assert not any(c[0]=='leaf-ace' for c in cards)
    cards.clear();d.scene=d.keys.index('change');d._elapsed=lambda:0
    d.draw((0,0))
    hornik=[c for c in cards if c[0]=='acorn-over']
    assert len(hornik)==1 and hornik[0][1]==d.spot[0]
    assert hornik[0][2]['alpha']==1 and not hornik[0][2].get('mark')
    assert not any(c[0] in ('leaf-ace','acorn-seven') for c in cards)
    # Po zbere nesmie pribudnúť rub ani sa presunúť zostávajúce sloty.
    backs = []
    for moment in (5.9, 6., 6.8, 8.4, 12.):
        cards.clear();d._elapsed=lambda moment=moment:moment
        d.draw((0,0))
        cpu2=sorted(c[1] for c in cards if c[0]=='card-back' and c[1][0]>d.center[0])
        assert len(cpu2)==2
        backs.append(cpu2)
        cpu1=sorted(c[1] for c in cards if c[0]=='card-back' and c[1][0]<d.center[0])
        assert len(cpu1)==(2 if moment<7 else 1)
        if moment in (5.9,6.,6.8):
            assert cpu1==sorted([(d.seat[1][0]+d.cw*.25,d.seat[1][1]),
                                 (d.seat[1][0]+d.cw*.5,d.seat[1][1])])
    assert all(pos==backs[0] for pos in backs)
    d._card=original;del d._elapsed
    d.reset();assert d.scene==0 and d.playing
    assert len(d.SCENES)==5
    assert len(o.first_trump_demo.SCENES)==6
    # Ruky a stav druhého variantu sa nezmenili.
    o.first_trump_demo.scene=1
    assert o.first_trump_demo.SCENE_LEN==9
    errors=o.layout_problems();assert not errors,'\n'.join(errors)
    print('OK: karty, poradie, hlásenia, body, časové udalosti, reset a presahy.')

if __name__=='__main__':main()
