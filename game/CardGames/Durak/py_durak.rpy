init python:
    def handle_card_click(index):
        """Handles card click events for player actions."""
        global confirm_attack, selected_attack_card_indexes, selected_attack_card
        card = card_game.player.hand[index]
        print("Card clicked:", card)

        if card_game.state == "player_attack":
            if index in selected_attack_card_indexes:
                selected_attack_card_indexes.remove(index)
            else:
                selected_attack_card_indexes.add(index)
            confirm_attack = len(selected_attack_card_indexes) > 0

        elif card_game.state == "player_defend" and selected_attack_card:
            if card_game.defend_card(card, selected_attack_card):
                print("Player defended against " + str(selected_attack_card) + " with " + str(card))
                selected_attack_card = None
                card_game.state = "ai_attack"
            else:
                print("Failed to defend with " + str(card))
                selected_attack_card = None

    def confirm_selected_attack():
        """Confirms all selected attack cards."""
        global confirm_attack, selected_attack_card_indexes

        if confirm_attack and selected_attack_card_indexes:
            cards = [card_game.player.hand[i] for i in sorted(selected_attack_card_indexes)]
            if card_game.attack_cards(cards):
                print("Player attacked with: " + ', '.join(str(c) for c in cards))
                card_game.state = "ai_defend"
                selected_attack_card_indexes.clear()
                confirm_attack = False
            else:
                print("Invalid attack. Resetting selection.")
                selected_attack_card_indexes.clear()
                confirm_attack = False
