label start_21:
    python:
        card_game = Game21(player_name, opponent_name, biased_draw, g21_card_num, g21_aces_low)
        card_game_name = "g21"
        base_cover_img_src = base_card_img_src + "/cover.png"
        card_game.opponent.avatar = card_game_avatar
        card_game.start_round()
        compute_hand_layout()

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
    jump g21_game_loop

label g21_game_loop:
    if is_dealing:
#         $ renpy.block_rollback()
        $ is_dealing = False
        call screen deal_cards
    else:
        $ deal_cards = False

    if card_game.state == "results":
#       $ renpy.block_rollback()
        pause 3.0
        hide screen card_game_base_ui
        if in_game:
            if card_game.result == player_name and card_game.player.total21() == 21 and ['7', 'Q', 'A'] in card_game.player.get_ranks():
                if not persistent.achievements["Три карты"]:
                    play sound sfx_achievement
                    show three_cards_message at achievement_trans
                    with dspr
                    $ renpy.pause(3, hard=True)
                    hide three_cards_message
                    $ persistent.achievements["Три карты"] = True
            if card_game.result == player_name and card_game.player.total21() == 21 and ['7', '7', '7'] == card_game.player.get_ranks():
                if not persistent.achievements["Три топора"]:
                    play sound sfx_achievement
                    show three_axes_message at achievement_trans
                    with dspr
                    $ renpy.pause(3, hard=True)
                    hide three_axes_message
                    $ persistent.achievements["Три топора"] = True
            jump expression card_game_results[card_game.result]
        else:
            jump card_games


    if card_game.result:
#         $ renpy.block_rollback()
        $ print("Game Over: ", card_game.result)
        $ card_game.state = "results"

    if card_game.state == "opponent_turn":
#         $ renpy.block_rollback()
        pause 1.5
        python:
            opponent_move = card_game.opponent_turn()
            if opponent_move == 'h':
                card_game._draw_one(card_game.opponent)
                if card_game.opponent.total21() >= 21:
                    card_game.finalize()
            elif opponent_move == 'p' and card_game.first_player == card_game.opponent:
                card_game.state = "player_turn"
            else:
                card_game.finalize()
            compute_hand_layout()

    call screen game21
    jump g21_game_loop


