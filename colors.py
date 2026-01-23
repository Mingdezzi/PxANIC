

COLORS = {

    'BG': (10, 10, 12),
    'GRID': (25, 25, 30),
    'GRID_10': (35, 35, 40),
    'GRID_50': (50, 50, 60),
    'GRID_CENTER': (80, 80, 90),
    'TEXT': (180, 180, 190),
    'MAP_BORDER': (80, 20, 20),
    'BLACK': (5, 5, 8),
    'WHITE': (200, 200, 210),
    'DARKNESS': (0, 0, 0),


    'FOG_DAY': (100, 100, 110, 50),
    'FOG_NIGHT': (5, 5, 8, 245),
    'FOG_DAWN': (20, 20, 40, 230),


    'HP_BAR': (139, 0, 0),
    'AP_BAR': (25, 25, 112),
    'STAMINA_BAR': (184, 134, 11),


    'UI_BG': (15, 15, 20, 230),
    'UI_BORDER': (80, 80, 90),
    'SELECTION': (60, 100, 60),
    'COPY_SELECT': (60, 80, 100),
    'ERROR': (150, 50, 50),

    'BUTTON': (40, 40, 50),
    'BUTTON_HOVER': (60, 60, 70),
    'BUTTON_DISABLED': (20, 20, 25),
    'BUTTON_SELECTED': (50, 80, 50),

    'BULLET': (200, 180, 100),
    'BLOOD': (100, 10, 10),


    'GAUGE_BG': (30, 30, 35),
    'GAUGE_BAR': (180, 160, 60),
    'GAUGE_EXHAUST': (150, 40, 40),
    'GAUGE_TARGET': (150, 40, 40),
    'BREATH_BAR': (50, 80, 120),


    'VOTE_BG': (10, 10, 15, 240),
    'VOTE_BTN': (40, 40, 60),
    'VOTE_BTN_HOVER': (60, 60, 80),
    'VOTE_BTN_SELECTED': (80, 80, 100),

    'MSG_INFO': (100, 150, 100),
    'MSG_WARN': (150, 80, 50),
    'MSG_BIG_DEATH': (180, 20, 20),
    'MSG_BIG_SKILL': (180, 160, 50),
    'MSG_DAWN': (80, 90, 120),
    'CHAT_TEXT': (160, 160, 170),

    'MENU_BG': (10, 10, 12),
    'SLOT_BG': (25, 25, 35),
    'ROLE_BTN': (50, 50, 60),


    'SKIN': (180, 140, 110),
    'CLOTHES': (100, 80, 60),
    'SPECTATOR': (80, 80, 120),
    'PATH_LINE': (100, 100, 100),

    'MM_BG': (10, 10, 15, 230),
    'MM_BORDER': (100, 100, 110),
    'MM_PLAYER': (50, 150, 50),
    'MM_MAFIA_PING': (150, 30, 30),
    'MM_POLICE_PING': (50, 50, 150),


    'ROLE_CITIZEN': (60, 120, 60),
    'ROLE_MAFIA': (140, 30, 30),
    'ROLE_POLICE': (40, 60, 120),
    'ROLE_DOCTOR': (160, 140, 60),
    'ROLE_SPECTATOR': (100, 100, 120),


    'MG_ARROW': (80, 120, 140),
    'MG_CIRCLE': (120, 80, 120),
    'MG_SUCCESS': (60, 120, 60),
    'MG_FAIL': (140, 40, 40),
    'MG_PIN': (160, 140, 60),
    'MG_WIRE_RED': (140, 40, 40),
    'MG_WIRE_BLUE': (40, 60, 120),
    'MG_WIRE_YELLOW': (160, 140, 60),

    'FX_SIREN_RED': (180, 20, 20, 60),
    'FX_SIREN_BLUE': (20, 20, 180, 60),
    'FX_BLOOD_BREATH': (100, 0, 0, 80),
    'FX_SWEAT': (100, 150, 180),
}

CUSTOM_COLORS = {
    'SKIN': [
        (255, 224, 189), (255, 205, 148), (234, 192, 134), # Pale, Light, Tan
        (210, 160, 100), (180, 130, 80),  (140, 100, 70),  # Medium, Olive, Brown
        (100, 70, 50),   (70, 40, 30),    (40, 25, 20)     # Dark, Deep, Ebony
    ],
    'EYES': [
        (20, 20, 20),    (80, 50, 20),    (40, 70, 40),    # Black, Brown, Hazel
        (40, 60, 140),   (60, 140, 180),  (80, 180, 100),  # Blue, Cyan, Green
        (160, 40, 40),   (180, 160, 40),  (120, 60, 140)   # Red, Amber, Purple
    ],
    'HAIR': [
        (15, 15, 15),    (60, 40, 20),    (100, 60, 30),   # Black, Dark Brown, Chestnut
        (160, 110, 60),  (220, 180, 80),  (160, 50, 40),   # Light Brown, Blonde, Redhead
        (150, 150, 160), (240, 240, 250), (60, 70, 120)    # Grey, White, Navy
    ],
    'CLOTHES': [
        (230, 230, 235), (30, 30, 35),    (160, 40, 40),   # White, Black, Red
        (40, 100, 40),   (40, 60, 140),   (220, 180, 40),  # Green, Blue, Yellow
        (200, 100, 40),  (100, 50, 140),  (230, 140, 170)  # Orange, Purple, Pink
    ],
    'HAT': [
        (40, 40, 45),    (200, 200, 205), (140, 30, 30),   # Black, White, Red
        (30, 80, 30),    (30, 50, 120),   (180, 150, 40),  # Green, Blue, Yellow
        (150, 80, 30),   (80, 40, 120),   (90, 60, 40)     # Orange, Purple, Brown
    ],
    'SHOES': [
        (25, 25, 30),    (210, 210, 210), (120, 40, 40),   # Black, White, Red
        (40, 80, 40),    (40, 60, 110),   (160, 130, 40),  # Green, Blue, Yellow
        (130, 70, 30),   (70, 40, 100),   (80, 50, 30)     # Orange, Purple, Leather
    ],
    'GLASSES': [
        (20, 20, 20),    (200, 200, 200), (200, 150, 50),  # Black Frame, Silver, Gold
        (40, 40, 150),   (150, 40, 40),   (40, 150, 40),   # Blue Tint, Red Tint, Green Tint
        (50, 50, 50),    (120, 80, 150),  (255, 100, 150)  # Dark, Purple, Pink
    ]
}
