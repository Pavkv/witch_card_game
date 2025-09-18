init:
    # init
    default card_game = None
    default card_game_name = None
    default player_name = None
    default opponent_name = None
    default base_card_img_src = None
    default base_cover_img_src = None
    default cards_bg = None
    default in_game = True
    default card_game_results = {}
    default card_game_avatar = None
    default biased_draw = None

    # Card selection and layout state
    default hovered_card_index = -1

    # Turn and animation state
    default deal_cards = True
    default next_turn = True
    default dealt_cards = []
    default is_dealing = False
    default draw_animations = []
    default is_drawing = False
    default table_animations = []
    default is_table_animating = False

    # Deck positions
    $ deck_x = 50
    $ deck_y = 350

    # Card layouts
    default player_card_layout = []
    default opponent_card_layout = []

    # Suit translations
    default card_suits = {
        "C": "К",
        "D": "Б",
        "H": "Ч",
        "S": "П"
    }

    # Game phase translations
    default card_game_state_tl = {
        "durak" : {
            "player_attack": "Вы атакуете",
            "player_defend": "Вы защищаетесь",
            "ai_attack": "Противник атакует",
            "ai_defend": "Противник защищается",
            "end_turn": "Окончание хода",
            "results": "Игра окончена"
        },
        "g21": {
            "initial_deal": "Раздача",
            "player_turn": "Ваш ход",
            "opponent_turn": "Ход противника",
            "reveal": "Раскрытие",
            "round_end": "Игра окончена"
        },
        "witch": {
            "player_turn": "Ваш ход",
            "opponent_turn": "Ход противника",
            "wait_choice": "Вытягивание карты",
            "wait_choice_opponent": "Противник вытягивает карту",
            "round_end": "Игра окончена"
        }
    }

    # Card transforms
    transform hover_offset(y=0, x=0):
        easein 0.1 yoffset y xoffset x

    transform no_shift:
        xoffset 0
        yoffset 0

    transform deal_card(dest_x, dest_y, delay=0):
        alpha 0.0
        xpos -50
        ypos 350
        pause delay
        linear 0.3 alpha 1.0 xpos dest_x ypos dest_y

    transform animate_table_card(x1, y1, x2, y2, delay=0.0, discard=False):
        alpha 1.0
        xpos x1
        ypos y1
        pause delay
        linear 0.4 xpos x2 ypos y2 alpha 0

    # Styles
    style card_game_button:
        background RoundRect("#b2b3b4", 10)
        hover_background RoundRect("#757e87", 10)
        xsize 150
        padding (5, 5)
        text_align 0.5
        align (0.5, 0.5)

# Show Achievements
label show_achievement(key, message_tag):
    play sound sfx_achievement
    show expression message_tag at achievement_trans
    with dspr
    $ renpy.pause(3, hard=True)
    hide expression message_tag
    $ persistent.achievements[key] = True
    return