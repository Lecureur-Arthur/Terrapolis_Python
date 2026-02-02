# settings.py
import pygame

TILE_SIZE = 64
MAP_WIDTH = 15
MAP_HEIGHT = 10
SIDEBAR_WIDTH = 340

# --- MODIFICATIONS ICI ---
QR_MARGIN_WIDTH = 200  # Largeur de la bande QR Code à gauche

# La largeur totale = Bande QR + Carte + Menu Latéral
SCREEN_WIDTH = QR_MARGIN_WIDTH + (MAP_WIDTH * TILE_SIZE) + SIDEBAR_WIDTH
SCREEN_HEIGHT = (MAP_HEIGHT * TILE_SIZE)

# On définit l'offset de la carte pour plus tard
MAP_OFFSET_X = QR_MARGIN_WIDTH 
MAP_OFFSET_Y = 0 # Pas de marge en haut
# -------------------------

FPS = 60

GAME_DURATION = 15 * 60
MATRIX_SAVE_INTERVAL = 15.0 
ACTION_FILE_CHECK_INTERVAL = 0.5 
AI_SUGGESTION_DURATION = 5.0 

# Paramètres Inondation
FLOOD_MIN_INTERVAL = 180
FLOOD_MAX_INTERVAL = 420
FLOOD_DURATION = 20
FLOOD_FADE_DURATION = 5.0 

COLORS = {
    "plain": (100, 200, 100), "forest": (34, 139, 34),
    "mountain": (128, 128, 128), "river": (65, 105, 225),
    "void": (0, 0, 0), "ui_bg": (40, 40, 50),
    "text": (255, 255, 255), "highlight": (255, 215, 0),
    "error": (255, 80, 80), "success": (80, 255, 80),
    "smog": (50, 50, 50), "mud": (101, 67, 33) 
}

BUILDING_IMAGES = {
    "sawmill": "scierie.png",
    "quarry": "carriere.png",
    "coal_plant": "centrale_charbon.png",
    "wind_turbine": "eolienne.png",
    "nuclear_plant": "centrale_nucleaire.png",
    "residence": "habitation.png"
}

# Nom de l'image à charger pour la bordure AR (doit être dans le dossier Assets)
AR_BORDER_IMAGE = "image_ar.png"