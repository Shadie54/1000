# tester/regression_rules_demo.py
#
# Overí, že príklady v animovanej ukážke pravidiel štichov
# (gui/rules_demo.py) zodpovedajú skutočnej logike hry — povolené karty
# (priznať farbu, prebiť, tromf), víťaz štichu, poradie hráčov — a ukážky
# Dražby a Talónu (gui/round_demos.py): poradie v dražbe, víťaz, posun
# povinnosti, odhodenie (nie eso ani desiatka), body odhodených kariet.
#
# Použitie:  python tester/regression_rules_demo.py

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def main():
    from gui.rules_demo import verify_scenes
    from gui.round_demos import verify_round_demos
    errors = verify_scenes() + verify_round_demos()
    for e in errors:
        print(f"  {e}")
    print("VÝSLEDOK: " + ("ukážka pravidiel zodpovedá logike hry" if not errors
                          else f"{len(errors)} chýb"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
