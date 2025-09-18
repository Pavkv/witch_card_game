label start:
    $ player_name = renpy.input("Введите ваше имя", length=20)
    $ opponent_name = "Противник"
    $ cards_bg = "images/bg/bg_14.jpg"
    $ in_game = False
    $ base_card_img_src = "images/cards/cards"
    $ biased_draw = ["opponent", 0.5]
    $ day2_game_with_Alice = False
    python:
        card_game = WitchGame(player_name, opponent_name, biased_draw)
        card_game_name = "witch"
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
    jump witch_game_loop

label witch_game_loop:
    $ print(card_game.player.hand)
    if is_dealing:
#         $ renpy.block_rollback()
        $ is_dealing = False
        call screen deal_cards
    else:
        $ deal_cards = False

    if card_game.state == "results":
#       $ renpy.block_rollback()
        "[card_game.result]"
#         pause 3.0
#         hide screen card_game_base_ui
#         if in_game:
#             if card_game.result == player_name and card_game.player.total21() == 21 and ['7', 'Q', 'A'] in card_game.player.get_ranks():
#                 if not persistent.achievements["Три карты"]:
#                     play sound sfx_achievement
#                     show three_cards_message at achievement_trans
#                     with dspr
#                     $ renpy.pause(3, hard=True)
#                     hide three_cards_message
#                     $ persistent.achievements["Три карты"] = True
#             if card_game.result == player_name and card_game.player.total21() == 21 and ['7', '7', '7'] == card_game.player.get_ranks():
#                 if not persistent.achievements["Три топора"]:
#                     play sound sfx_achievement
#                     show three_axes_message at achievement_trans
#                     with dspr
#                     $ renpy.pause(3, hard=True)
#                     hide three_axes_message
#                     $ persistent.achievements["Три топора"] = True
#             jump expression card_game_results[card_game.result]
#         else:
#             jump card_games

    $ game_over = card_game.game_over()
    if game_over[0]:
#         $ renpy.block_rollback()
        $ card_game.result = game_over[1]
        $ print("Game Over: ", card_game.result)
        $ card_game.state = "results"

    if card_game.state == "opponent_turn":
#         $ renpy.block_rollback()
        pause 1.5
        python:
            if len(card_game.opponent.hand) < 6 and len(card_game.deck.cards) > 0:
                print("AI draws cards.")
                witch_ai_draw_to_six_anim()
                if card_game.opponent.count_pairs_excluding_witch() > 0:
                    print("AI discards pairs.")
                    compute_hand_layout()
                    renpy.pause(1.5)
                    witch_ai_discard_pairs_anim()
            elif card_game.opponent.count_pairs_excluding_witch() > 0:
                print("AI discards pairs.")
                witch_ai_discard_pairs_anim()
            elif card_game.opponent.can_exchange_now(card_game.deck):
                print("AI exchanges a card.")
                card_game.state = "wait_choice_opponent"
                donor_idx = card_game._next_player_with_cards(1)
                donor = card_game.players[donor_idx]
                ai_idx = (card_game.opponent.choose_exchange_index(donor)
                      if hasattr(card_game.opponent, "choose_exchange_index")
                      else renpy.random.randint(0, len(donor.hand)-1))
                renpy.pause(1.5)
                witch_ai_take_from_user_anim(ai_idx)
                if card_game.opponent.count_pairs_excluding_witch() > 0:
                        print("AI discards pairs.")
                        compute_hand_layout()
                        renpy.pause(1.5)
                        witch_ai_discard_pairs_anim()
            card_game.state = "player_turn"
            compute_hand_layout()

    call screen witch
    jump witch_game_loop


