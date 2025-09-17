init python:
    def player_hit():
        card_game._draw_one(card_game.player)
        if card_game.that_s_him and not persistent.achievements.get("Он самый", False):
            renpy.call_in_new_context("show_achievement", "Он самый", "that_s_him_message")
        if card_game.that_s_him and not persistent.achievements.get("Всё теперь на месте", False):
            renpy.call_in_new_context("show_achievement", "Всё теперь на месте", "all_in_place_message")
        if card_game.player.total21() >= 21:
            card_game.finalize()
        compute_hand_layout()

    def player_pass():
        if card_game.state == "player_turn" and card_game.result is None and card_game.first_player == card_game.player:
            card_game.state = "opponent_turn"
        else:
            card_game.finalize()