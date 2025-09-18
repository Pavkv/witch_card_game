init python:
    # ----------------------------
    # Layout anchors — tweak to your UI
    # ----------------------------
    DECK_X,    DECK_Y    = 50, 350
    DISCARD_X, DISCARD_Y = 1600, 350
    HAND0_X,   HAND0_Y   = 700, 825   # user hand baseline
    HAND1_X,   HAND1_Y   = 700,  20   # ai hand baseline
    HAND_SPACING         = 120

    # global animations list used by your screen
    if "table_animations" not in globals():
        table_animations = []

    # ----------------------------
    # position helpers
    # ----------------------------
    def _hand_card_pos(side_index, card):
        """Approx start position of CARD in hand; replace with your own layout if available."""
        hand = card_game.players[side_index].hand
        try:
            idx = hand.index(card)
        except ValueError:
            idx = 0
        if side_index == 0:
            return HAND0_X + idx * HAND_SPACING, HAND0_Y
        else:
            return HAND1_X + idx * HAND_SPACING, HAND1_Y

    def _next_slot_pos(side_index):
        """Position where the next card would visually land in the hand."""
        hand = card_game.players[side_index].hand
        idx = len(hand)  # simple: to the right of current last card
        return (HAND0_X + idx * HAND_SPACING, HAND0_Y) if side_index == 0 else (HAND1_X + idx * HAND_SPACING, HAND1_Y)

    def _diff_removed(before, after):
        """Cards removed from 'before' (order preserved)."""
        removed = []
        after_set = set(after)
        for c in before:
            if c not in after_set:
                removed.append(c)
        return removed

    def _show_anim():
        renpy.show_screen("table_card_animation")

    def _bias_for(side_index):
        return card_game.bias["player"] if side_index == 0 else card_game.bias["opponent"]

    # ----------------------------
    # USER (side_index = 0) — animations
    # ----------------------------
    def witch_user_discard_pairs_anim(base_delay=0.0, step=0.05):
        """Animate user pair-discard to the discard pile, then shuffle and advance player_turn."""
        p = card_game.players[0]
        before = list(p.hand)
        p.discard_pairs_excluding_witch(card_game.deck)
        after = list(p.hand)
        removed = _diff_removed(before, after)

        table_animations[:] = []
        for i, card in enumerate(removed):
            sx, sy = _hand_card_pos(0, card)
            table_animations.append({
                "card": card, "src_x": sx, "src_y": sy,
                "dest_x": DISCARD_X, "dest_y": DISCARD_Y,
                "delay": base_delay + i * step, "target": "discard",
            })
        _show_anim()

        p.shaffle_hand()
        compute_hand_layout()
        card_game.state = "opponent_turn"

    def witch_user_draw_to_six_anim(step_delay=0.05):
        side = 0
        table_animations[:] = []
        d = 0.0
        # enqueue one animation per draw (compute dest BEFORE draw so slot is correct)
        while len(card_game.players[side].hand) < 6 and not card_game.deck.is_empty():
            dx, dy = _next_slot_pos(side)
            # draw with bias
            card_game.players[side].draw_from_deck(
                card_game.deck, trump_suit=None, good_prob=_bias_for(side)
            )
            last = card_game.players[side].hand[-1]
            table_animations.append({
                "card": last,
                "src_x": DECK_X, "src_y": DECK_Y,
                "dest_x": dx, "dest_y": dy,
                "delay": d, "target": "hand0",
            })
            d += step_delay
        if table_animations:
            renpy.show_screen("table_card_animation")
        compute_hand_layout()
        if card_game.player.count_pairs_excluding_witch() == 0:
            card_game.state = "opponent_turn"

    def witch_user_take_from_ai_anim(index, base_delay=0.0):
        """Animate user taking a facedown card from AI (exchange/drain)."""
        donor = card_game.players[1]
        taker = card_game.players[0]

        # get a visual source: approximate source slot in AI hand
        sx, sy = _hand_card_pos(1, donor.hand[index] if index < len(donor.hand) else donor.hand[-1])
        dx, dy = _next_slot_pos(0)

        # perform the take
        taken = taker.take_card_from(donor, index=index)
        if hasattr(taker, 'on_after_take'):
            taker.on_after_take(donor, taken)

        # animate move to user hand
        table_animations[:] = [{
            "card": taken, "src_x": sx, "src_y": sy,
            "dest_x": dx, "dest_y": dy, "delay": base_delay, "target": "hand0",
        }]
        _show_anim()
        compute_hand_layout()
        if card_game.player.count_pairs_excluding_witch() == 0:
            card_game.state = "opponent_turn"

    # ----------------------------
    # AI (side_index = 1) — animations
    # ----------------------------
    def witch_ai_discard_pairs_anim(base_delay=0.0, step=0.05):
        """Animate AI pair-discard to the discard pile, then shuffle and continue opponent_turn."""
        p = card_game.players[1]
        before = list(p.hand)
        p.discard_pairs_excluding_witch(card_game.deck)
        after = list(p.hand)
        removed = _diff_removed(before, after)

        table_animations[:] = []
        for i, card in enumerate(removed):
            sx, sy = _hand_card_pos(1, card)
            table_animations.append({
                "card": card, "src_x": sx, "src_y": sy,
                "dest_x": DISCARD_X, "dest_y": DISCARD_Y,
                "delay": base_delay + i * step, "target": "discard",
            })
        _show_anim()

        p.shaffle_hand()

    def witch_ai_draw_to_six_anim(step_delay=0.05):
        side = 1
        table_animations[:] = []
        d = 0.0
        while len(card_game.players[side].hand) < 6 and not card_game.deck.is_empty():
            dx, dy = _next_slot_pos(side)
            card_game.players[side].draw_from_deck(
                card_game.deck, trump_suit=None, good_prob=_bias_for(side)
            )
            last = card_game.players[side].hand[-1]
            table_animations.append({
                "card": last,
                "src_x": DECK_X, "src_y": DECK_Y,
                "dest_x": dx, "dest_y": dy,
                "delay": d, "target": "hand1",
            })
            d += step_delay
        if table_animations:
            renpy.show_screen("table_card_animation")

    def witch_ai_take_from_user_anim(index, base_delay=0.0):
        """Animate AI taking a card from User (exchange/drain)."""
        donor = card_game.players[0]
        taker = card_game.players[1]

        sx, sy = _hand_card_pos(0, donor.hand[index] if index < len(donor.hand) else donor.hand[-1])
        dx, dy = _next_slot_pos(1)

        taken = taker.take_card_from(donor, index=index)
        if hasattr(taker, 'on_after_take'):
            taker.on_after_take(donor, taken)

        table_animations[:] = [{
            "card": taken, "src_x": sx, "src_y": sy,
            "dest_x": dx, "dest_y": dy, "delay": base_delay, "target": "hand1",
        }]
        _show_anim()
