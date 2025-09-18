screen card_game_base_ui():

    # Base UI for the card game
    tag base_ui
    zorder 0

    add cards_bg xpos 0 ypos 0 xysize (1920, 1080)

    if not in_game:
        frame:
            xpos 1755
            ypos 750
            xsize 150
            padding (0, 0)
            has vbox
            textbutton "{color=#fff}Вернуться в меню{/color}":
                style "card_game_button"
                text_size 23
                action [
                    Function(reset_card_game),
                    SetVariable("in_game", True),
                    Hide("card_game_base_ui"),
                    Return(),
                ]

    # Opponent avatar
    frame:
        background None
        xpos 1750
        ypos 20
        has vbox

        frame:
            background RoundRect("#b2b3b4", 10)
            xysize (150, 150)
            add opponent_avatar_displayable(size=(150, 150), pad=10) align (0.5, 0.5)

        frame:
            background RoundRect("#b2b3b4", 10)
            xsize 150
            yoffset 8
            padding (5, 5)
            text card_game.opponent.name color "#ffffff" text_align 0.5 align (0.5, 0.5)

        if day2_game_with_Alice:
            $ tournament_players = card_game.player.name + " | " + card_game.opponent.name
            $ tournament_scores = str(day2_alice_tournament_result[0]) + " | " + str(day2_alice_tournament_result[1])

            frame:
                background RoundRect("#b2b3b4", 10)
                xsize 150
                yoffset 18
                padding (2, 2)
                xalign 0.5
                yalign 0.0

                vbox:
                    spacing 4
                    xalign 0.5

                    text tournament_players color "#ffffff" size 19 xalign 0.5 text_align 0.5
                    text tournament_scores color "#ffffff" size 19 xalign 0.5 text_align 0.5

    # Game phase and action buttons
    frame:
        background None
        xpos 1750
        ypos 823
        has vbox

        frame:
            background RoundRect("#b2b3b4", 10)
            xsize 150
            yoffset 10
            padding (5, 5)
            text "Фаза Игры:" color "#ffffff" text_align 0.5 align (0.5, 0.5)

        frame:
            background RoundRect("#b2b3b4", 10)
            xsize 150
            yoffset 20
            padding (5, 5)
            $ phase_text = "—"
            if card_game is not None and hasattr(card_game, "state"):
                $ phase_text = card_game_state_tl.get(card_game_name, {}).get(card_game.state, "—")

            text phase_text:
                color "#ffffff"
                size 19
                text_align 0.5
                align (0.5, 0.5)

        if isinstance(card_game, DurakCardGame):
            $ show_end_turn = card_game.table and card_game.state in ["player_attack", "player_defend"]
            $ show_confirm_attack = card_game.state == "player_attack" and len(selected_attack_card_indexes) > 0
            if show_end_turn and show_confirm_attack:
                $ y1 = 30
                $ y2 = 40
            else:
                $ y1 = y2 = 30

            if show_end_turn:
                frame:
                    xsize 150
                    padding (0, 0)
                    ypos y1
                    has vbox
                    textbutton ["{color=#fff}Бито{/color}" if card_game.state == "player_attack" else "{color=#fff}Взять{/color}"]:
                        style "card_game_button"
                        text_size 25
                        action [If(
                            card_game.state == "player_attack",
                            [SetVariable("card_game.state", "end_turn"), SetVariable("selected_attack_card_indexes", set())],
                            SetVariable("card_game.state", "ai_attack")
                        ), SetVariable("confirm_take", True)]

            if show_confirm_attack:
                frame:
                    xsize 150
                    padding (0, 0)
                    ypos y2
                    has vbox
                    textbutton "{color=#fff}Подтвердить\nатаку{/color}":
                        style "card_game_button"
                        text_size 18
                        action [SetVariable("confirm_attack", True), Function(confirm_selected_attack)]

        elif isinstance(card_game, WitchGame) and card_game.state == "wait_choice":
                frame:
                    xsize 150
                    padding (0, 0)
                    ypos 30
                    has vbox
                    textbutton "{color=#fff}Подтвердить{/color}":
                        style "card_game_button"
                        text_size 18
                        action [Function(witch_user_take_from_ai_anim, selected_exchange_card_index), SetVariable("selected_exchange_card_index", -1), SetVariable("hovered_card_index_exchange", -1)]

    # Deck and Trump Card
    $ deck_text = str(len(card_game.deck.cards)) if len(card_game.deck.cards) > 0 else card_suits[card_game.deck.trump_suit]
    $ deck_xpos = 55 if len(card_game.deck.cards) > 9 else 73

    if card_game.deck.cards:
        if isinstance(card_game, DurakCardGame):
            $ trump = card_game.deck.trump_card
            if trump:
                add Transform(get_card_image(trump), xysize=(CARD_WIDTH, CARD_HEIGHT), rotate=90):
                    xpos CARD_WIDTH // 2 - 55
                    ypos 350

        add Transform(base_cover_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT), rotate=0):
            xpos -50
            ypos 350

        text str(len(card_game.deck.cards)):
            xpos deck_xpos
            ypos 455
            size 60
    elif isinstance(card_game, DurakCardGame) and not card_game.deck.cards:
            text card_suits[card_game.deck.trump_suit]:
                xpos deck_xpos
                ypos 455
                size 75

    # Discard pile
    $ rotate = 0
    for card in card_game.deck.discard:
        add Transform(base_cover_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT), rotate=rotate + 15):
            xpos 1600
            ypos 350
        $ rotate += 15 if rotate < 360 else -360

    if not deal_cards:
        # Opponent hand layout
        if isinstance(card_game, Game21):
            $ opponent_total = card_game.opponent.total21()
            $ opponent_hand_total = "Цена: " + (
                str(opponent_total) if card_game.state in ("reveal", "results")
                else "#" if opponent_total < 10
                else "##"
            )
            frame:
                background RoundRect("#b2b3b4", 10)
                xpos 885
                ypos 300
                xsize 150
                yoffset 10
                padding (5, 5)
                text opponent_hand_total color "#ffffff" text_align 0.5 align (0.5, 0.5) size 25

        for i, card in enumerate(card_game.opponent.hand):
            $ card_x = opponent_card_layout[i]["x"]
            $ card_y = opponent_card_layout[i]["y"]

            if isinstance(card_game, Game21) or isinstance(card_game, WitchGame) and card_game.state == "result" or card_game.result:
                add Transform(get_card_image(card), xysize=(CARD_WIDTH, CARD_HEIGHT)):
                    xpos card_x
                    ypos card_y
            elif isinstance(card_game, WitchGame) and card_game.state == "wait_choice":
                $ is_hovered = (i == hovered_card_index_exchange)
                $ is_adjacent = abs(i - hovered_card_index_exchange) == 1
                $ is_selected = (i == selected_exchange_card_index)

                $ x_shift = 20 if i == hovered_card_index_exchange + 1 else (-20 if i == hovered_card_index_exchange - 1 else 0)
                $ y_shift = 80 if is_hovered or is_selected else 0
                imagebutton:
                    idle Transform(base_cover_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT))
                    hover Transform(base_cover_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT))
                    xpos card_x
                    ypos card_y
                    at hover_offset(y=y_shift, x=x_shift)
                    action If(
                        isinstance(card_game, WitchGame),
                        SetVariable("selected_exchange_card_index", i),
                        Return()
                    )
                    hovered If(hovered_card_index_exchange != i, SetVariable("hovered_card_index_exchange", i))
                    unhovered If(hovered_card_index_exchange == i, SetVariable("hovered_card_index_exchange", -1))
            else:
                add Transform(base_cover_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT)):
                    xpos card_x
                    ypos card_y

        # Player hand
        if isinstance(card_game, Game21):
            $ player_hand_total = "Цена: " + str(card_game.player.total21())
            frame:
                background RoundRect("#b2b3b4", 10)
                xpos 885
                ypos 705
                xsize 150
                padding (5, 5)
                text player_hand_total color "#ffffff" text_align 0.5 align (0.5, 0.5) size 25

        for i, card in enumerate(card_game.player.hand):
            $ card_x = player_card_layout[i]["x"]
            $ card_y = player_card_layout[i]["y"]

            $ is_hovered = (i == hovered_card_index)
            $ is_adjacent = abs(i - hovered_card_index) == 1
            $ is_selected = (i in selected_attack_card_indexes)

            $ x_shift = 20 if i == hovered_card_index + 1 else (-20 if i == hovered_card_index - 1 else 0)
            $ y_shift = -80 if is_hovered or is_selected else 0
            imagebutton:
                idle Transform(get_card_image(card), xysize=(CARD_WIDTH, CARD_HEIGHT))
                hover Transform(get_card_image(card), xysize=(CARD_WIDTH, CARD_HEIGHT))
                xpos card_x
                ypos card_y
                at hover_offset(y=y_shift, x=x_shift)
                action If(
                    isinstance(card_game, DurakCardGame),
                    Function(handle_card_click, i),
                    Return()
                )
                hovered If(hovered_card_index != i, SetVariable("hovered_card_index", i))
                unhovered If(hovered_card_index == i, SetVariable("hovered_card_index", -1))

    if card_game.state == "result" or card_game.result:
        timer 0.5 action Jump(card_game_name + "_game_loop")

screen deal_cards():

    for card_data in dealt_cards:

        $ i = card_data["index"]
        $ delay = card_data["delay"]

        if card_data["owner"] == "player":
            $ dest_x = player_card_layout[i]["x"]
            $ dest_y = player_card_layout[i]["y"]
            $ card_img_src = get_card_image(card_game.player.hand[i])
        else:
            $ dest_x = opponent_card_layout[i]["x"]
            $ dest_y = opponent_card_layout[i]["y"]
            $ card_img_src = base_cover_img_src

        add Transform(card_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT)) at deal_card(dest_x, dest_y, delay)

    timer delay + 1.0 action Jump(card_game_name + "_game_loop")

screen draw_cards():

    for card_data in draw_animations:

        $ i = card_data["index"]
        $ delay = card_data["delay"]

        if card_data["owner"] == "player":
            $ spacing = CARD_SPACING
            $ total = len(card_game.player.hand)
            $ total_width = CARD_WIDTH + (total - 1) * spacing
            $ start_x = max((1920 - total_width) // 2, 20)
            $ dest_x = start_x + i * spacing
            $ dest_y = 825
            $ card_img_src = get_card_image(card_game.player.hand[i])
        else:
            $ spacing = CARD_SPACING
            $ total = len(card_game.opponent.hand)
            $ total_width = CARD_WIDTH + (total - 1) * spacing
            $ start_x = max((1920 - total_width) // 2, 20)
            $ dest_x = start_x + i * spacing
            $ dest_y = 20
            $ card_img_src = base_cover_img_src

        add Transform(card_img_src, xysize=(CARD_WIDTH, CARD_HEIGHT)) at deal_card(dest_x, dest_y, delay)

    timer delay + 1.0 action Jump(card_game_name + "_game_loop")

screen table_card_animation():

    # Animate table cards moving to hand or discard
    for anim in table_animations:

        $ card = anim["card"]
        $ src_x = anim["src_x"]
        $ src_y = anim["src_y"]
        $ dest_x = anim["dest_x"]
        $ dest_y = anim["dest_y"]
        $ delay = anim["delay"]
        $ is_discard = anim["target"] == "discard"

        add Transform(get_card_image(card), xysize=(CARD_WIDTH, CARD_HEIGHT)) at animate_table_card(src_x, src_y, dest_x, dest_y, delay, is_discard)

    timer 0.5 action Hide("table_card_animation")