# game/ai_strategies_const.py
# Názvy stratégií pre logovanie

# Leader stratégie (L)
CERTAIN_TRICK = "L1-CERTAIN_TRICK"
TRUMP_DECLARE = "L2-TRUMP_DECLARE"
FORCING = "L3-FORCING"
ENDGAME = "L4-ENDGAME"
PASSIVE = "L5-PASSIVE"
FIRST_TRICK_TRUMP = "L6-FIRST_TRICK_TRUMP"     # variant: hlásenie v 1. štichu

# Follower stratégie (F)
TRACK_BIDDER = "F1-TRACK_BIDDER"
PROTECT_TEN = "F2-PROTECT_TEN"
CLAIM_LEAD = "F3-CLAIM_LEAD"
SAFE_DISCARD = "F4-SAFE_DISCARD"
DENY_TRICK = "F5-DENY_TRICK"                   # variant: nedať štich hlásiacemu
SECURE_TRICK = "F6-SECURE_TRICK"               # variant: hlásiaci si zaistí štich

# Bidding stratégie (B)
SECURE_TRUMP_BID = "B1-SECURE_TRUMP_BID"
PASSIVE_BID = "B2-PASSIVE_BID"
PASS_FOR_TRUMP = "B3-PASS_FOR_TRUMP"
LONG_SUIT_BID = "B4-LONG_SUIT_BID"
BID_ESTIMATE = "B5-BID_ESTIMATE"
FIRST_TRICK_BID = "B6-FIRST_TRICK_BID"         # variant: nepasuj kvôli hláške

# Talon stratégie (T)
SMART_DISCARD = "T1-SMART_DISCARD"
RAISE_AFTER_TALON = "T2-RAISE_AFTER_TALON"