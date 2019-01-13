# Evaluates the "superaccept" bidding convention, in which 1NT opener with a
# maximal (17 HCP) hand responds to partner's Jacoby transfer by bidding 3 of
# the major when they have 4+ card support.

# Computed payoff of superaccepting (N = 50000):
# MP      = 0.00 +/- 0.00
# IMPs V  = 1.67 +/- 0.03
# IMPs NV = 0.67 +/- 0.02
# 16219 hands with same score and strain

import redeal

# for now, assume 1NT is only opened on balanced shapes
superaccept_shape = redeal.Shape("(43)33") + redeal.Shape("44(32)") + \
                    redeal.Shape("5(332)") + redeal.Shape("35(32)") + \
                    redeal.Shape("2533")
NT_shape = superaccept_shape

# require south hand to have 17 HCP and the right shape to open 1NT and
# possibly superaccept a transfer
predeal = {"S": redeal.SmartStack(NT_shape, redeal.hcp, [17])}

# this is based on a script that used global variables;
# it'd be nice if there were a different way
def initial():
    global TABLE_MP
    global TABLE_IMP
    global TABLE_IMP_VUL
    global TABLE_IMP_NVUL
    global SAME_SCORE

    TABLE_MP = redeal.Payoff(("super", "nosuper"), redeal.matchpoints)
    TABLE_IMP_VUL = redeal.Payoff(("super", "nosuper"), redeal.imps)
    TABLE_IMP_NVUL = redeal.Payoff(("super", "nosuper"), redeal.imps)
    # TABLE_IMP averages over vulnerability. The individual "scores" added
    # will actually be tuples of length 2 representing the vul score and
    # the nonvul score.
    TABLE_IMP = redeal.Payoff(("super", "nosuper"),
                               lambda p1, p2: (redeal.imps(p1[0], p2[0]) +
                                               redeal.imps(p1[1], p2[1])) / 2.0)
    SAME_SCORE = 0


def short_suit_points(holding):
    if len(holding) >= 3:
        return 0
    elif len(holding) == 2:
        return 1
    elif len(holding) == 1:
        return 2
    else:
        return 3


def dist_points(hand):
    return (short_suit_points(hand.spades) + 
            short_suit_points(hand.hearts) +
            short_suit_points(hand.diamonds) +
            short_suit_points(hand.clubs))


# Uses traditional 4-3-2-1 and doubleton-singleton-void hand evaluation.
# Returns None if the result doesn't depend on use_superaccept and we're too
# lazy to compute it.
def contract(deal, use_superaccept):
    ns = len(deal.north.spades)
    nh = len(deal.north.hearts)
    nhcp = deal.north.hcp
    ntp = nhcp + dist_points(deal.north)
    ss = len(deal.south.spades)
    sh = len(deal.south.hearts)

    # South opens 1NT. Let's first take care of 6-card suits. Here North will
    # always give themselves distribution points because a fit is known to
    # exist.
    if ns >= 6 or nh >= 6:
        # If North is strong enough, they'll just Texas into game.
        if ntp >= 10: return None

        # Otherwise, North Jacobys into their 6-card suit. If they have more
        # than one, break ties by playing tricks.
        if ns < 6:
            suit = 'H'
        elif nh < 6:
            suit = 'S'
        elif deal.north.spades.pt >= deal.north.hearts.pt:
            suit = 'S'
        else:
            suit = 'H'
        if suit == 'H':
            sl = sh
        else:
            sl = ss
        # If south doesn't have 4+ card support for the chosen suit, then
        # superaccepts don't matter.
        if sl < 4: return None
        if use_superaccept:
            # South bids 3 of the suit. North now knows South has 17 HCP.
            if ntp >= 8: return '4' + suit + 'S'
            else: return '3' + suit + 'S'
        else:
            # South bids 2 of the suit. With 9 total points, North invites with
            # 3M and South accepts. With 8-, North passes.
            if ntp == 9: return '4' + suit + 'S'
            else: return '2' + suit + 'S'

    # Now north has 1 or 2 5-card suits. If they only have 1, they show that
    # suit. If they have 2, the suit they show first depends on their strength.
    # It then doesn't matter for our purposes whether a fit exists in the other
    # suit, because the opportunity for south to show a superaccept exists only
    # for the first suit north shows.
    if ns < 5:
        suit = 'H'
    elif nh < 5:
        suit = 'S'
    elif ntp >= 10:
        # North assumes that a fit exists in at least one of the two suits
        # (as south has at most one doubleton), and thus evaluates their hand
        # based on total points. With GF strength, spades is shown first.
        suit = 'S'
    elif ntp == 9:
        # With invitational strength, north bids 2D as transfer to hearts, then
        # bids 2S and lets south place the contract.
        suit = 'H'
    elif deal.north.spades.losers <= deal.north.hearts.losers:
        # With less than invitational strength, north picks the better of the
        # two suits to transfer into, planning to pass.
        suit = 'S'
    else:
        suit = 'H'

    if suit == 'H':
        os = 'S'
        ssl = sh
        sol = ss
        nol = ns
    else:
        os = 'H'
        ssl = ss
        sol = sh
        nol = nh
    if ssl < 4: return None

    # In the case where north has exactly 4 of the other major and inv+
    # strength, they'll choose to go through Stayman instead of a transfer.
    if nol == 4 and nhcp >= 9: return None

    if use_superaccept:
        # South bids 3 of the suit. North now knows a fit exists and South has
        # 17 HCP, so North goes to game with 8+ total points.
        if ntp >= 8: return '4' + suit + 'S'
        else: return '3' + suit + 'S'
    # South bids 2. Let's now tackle the cases where north is 5-5.
    if nol == 5:
        if ntp >= 10:
            # North previously bid 2H and now bids 3H, showing 5-5 GF. South has
            # to decide which suit to play in. Let's assume South picks the
            # longer of the two suits. In case of a tie, South picks spades
            # to retain the transfer advantage.
            if sh > ss:
                return '4HN'
            else:
                return '4SS'
        elif ntp == 9:
            # North had bid 2D and now bids 2S over South's 2H, showing 5-5 inv.
            # South picks the longer of the two suits and goes to game because
            # of the maximal hand. In case of a tie, hearts is picked to retain
            # the transfer advantage.
            if ss > sh:
                return '4SN'
            else:
                return '4HS'
        else:
            # North passes.
            return '2' + suit + 'S'
    # North has only one 5-card major, and doesn't know whether a fit exists.
    if nhcp >= 9:
        # North bids 2NT (with 9 HCP) or 3NT (with 10+ HCP).
        # South then bids 4M with the maximal hand.
        return '4' + suit + 'S'
    else:
        # North doesn't know about the fit, and with 8- HCP, must pass even
        # if distribution justifies going to game.
        return '2' + suit + 'S'
        

def accept(deal):
    if len(deal.north.spades) < 5 and len(deal.north.hearts) < 5:
        # No Jacoby transfer. Skip.
        return False
    if len(deal.south.spades) < 4 and len(deal.south.hearts) < 4:
        # No possibility of superaccept. Skip.
        return False
    deal.sc = contract(deal, True)  # superaccept contract
    deal.nsc = contract(deal, False)  # no superaccept contract
    if deal.sc is None or deal.nsc is None:
        assert deal.sc is None and deal.nsc is None
        return False
    if deal.sc == deal.nsc:
        # the superaccept makes no difference
        return False;
    # the superaccept does make a difference, so proceed.
    return True


def do(deal):
    global SAME_SCORE

    ns_nv = deal.dd_score(deal.nsc, vul=False)
    ns_v = deal.dd_score(deal.nsc, vul=True)
    s_nv = deal.dd_score(deal.sc, vul=False)
    s_v = deal.dd_score(deal.sc, vul=True)
    print("{} {} {} {} {}".format(deal, ns_nv, ns_v, s_nv, s_v))

    TABLE_MP.add_data(dict(super=s_nv, nosuper=ns_nv))
    TABLE_IMP_VUL.add_data(dict(super=s_v, nosuper=ns_v))
    TABLE_IMP_NVUL.add_data(dict(super=s_nv, nosuper=ns_nv))
    TABLE_IMP.add_data(dict(super=(s_v, s_nv), nosuper=(ns_v, ns_nv)))

    if ns_nv == s_nv and deal.sc[0] > deal.nsc[0] and deal.nsc[1] == deal.sc[1]:
        SAME_SCORE += 1


def final(n_tries):
    print('MPs report')
    TABLE_MP.report()
    print('IMPs report (V/NV/overall)')
    TABLE_IMP_VUL.report()
    TABLE_IMP_NVUL.report()
    TABLE_IMP.report()
    print('Hands with the same double-dummy score but where superaccepting ' +
          'gets you one level higher in the auction: {}'.format(SAME_SCORE))
    print("Tries: {}".format(n_tries))
