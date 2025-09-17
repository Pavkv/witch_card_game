init:
    # Card selection and layout state
    default confirm_attack = False
    default confirm_take = False
    default selected_card = None
    default selected_attack_card = None
    default attack_target = None
    default selected_attack_card_indexes = set()
    default selected_card_indexes = set()

    # Achievements
    default last_attack_two_sixes = True
    default sixes_loss_candidate = False