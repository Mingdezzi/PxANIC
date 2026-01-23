# assets/character_parts.py

# Definitions for Character Customization Parts (9 Presets Each)
# Pixel Grids are 8x8 relative to their draw area (centered on face).
# 1 = Primary Color, 2 = Secondary/White, 0 = Transparent

# 1. Body Types (9 Variants)
# Defined as Polygon Points for Torso relative to (0,0) of Torso Rect (approx 14x10 area)
# Expected Torso Drawing Area is approx 16-20px wide centered on 32px tile.
# Coordinates are relative to CENTER (16, 16) for simplicity in Renderer? 
# Actually, Renderer uses LEGO_NECK, LEGO_HIPS etc. 
# Let's define abstract "Shoulder Width", "Waist Width", "Hip Width" for procedural generation
BODY_TYPES = [
    {'name': 'Average',  'shoulder': 14, 'waist': 12, 'hip': 13}, # Normal
    {'name': 'Slim',     'shoulder': 12, 'waist': 10, 'hip': 11}, # Thin
    {'name': 'Athletic', 'shoulder': 16, 'waist': 11, 'hip': 12}, # V-Shape
    {'name': 'Heavy',    'shoulder': 16, 'waist': 16, 'hip': 16}, # Blocky
    {'name': 'Pear',     'shoulder': 12, 'waist': 12, 'hip': 15}, # Wide Hips
    {'name': 'Strong',   'shoulder': 18, 'waist': 14, 'hip': 14}, # Buff
    {'name': 'Child',    'shoulder': 11, 'waist': 11, 'hip': 11}, # Small
    {'name': 'Curvy',    'shoulder': 13, 'waist': 10, 'hip': 14}, # Hourglass
    {'name': 'Hero',     'shoulder': 20, 'waist': 12, 'hip': 13}, # Exaggerated
]

# [FACE PARTS - 8x8 Grids]
# ... EYES, BROWS, MOUTHS, BEARDS are mostly fine, but let's keep them here 
# (Assuming previous definitions for Face parts are kept or need re-stating if file is wiped. 
#  Since this is replace_file_content with range, I will omit if possible, but the prompt says 5. Ensure TOPS... so I should probably provide full file content mostly or targeted chunks.
#  The user instruction said "Replace Assets...". I will keep Face parts as is if I can target ranges, but replacing WHOLE file is safer for structure change.)

# Let's assume I am rewriting the file content mostly.

# Eyes (Type)
EYES = [
    {'name': 'Classic Dot', 'grid': [[0,0,0,0],[0,1,1,0],[0,1,1,0],[0,0,0,0]]},
    {'name': 'Sharp',       'grid': [[0,0,1,0],[0,1,1,0],[1,1,0,0],[0,0,0,0]]},
    {'name': 'Gentle',      'grid': [[0,0,0,0],[1,1,1,1],[0,1,1,0],[0,0,0,0]]},
    {'name': 'Tired',       'grid': [[0,0,0,0],[0,1,1,0],[0,1,1,0],[1,0,0,1]]}, 
    {'name': 'Wide',        'grid': [[0,1,1,0],[1,1,1,1],[1,1,1,1],[0,1,1,0]]},
    {'name': 'Sparkle',     'grid': [[0,1,1,0],[1,0,2,1],[1,2,0,1],[0,1,1,0]]}, 
    {'name': 'Dead',        'grid': [[0,1,0,1],[1,0,1,0],[0,1,0,1],[1,0,1,0]]}, 
    {'name': 'Robot',       'grid': [[1,1,1,1],[1,2,2,1],[1,1,1,1],[0,0,0,0]]}, 
    {'name': 'Closed',      'grid': [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]]}  
]

# Brows (Type)
BROWS = [
    {'name': 'None',        'grid': []},
    {'name': 'Neat',        'grid': [[0,1,1,0]]},
    {'name': 'Thick',       'grid': [[1,1,1,1],[0,1,1,0]]},
    {'name': 'Angry',       'grid': [[0,0,1,1],[0,1,1,0]]},
    {'name': 'Worried',     'grid': [[1,1,0,0],[0,1,1,0]]},
    {'name': 'Monobrow',    'grid': [[1,1,1,1,1,1]]}, 
    {'name': 'Short',       'grid': [[0,1,1,0]]},
    {'name': 'High Arch',   'grid': [[1,1,1,1]]},
    {'name': 'Scarred',     'grid': [[1,1,0,1],[1,1,0,1]]} 
]

# Mouths (Type)
MOUTHS = [
    {'name': 'Smile',       'grid': [[0,0,0,0],[1,0,0,1],[0,1,1,0]]},
    {'name': 'Poker',       'grid': [[0,0,0,0],[1,1,1,1],[0,0,0,0]]},
    {'name': 'Frown',       'grid': [[0,1,1,0],[1,0,0,1],[0,0,0,0]]},
    {'name': 'Surprised',   'grid': [[0,1,1,0],[1,0,0,1],[1,0,0,1],[0,1,1,0]]},
    {'name': 'Laugh',       'grid': [[1,0,0,1],[0,1,1,0],[0,1,1,0]]},
    {'name': 'Smirk',       'grid': [[0,0,0,1],[0,0,1,0],[0,1,0,0]]},
    {'name': 'Cheeky',      'grid': [[0,0,0,0],[1,1,1,0],[0,0,0,1]]}, 
    {'name': 'Toothy',      'grid': [[1,1,1,1],[1,2,2,1],[1,1,1,1]]}, 
    {'name': 'Cat',         'grid': [[0,1,1,0],[1,0,0,1],[0,0,0,0]]}  
]

# Beards (Type)
BEARDS = [
    {'name': 'Clean',       'grid': []},
    {'name': 'Stubble',     'grid': [[0,1,0,1,0],[1,0,1,0,1]]},
    {'name': 'Goatee',      'grid': [[0,0,0,0,0],[0,1,1,1,0],[0,0,1,0,0]]},
    {'name': 'Mustache',    'grid': [[0,0,0,0,0],[1,1,1,1,1],[0,1,0,1,0]]},
    {'name': 'Full',        'grid': [[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0]]},
    {'name': 'Chinstrap',   'grid': [[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,1]]},
    {'name': 'Mutton',      'grid': [[1,1,0,0,1],[1,1,0,0,1],[1,1,0,0,1]]},
    {'name': 'Dwarf',       'grid': [[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]]},
    {'name': 'Soul Patch',  'grid': [[0,0,0,0,0],[0,0,1,0,0],[0,0,1,0,0]]}
]

# Hair (Type) - 9 Styles - REFIXED (Round 4)
# Head Top is defined as (9, 2) in absolute Renderer terms.
# Here relative to Head Top-Left (0,0 of Head Rect 14x12).
# Hair Front should be around y=0 to y=4 (Forehead).
# Hair Back should be around y=-2 to y=10 (Behind).
HAIR = [
    {'name': 'Bald',      'front': [], 'back': [], 'draw': []},
    {'name': 'Crew Cut',  'front': [{'type':'rect', 'rect':(0,-2,14,3), 'col':'h'}], 'back': [], 'draw': []}, 
    {'name': 'Bob',       'front': [{'type':'rect', 'rect':(0,-1,14,3), 'col':'h'}, {'type':'rect', 'rect':(0,2,2,4), 'col':'h'}, {'type':'rect', 'rect':(12,2,2,4), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(-1,0,16,10), 'col':'h'}]},
    {'name': 'Long',      'front': [{'type':'rect', 'rect':(2,-1,10,3), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(-1,0,16,16), 'col':'h'}]},
    {'name': 'Ponytail',  'front': [{'type':'rect', 'rect':(0,-1,14,3), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(4,-3,6,6), 'col':'h'}, {'type':'rect', 'rect':(5,3,4,8), 'col':'h'}]},
    {'name': 'Spiky',     'front': [{'type':'rect', 'rect':(0,-5,14,5), 'col':'h'}], 'back': []},
    {'name': 'Mohawk',    'front': [{'type':'rect', 'rect':(5,-5,4,8), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(5,-2,4,14), 'col':'h'}]},
    {'name': 'Afro',      'front': [{'type':'rect', 'rect':(-2,-4,18,6), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(-3,-2,20,14), 'col':'h'}]},
    {'name': 'Side Part', 'front': [{'type':'rect', 'rect':(0,-1,14,4), 'col':'h'}], 
                          'back': [{'type':'rect', 'rect':(0,1,14,5), 'col':'h'}]}
]

# Clothes - Top (Type)
# Drawn relative to TORSO bounding box (approx 14x10).
# We use 0-100% mapping in renderer, so we define shapes in 0-100 coordinates.
TOPS = [
    {'name': 'T-Shirt',     'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}]}, 
    {'name': 'Shirt',       'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'rect', 'rect':(45,0,10,100), 'col':'s'}]}, 
    {'name': 'Tank Top',    'draw': [{'type':'rect', 'rect':(15,0,70,100), 'col':'p'}]}, 
    {'name': 'Hoodie',      'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'rect', 'rect':(0,-10,100,10), 'col':'p'}]}, 
    {'name': 'Suit',        'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'poly', 'points':[(50,0),(40,40),(60,40)], 'col':'s'}]}, 
    {'name': 'Sweater',     'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'rect', 'rect':(0,80,100,20), 'col':'s'}]}, 
    {'name': 'Jersey',      'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'rect', 'rect':(30,30,40,40), 'col':'white'}]}, 
    {'name': 'Crop Top',    'draw': [{'type':'rect', 'rect':(0,0,100,60), 'col':'p'}]}, 
    {'name': 'Turtleneck',  'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}, {'type':'rect', 'rect':(20,-10,60,10), 'col':'p'}]} 
]

# Clothes - Bottom (Type)
BOTTOMS = [
    {'name': 'Jeans',       'draw': [{'type':'legs', 'len':'long', 'col':'p'}]},
    {'name': 'Shorts',      'draw': [{'type':'legs', 'len':'short', 'col':'p'}]},
    {'name': 'Skirt',       'draw': [{'type':'skirt', 'len':'short', 'col':'p'}]},
    {'name': 'Long Skirt',  'draw': [{'type':'skirt', 'len':'long', 'col':'p'}]},
    {'name': 'Cargos',      'draw': [{'type':'legs', 'len':'long', 'col':'p'}, {'type':'rect', 'rect':(-5,20,10,20), 'col':'p'}]}, 
    {'name': 'Leggings',    'draw': [{'type':'legs', 'len':'long', 'col':'p'}]},
    {'name': 'Sweatpants',  'draw': [{'type':'legs', 'len':'long', 'col':'p'}, {'type':'rect', 'rect':(0,90,100,10), 'col':'white'}]}, 
    {'name': 'Mini Skirt',  'draw': [{'type':'skirt', 'len':'mini', 'col':'p'}]},
    {'name': 'Swimwear',    'draw': [{'type':'legs', 'len':'briefs', 'col':'p'}]}
]

# Clothes - Shoes (Type)
SHOES = [
    {'name': 'Sneakers',    'draw': [{'type':'rect', 'rect':(0,0,100,100), 'col':'p'}]},
    {'name': 'Boots',       'draw': [{'type':'rect', 'rect':(0,-20,100,120), 'col':'p'}]}, 
    {'name': 'Loafers',     'draw': [{'type':'rect', 'rect':(0,2,100,98), 'col':'p'}, {'type':'rect', 'rect':(20,0,60,10), 'col':'s'}]},
    {'name': 'Sandals',     'draw': [{'type':'rect', 'rect':(0,10,100,90), 'col':'p'}, {'type':'rect', 'rect':(20,0,20,100), 'col':'p'}]},
    {'name': 'Heels',       'draw': [{'type':'rect', 'rect':(0,0,40,100), 'col':'p'}, {'type':'rect', 'rect':(60,0,40,100), 'col':'p'}]},
    {'name': 'Slippers',    'draw': [{'type':'rect', 'rect':(0,5,100,95), 'col':'p'}]},
    {'name': 'High-Tops',   'draw': [{'type':'rect', 'rect':(0,-10,100,110), 'col':'p'}]},
    {'name': 'Barefoot',    'draw': []},
    {'name': 'Combat',      'draw': [{'type':'rect', 'rect':(-5,-10,110,110), 'col':'p'}]}
]

# Accessories - Hats (Type)
HATS = [
    {'name': 'None',      'draw': []},
    {'name': 'Ball Cap',  'draw': [{'type':'rect', 'rect':(0,-2,14,4), 'color':'primary'}, {'type':'rect', 'rect':(0,1,14,1), 'color':'primary'}]},
    {'name': 'Beanie',    'draw': [{'type':'rect', 'rect':(0,-2,14,5), 'color':'primary'}]},
    {'name': 'Fedora',    'draw': [{'type':'rect', 'rect':(1,-5,12,5), 'color':'primary'}, {'type':'rect', 'rect':(-2,-1,18,2), 'color':'primary'}]},
    {'name': 'Top Hat',   'draw': [{'type':'rect', 'rect':(2,-8,10,8), 'color':'primary'}, {'type':'rect', 'rect':(0,0,14,2), 'color':'primary'}]},
    {'name': 'Bandana',   'draw': [{'type':'rect', 'rect':(0,-1,14,4), 'color':'primary'}]},
    {'name': 'Crown',     'draw': [{'type':'poly', 'points':[(0,0),(14,0),(14,-5),(11,-2),(7,-5),(3,-2),(0,-5)], 'color':'primary'}]},
    {'name': 'Headphones','draw': [{'type':'rect', 'rect':(-2,0,3,10), 'color':'primary'}, {'type':'rect', 'rect':(13,0,3,10), 'color':'primary'}, {'type':'rect', 'rect':(0,-2,14,2), 'color':'primary'}]},
    {'name': 'Cat Ears',  'draw': [{'type':'poly', 'points':[(1,-3),(5,-3),(3,-7)], 'color':'primary'}, {'type':'poly', 'points':[(9,-3),(13,-3),(11,-7)], 'color':'primary'}]}
]

# Accessories - Glasses (Type)
GLASSES = [
    {'name': 'None',        'draw': []},
    {'name': 'Square',      'draw': [{'type':'rect', 'rect':(2,4,4,3), 'col':'p'}, {'type':'rect', 'rect':(8,4,4,3), 'col':'p'}, {'type':'rect', 'rect':(6,5,2,1), 'col':'p'}]},
    {'name': 'Round',       'draw': [{'type':'circle', 'rect':(4,5,2), 'col':'p'}, {'type':'circle', 'rect':(10,5,2), 'col':'p'}, {'type':'rect', 'rect':(6,5,2,1), 'col':'p'}]},
    {'name': 'Sunglasses',  'draw': [{'type':'rect', 'rect':(1,4,12,3), 'col':'p'}]},
    {'name': 'Aviator',     'draw': [{'type':'poly', 'points':[(2,4),(6,4),(5,7),(3,7)], 'col':'p'}, {'type':'poly', 'points':[(8,4),(12,4),(11,7),(9,7)], 'col':'p'}, {'type':'rect', 'rect':(6,4,2,1), 'col':'p'}]},
    {'name': 'Visor',       'draw': [{'type':'rect', 'rect':(1,3,12,4), 'col':'p'}]},
    {'name': 'Monocle',     'draw': [{'type':'circle', 'rect':(10,5,2), 'col':'p'}]},
    {'name': 'Eye Patch',   'draw': [{'type':'rect', 'rect':(2,4,4,4), 'col':'p'}, {'type':'line', 'start':(4,4), 'end':(12,0), 'col':'black'}]},
    {'name': 'Goggles',     'draw': [{'type':'rect', 'rect':(0,3,14,5), 'col':'p'}, {'type':'rect', 'rect':(2,4,4,3), 'col':'light'}, {'type':'rect', 'rect':(8,4,4,3), 'col':'light'}]}
]

# Clothes - Coats (Type) - Outerwear
# Drawn ON TOP of everything (except Head)
COATS = [
    {'name': 'None',        'draw': []},
    {'name': 'Vest',        'draw': [{'type':'rect', 'rect':(0,0,30,100), 'col':'p'}, {'type':'rect', 'rect':(70,0,30,100), 'col':'p'}]},
    {'name': 'Jacket',      'draw': [{'type':'rect', 'rect':(-5,-5,110,60), 'col':'p'}, {'type':'rect', 'rect':(45,0,10,100), 'col':'s'}]}, 
    {'name': 'Trench',      'draw': [{'type':'rect', 'rect':(-10,-5,120,110), 'col':'p'}]}, 
    {'name': 'Cape',        'draw': [{'type':'rect', 'rect':(-10,0,120,90), 'col':'p'}, {'type':'rect', 'rect':(40,0,20,10), 'col':'s'}]}, 
    {'name': 'Parka',       'draw': [{'type':'rect', 'rect':(-15,-10,130,80), 'col':'p'}, {'type':'rect', 'rect':(-15,-10,130,20), 'col':'s'}]}, 
    {'name': 'Labcoat',     'draw': [{'type':'rect', 'rect':(-5,0,110,110), 'col':'p'}, {'type':'rect', 'rect':(45,0,10,110), 'col':'white'}]},
    {'name': 'Blazer',      'draw': [{'type':'rect', 'rect':(0,0,40,70), 'col':'p'}, {'type':'rect', 'rect':(60,0,40,70), 'col':'p'}]},
    {'name': 'Robe',        'draw': [{'type':'rect', 'rect':(-10,0,120,120), 'col':'p'}]}
]

# Movement Styles
# Movement Styles (9 Concepts)
MOVEMENT_STYLES = [
    'Heroic', 'Stealthy', 'Limping', 'Cheerful', 'HipHop', 'Normal', 'Moonwalk', 'Cat', 'Dog'
]
