label start_durak:
    python:
        card_game = DurakCardGame(player_name, opponent_name, biased_draw)
        card_game_name = "durak"
        base_cover_img_src = base_card_img_src + "/cover.png"
        card_game.opponent.avatar = card_game_avatar
        card_game.draw_cards()
        compute_hand_layout()
        card_game.define_first_turn()

        dealt_cards = []
        is_dealing = True
        deal_cards = True

        delay = 0.0
        for i in range(len(card_game.player.hand)):
            dealt_cards.append({
                "owner": "player",
                "index": i,
                "delay": delay
            })
            delay += 0.1

        for i in range(len(card_game.opponent.hand)):
            dealt_cards.append({
                "owner": "opponent",
                "index": i,
                "delay": delay
            })
            delay += 0.1

    show screen card_game_base_ui
    jump durak_game_loop

label durak_game_loop:

    if is_dealing:
#         $ renpy.block_rollback()
        $ is_dealing = False
        call screen deal_cards
    else:
        $ deal_cards = False

    if card_game.result:
#         $ renpy.block_rollback()
        $ print("Game Over: ", card_game.result)
        $ card_game.state = "results"

    if card_game.state == "ai_attack":
#         $ renpy.block_rollback()
        if card_game.can_attack(card_game.opponent):
            $ attack_success = card_game.ai_attack()
            if attack_success:
                $ print("AI attacked successfully.")
                $ card_game.state = "player_defend"
        else:
            if not card_game.table.beaten() and not confirm_take:
                $ print("AI could not attack, player must defend or take.")
                $ card_game.state = "player_defend"
            else:
                $ print("AI could not attack, ending turn.")
                $ confirm_take = False
                $ card_game.state = "end_turn"

    elif card_game.state == "ai_defend":
#         $ renpy.block_rollback()
        $ defend_success = card_game.ai_defend()
        if defend_success:
            $ print("AI defended successfully.")
        else:
            $ print("AI could not defend, ending turn.")
        $ card_game.state = "player_attack"

    elif card_game.state == "end_turn":
#         $ renpy.block_rollback()

        if card_game.current_turn == card_game.opponent and card_game.can_attack(card_game.opponent):
            $ print("Ai adding throw ins.")
            $ card_game.throw_ins()

        $ print("Table before ending turn: ", card_game.table)
        $ print("Player hand before ending turn: ", card_game.player.hand)
        $ print("Opponent hand before ending turn: ", card_game.opponent.hand)

        # Make sure old animation is gone
        hide screen table_card_animation

        # Build the new animation list
        python:
            table_animations = []
            delay = 0.0
            for i, (atk, (beaten, def_card)) in enumerate(card_game.table.table.items()):
                src_x = 350 + i * 200
                src_y = 375
                cards = list(filter(None, [atk, def_card]))

                if not card_game.table.beaten():
                    receiver = card_game.player if card_game.current_turn != card_game.player else card_game.opponent
                    for card in cards:
                        table_animations.append({
                            "card": card,
                            "src_x": src_x,
                            "src_y": src_y if card == atk else src_y + 120,
                            "dest_x": 700,
                            "dest_y": 825 if receiver == card_game.player else 20,
                            "delay": delay,
                            "target": "hand"
                        })
                        delay += 0.1
                else:
                    for card in cards:
                        table_animations.append({
                            "card": card,
                            "src_x": src_x,
                            "src_y": src_y if card == atk else src_y + 120,
                            "dest_x": 1600,
                            "dest_y": 350,
                            "delay": delay,
                            "target": "discard"
                        })
                        delay += 0.1

        # Show the fresh animation
        show screen table_card_animation
        $ is_table_animating = False

        $ attack_cards = [atk for atk, (_b, _d) in card_game.table.table.items()]
        $ print("Attack cards: ", attack_cards)
        python:
            if len(attack_cards) == 2:
                for c in attack_cards:
                    if getattr(c, "rank", None) not in ("6", 6):
                        last_attack_two_sixes = False
                        break

        $ lost_to_two_sixes = (
            card_game.current_turn == card_game.opponent
            and last_attack_two_sixes
            and card_game.deck.is_empty()
        )

        $ card_game.take_or_discard_cards()
        $ card_game.end_turn()

        $ print("Discarding table cards", card_game.deck.discard)
        $ print("Player hand after ending turn: ", card_game.player.hand)
        $ print("Opponent hand after ending turn: ", card_game.opponent.hand)

        if card_game.result:
            $ card_game.state = "results"
        else:
            $ old_player_len = len(card_game.player.hand)
            $ old_opponent_len = len(card_game.opponent.hand)

            $ card_game.draw_cards()
            $ compute_hand_layout()

            $ print("Player hand after drawing: ", card_game.player.hand)
            $ print("Opponent hand after drawing: ", card_game.opponent.hand)

            $ new_player_len = len(card_game.player.hand)
            $ new_opponent_len = len(card_game.opponent.hand)

            $ next_turn = True
            $ confirm_take = False

    if card_game.state == "results":
#       $ renpy.block_rollback()
        hide screen card_game_base_ui
        if in_game:
            if card_game.result == card_game.opponent.name and lost_to_two_sixes:
                if not persistent.achievements["Адмирал"]:
                    play sound sfx_achievement
                    show admiral_message at achievement_trans
                    with dspr
                    $ renpy.pause(3, hard=True)
                    hide admiral_message
                    $ persistent.achievements["Адмирал"] = True
            jump expression card_game_results[card_game.result]
        else:
            $ reset_card_game()
            jump card_games

    call screen durak
    jump durak_game_loop
