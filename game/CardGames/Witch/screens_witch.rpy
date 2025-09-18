screen witch():

    # Main game screen for witch
    tag witch_screen
    zorder 1

    if card_game.state not in ["wait_choice", "player_turn"]:
         timer 0.5 action Jump(card_game_name + "_game_loop")
    else:
        frame:
            background None
            xpos 1750
            ypos 945
            if card_game.player.count_pairs_excluding_witch() > 0:
                frame:
                    xsize 150
                    padding (0, 0)
                    has vbox
                    textbutton "{color=#fff}Скинуть\nпары{/color}":
                        style "card_game_button"
                        text_size 18
                        action Function(witch_user_discard_pairs_anim)

            elif len(card_game.player.hand) < 6 and len(card_game.deck.cards) > 0:
                frame:
                    xsize 150
                    padding (0, 0)
                    ypos 30
                    has vbox
                    textbutton "{color=#fff}Взять{/color}":
                        style "card_game_button"
                        text_size 25
                        action Function(witch_user_draw_to_six_anim)

            elif card_game.player.can_exchange_now(card_game.deck) and card_game.state != "wait_choice":
                frame:
                    xsize 150
                    padding (0, 0)
                    ypos 30
                    has vbox
                    textbutton "{color=#fff}Вытянуть\nкарту{/color}":
                        style "card_game_button"
                        text_size 18
                        action SetVariable("card_game.state", "wait_choice")