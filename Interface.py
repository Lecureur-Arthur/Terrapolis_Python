import pygame
import numpy as np
import sys
import json
import os
import random
from datetime import datetime

# ==========================================
# --- 1. CONFIGURATION & DONNÉES ---
# ==========================================

TILE_SIZE = 64
MAP_WIDTH = 15
MAP_HEIGHT = 10
SIDEBAR_WIDTH = 340
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE
FPS = 60
GAME_DURATION = 15 * 60  # 15 minutes
MATRIX_SAVE_INTERVAL = 15.0 
ACTION_FILE_CHECK_INTERVAL = 0.5 

# Paramètres Inondation
FLOOD_MIN_INTERVAL = 180  # 3 minutes minimum
FLOOD_MAX_INTERVAL = 420  # 7 minutes max
FLOOD_DURATION = 20
FLOOD_FADE_DURATION = 5.0 # Temps de transition (séchage) en secondes

COLORS = {
    "plain": (100, 200, 100), "forest": (34, 139, 34),
    "mountain": (128, 128, 128), "river": (65, 105, 225),
    "void": (0, 0, 0), "ui_bg": (40, 40, 50),
    "text": (255, 255, 255), "highlight": (255, 215, 0),
    "error": (255, 80, 80), "success": (80, 255, 80),
    "smog": (50, 50, 50),
    "mud": (101, 67, 33) 
}

BUILDING_COLORS = {
    "sawmill": (139, 69, 19), "quarry": (200, 200, 200),
    "coal_plant": (20, 20, 20), "wind_turbine": (220, 220, 255),
    "nuclear_plant": (100, 0, 100), "residence": (255, 100, 100)
}

BUILDING_SYMBOLS = {
    "sawmill": "🪵", "quarry": "⛏️", "coal_plant": "🏭",
    "wind_turbine": "sw", "nuclear_plant": "☢️", "residence": "🏠"
}

# --- DONNÉES CARTE ---
mountain = np.array([
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
])
plain = np.array([
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1],
    [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0]
])
forest = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
])
river = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
])

# ==========================================
# --- 2. CHARGEMENT JSON ---
# ==========================================

def load_rules_from_json(filename="Rules.json"):
    if not os.path.exists(filename):
        print(f"ERREUR CRITIQUE: '{filename}' introuvable !")
        sys.exit()

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    adj_modifiers = data["common"]["adjacentModifiers"]
    buildings_rules = {}
    
    for key, b_data in data["buildings"].items():
        placement = b_data.get("placement", {})
        construction = b_data.get("construction", {})
        production = b_data.get("production", {})
        operation = b_data.get("operation", {})
        events = b_data.get("events", {})
        additional = b_data.get("additionalInstances", {})
        
        cost_dict = additional.get("cost", construction.get("cost", {"wood": 0, "stones": 0}))
        
        needs_adj = placement.get("operatesIfAdjacentTo")
        if needs_adj == []: needs_adj = None
        
        req_adj = placement.get("placementRequiresAdjacentTile")
        if req_adj == []: req_adj = None

        poll_spread_sec = operation.get("pollutionSpreadAfterSec") or 0
        poll_river_sec = operation.get("pollutesRiverAfterSec") or 0

        rate = production.get("ratePerSec", 0)
        if key == "sawmill": rate = 500.0 / 120.0
        elif key == "quarry": rate = 500.0 / 120.0

        on_destroy = events.get("onPlayerDestroy", {})
        loss_on_destroy = on_destroy.get("loseVirtuosityAmount", construction.get("virtuosityGain", 0))

        flood_rules = events.get("onFlood", {})

        rule = {
            "name": b_data.get("displayName", key),
            "color": BUILDING_COLORS.get(key, (255, 255, 255)),
            "first_free": b_data.get("firstFree", False),
            "forbidden": placement.get("placementForbiddenTiles", []),
            "needs_adj_terrain": needs_adj,
            "requires_adj_terrain": req_adj,
            "cost": cost_dict,
            "production": {
                "resource": production.get("resource"),
                "amount": rate 
            },
            "pollution_on_build": construction.get("pollutionOnBuild", 0),
            "virtuosity_on_build": construction.get("virtuosityGain", 0),
            "virtuosity_loss_on_destroy": loss_on_destroy,
            
            "emits_per_sec": operation.get("emitsPerSec", 0),
            "virtuosity_per_sec": operation.get("virtuosityPerSec", 0),

            "spreads_pollution": operation.get("affectsAdjacentTiles", False),
            "pollution_spread_after_sec": poll_spread_sec,
            
            "river_pollution_amount": operation.get("riverPollutionAmount", 0),
            "pollutes_river_after_sec": poll_river_sec,
            
            "on_flood": {
                "destroyed": flood_rules.get("destroyed", False),
                "floodScoreIncrease": flood_rules.get("floodScoreIncrease", 0)
            }
        }
        buildings_rules[key] = rule

    return buildings_rules, adj_modifiers

BUILDING_RULES, ADJACENT_MODIFIERS = load_rules_from_json()

# ==========================================
# --- 3. JEU ---
# ==========================================

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("City Builder - Terrapolis")

        self.score_font = pygame.font.SysFont("Arial", 14, bold=True)
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.timer_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 12)
        self.tiny_font = pygame.font.SysFont("Arial", 10)

        try:
            self.icon_font = pygame.font.SysFont("Segoe UI Emoji", 32)
        except:
            self.icon_font = pygame.font.SysFont("Arial", 32)
        
        self.clock = pygame.time.Clock()
        
        self.retry_rect = None
        self.quit_rect = None

        self.reset_game()

    def reset_game(self):
        self.resources = {"wood": 0, "stones": 0, "virtuosity": 0}
        self.building_counts = {k: 0 for k in BUILDING_RULES.keys()} 
        self.destroyed_counts = {k: 0 for k in BUILDING_RULES.keys()}
        
        self.selected_building = None
        self.last_production_time = pygame.time.get_ticks()
        
        # --- TIMERS ---
        self.last_matrix_save_time = pygame.time.get_ticks()
        self.last_action_check_time = pygame.time.get_ticks()
        self.last_action_file_date = ""

        # --- INONDATION & POLLUTION SPECIALE ---
        self.flooded_grid = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool) 
        
        # Logique inondation (0, 1 ou 2 fois par partie)
        self.max_floods_game = random.randint(0, 2)
        self.floods_occurred = 0
        
        self.next_flood_time = random.randint(FLOOD_MIN_INTERVAL, FLOOD_MAX_INTERVAL) 
        self.flood_timer = 0 
        self.flood_clear_timer = 0 
        self.flood_pollution_total = 0 
        
        print(f"DEBUG: Partie lancée avec {self.max_floods_game} inondations prévues.")
        # ---------------------------------------
        
        self.message = "Bienvenue."
        self.message_color = COLORS["text"]
        
        self.map_data = self.generate_map()

        self.time_left = GAME_DURATION
        self.game_over = False
        self.final_stats = {}

        self.tile_resources = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] == "forest":
                    self.tile_resources[y][x] = 500.0
                elif self.map_data[y][x] == "mountain":
                    self.tile_resources[y][x] = 500.0

        self.forests_destroyed_count = 0

        self.buildings_grid = [[None for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.building_timestamps = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)
        
        self.pol_build_grid = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)
        self.pol_duration_grid = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)

        self.virt_build_grid = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)
        self.virt_duration_grid = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=float)

    def generate_map(self):
        game_map = np.full((MAP_HEIGHT, MAP_WIDTH), "void", dtype=object)
        game_map[plain == 1] = "plain"
        game_map[forest == 1] = "forest"
        game_map[mountain == 1] = "mountain"
        game_map[river == 1] = "river"
        return game_map

    def check_adjacency(self, x, y, target, is_terrain=True):
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if isinstance(target, str): targets = [target]
        elif isinstance(target, list): targets = target
        else: return False

        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if is_terrain:
                    if self.map_data[ny][nx] in targets: return True
                else:
                    if self.buildings_grid[ny][nx] in targets: return True
        return False

    def place_building(self, x, y):
        if self.game_over: return
        if not self.selected_building: return
        
        if self.selected_building == "demolish":
            b_target = self.buildings_grid[y][x]
            if b_target:
                # Démolition manuelle = is_flood=False
                self.execute_action(x, y, b_target, -1, is_flood=False)
            else:
                self.message = "Rien à détruire ici."
                self.message_color = COLORS["text"]
        else:
            self.execute_action(x, y, self.selected_building, 1)

    def execute_action(self, x, y, b_key, action_type, is_flood=False):
        if self.game_over: return
        if action_type == 0: return

        # --- DESTRUCTION ---
        if action_type == -1:
            current_b = self.buildings_grid[y][x]
            if current_b and (current_b == b_key or b_key == "ANY"):
                
                # Cas 1 : Démolition par le joueur (Nettoyage complet)
                if not is_flood:
                    b_rules = BUILDING_RULES[current_b]
                    virt_lost = b_rules.get("virtuosity_loss_on_destroy", 0)
                    
                    self.resources["virtuosity"] -= virt_lost
                    if self.resources["virtuosity"] < 0: self.resources["virtuosity"] = 0
                    
                    self.pol_build_grid[y][x] = 0
                    self.pol_duration_grid[y][x] = 0
                    self.virt_build_grid[y][x] = 0
                    
                    self.message = f"Détruit ! -{virt_lost} Virtuosité."
                    self.message_color = (255, 100, 100)
                
                # Cas 2 : Destruction par Inondation (On garde l'historique de la case)
                else:
                    pass

                self.buildings_grid[y][x] = None
                self.building_counts[current_b] -= 1
                self.destroyed_counts[current_b] += 1
                
            return

        # --- CONSTRUCTION (action_type == 1) ---
        if action_type == 1:
            terrain = self.map_data[y][x]
            rules = BUILDING_RULES.get(b_key)
            if not rules: return 

            if self.buildings_grid[y][x] is not None:
                self.message = "Case occupée !"
                self.message_color = COLORS["error"]
                return
            
            if self.flooded_grid[y][x]:
                self.message = "Terrain inondé (Boue) !"
                self.message_color = COLORS["mud"]
                return

            if terrain in rules.get("forbidden", []):
                self.message = f"Interdit sur {terrain}"
                self.message_color = COLORS["error"]
                return

            cost_wood = rules["cost"].get("wood", 0)
            cost_stones = rules["cost"].get("stones", 0)
            
            is_free = False
            if b_key in ["sawmill", "quarry"]:
                if self.building_counts[b_key] == 0:
                    if self.resources["wood"] < cost_wood or self.resources["stones"] < cost_stones:
                        is_free = True

            if is_free: cost_wood, cost_stones = 0, 0

            if self.resources["wood"] < cost_wood or self.resources["stones"] < cost_stones:
                self.message = "Pas assez de ressources !"
                self.message_color = COLORS["error"]
                return

            req_terrain = rules.get("needs_adj_terrain")
            if req_terrain and not self.check_adjacency(x, y, req_terrain, is_terrain=True):
                self.message = f"Doit toucher : {req_terrain}"
                self.message_color = COLORS["error"]
                return
            
            req_adj_list = rules.get("requires_adj_terrain")
            if req_adj_list and not self.check_adjacency(x, y, req_adj_list, is_terrain=True):
                self.message = f"Doit toucher : {req_adj_list}"
                self.message_color = COLORS["error"]
                return

            self.resources["wood"] -= cost_wood
            self.resources["stones"] -= cost_stones
            self.buildings_grid[y][x] = b_key
            self.building_counts[b_key] += 1
            
            self.building_timestamps[y][x] = pygame.time.get_ticks() / 1000.0
            
            p_val = rules.get("pollution_on_build", 0)
            self.pol_build_grid[y][x] += p_val
            
            v_val = rules.get("virtuosity_on_build", 0)
            self.virt_build_grid[y][x] += v_val
            self.resources["virtuosity"] += v_val
            
            if is_free:
                self.message = f"{rules['name']} (Secours) construit !"
            else:
                self.message = f"{rules['name']} construit !"
            self.message_color = COLORS["success"]

    def check_external_actions(self):
        proj_root = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(proj_root, 'Action', 'action.txt')
        if not os.path.exists(filename):
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines: return

            file_date = lines[0].strip()
            if file_date == self.last_action_file_date:
                return 
            
            self.last_action_file_date = file_date
            print(f"Nouvelles actions détectées : {file_date}")
            self.message = "IA : Exécution des ordres..."
            self.message_color = (100, 200, 255)

            current_building = None
            grid_row = 0
            
            for line in lines[1:]:
                line = line.strip()
                if not line: continue
                
                if line.startswith("===") and line.endswith("==="):
                    b_name = line.replace("=", "").strip()
                    if b_name in BUILDING_RULES:
                        current_building = b_name
                        grid_row = 0
                    continue
                
                if current_building and grid_row < MAP_HEIGHT:
                    parts = line.split()
                    if len(parts) >= MAP_WIDTH:
                        for col in range(MAP_WIDTH):
                            try:
                                val = int(parts[col])
                                if val != 0:
                                    self.execute_action(col, grid_row, current_building, val, is_flood=False)
                            except ValueError:
                                pass
                        grid_row += 1

        except Exception as e:
            print(f"Erreur lecture action.txt : {e}")

    def save_matrix_snapshot(self):
        map_folder = "Batiment_Maps"
        if not os.path.exists(map_folder):
            os.makedirs(map_folder)

        matrix_filename = f"{map_folder}/matrix_state.txt"
        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        full_matrix_content = f"Snapshot Date: {now_str}\n\n"

        terrain_types = ['mountain', 'plain', 'forest', 'river']
        for t_type in terrain_types:
            full_matrix_content += f"=== {t_type} ===\n"
            for y in range(MAP_HEIGHT):
                row_vals = []
                for x in range(MAP_WIDTH):
                    if self.map_data[y][x] == t_type:
                        row_vals.append("1")
                    else:
                        row_vals.append("0")
                full_matrix_content += " ".join(row_vals) + "\n"
            full_matrix_content += "\n"
        
        full_matrix_content += f"=== FLOOD ===\n"
        for y in range(MAP_HEIGHT):
            row_vals = []
            for x in range(MAP_WIDTH):
                if self.flooded_grid[y][x]:
                     row_vals.append("1")
                else:
                    row_vals.append("0")
            full_matrix_content += " ".join(row_vals) + "\n"
        full_matrix_content += "\n"

        target_types = ['sawmill', 'quarry', 'coal_plant', 'wind_turbine', 'nuclear_plant', 'residence']
        for b_type in target_types:
            full_matrix_content += f"=== {b_type} ===\n"
            for y in range(MAP_HEIGHT):
                row_vals = []
                for x in range(MAP_WIDTH):
                    if self.buildings_grid[y][x] == b_type:
                        row_vals.append("1")
                    else:
                        row_vals.append("0")
                full_matrix_content += " ".join(row_vals) + "\n"
            full_matrix_content += "\n"

        try:
            with open(matrix_filename, "w", encoding="utf-8") as f:
                f.write(full_matrix_content)
        except Exception as e:
            print(f"Erreur sauvegarde snapshot : {e}")

    def save_game_results(self):
        folder_name = "Terrapolis_Save"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{folder_name}/Save_{now}.txt"
        
        virt = int(self.final_stats.get("virtuosity", 0))
        pol_total = int(self.final_stats.get("pollution_total", 0))
        score = int(self.final_stats.get("score", 0))
        
        pol_build = int(np.sum(self.pol_build_grid))
        pol_dur = int(np.sum(self.pol_duration_grid))
        pol_flood = int(self.flood_pollution_total)
        
        content = f"=== RAPPORT DE FIN DE PARTIE - TERRAPOLIS ===\n"
        content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        content += f"SCORE FINAL : {score}\n"
        content += f"---------------------------------------\n"
        content += f"Virtuosité      : {virt}\n"
        content += f"Pollution Totale: {pol_total}\n"
        content += f"  > Construction: {pol_build}\n"
        content += f"  > Durée       : {pol_dur}\n"
        content += f"  > Inondation  : {pol_flood}\n\n"
        content += f"BÂTIMENTS (Construits / Détruits):\n"
        
        for key, rule in BUILDING_RULES.items():
            built = self.building_counts[key]
            destroyed = self.destroyed_counts[key]
            content += f"- {rule['name']:<18} : {built} / {destroyed}\n"
            
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Sauvegarde réussie : {filename}")
            self.message = f"Sauvegardé : Save_{now}.txt"
        except Exception as e:
            print(f"Erreur de sauvegarde : {e}")
    
    # =========================================================================
    # --- LOGIQUE INONDATION AMÉLIORÉE (PAR ZONES) ---
    # =========================================================================
    def trigger_flood(self):
        # 1. Identifier toutes les tuiles candidates (adjacentes à la rivière, non rivière)
        candidates_list = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map_data[y][x] == "river":
                    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dx, dy in deltas:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                            if self.map_data[ny][nx] not in ["river", "void"]:
                                candidates_list.append((nx, ny))
        
        # Supprimer les doublons s'il y en a
        candidates_list = list(set(candidates_list))
        total_candidates = len(candidates_list)
        
        if total_candidates == 0:
            return

        # 2. Définir le nombre de tuiles à inonder (Au moins 1/3, Max 2/3)
        min_flood = max(1, int(total_candidates / 3))
        max_flood = max(min_flood + 1, int(total_candidates * 2 / 3)) 
        
        target_count = random.randint(min_flood, max_flood)
        
        # 3. Sélection par propagation de zone (Cluster)
        flooded_selection = set()
        candidates_set = set(candidates_list)
        
        while len(flooded_selection) < target_count and candidates_set:
            # Choisir une "graine" (point de départ d'une zone)
            seed = random.choice(list(candidates_set))
            
            # File d'attente pour l'expansion de cette zone
            zone_frontier = [seed]
            
            # Tant qu'on peut étendre cette zone et qu'on n'a pas atteint le quota global
            while zone_frontier and len(flooded_selection) < target_count:
                # On prend une tuile aléatoire dans la frontière pour donner une forme organique
                idx = random.randint(0, len(zone_frontier) - 1)
                curr = zone_frontier.pop(idx)
                
                if curr in flooded_selection:
                    continue
                
                # Valider l'inondation
                flooded_selection.add(curr)
                if curr in candidates_set:
                    candidates_set.remove(curr)
                
                # Ajouter les voisins éligibles à la frontière
                cx, cy = curr
                deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dx, dy in deltas:
                    nx, ny = cx + dx, cy + dy
                    neighbor = (nx, ny)
                    # Si le voisin est un candidat valide et pas encore inondé
                    if neighbor in candidates_set and neighbor not in flooded_selection:
                        if neighbor not in zone_frontier:
                            zone_frontier.append(neighbor)

        print(f"--- INONDATION DÉCLENCHÉE : {len(flooded_selection)} tuiles (Cible: {target_count}) ---")
        
        count_destroyed = 0
        new_flood_pollution = 0

        # 4. Appliquer les effets
        for (fx, fy) in flooded_selection:
            self.flooded_grid[fy][fx] = True
            
            b_name = self.buildings_grid[fy][fx]
            if b_name:
                rules = BUILDING_RULES.get(b_name)
                flood_rules = rules.get("on_flood", {})
                
                poll_increase = flood_rules.get("floodScoreIncrease", 0)
                if poll_increase > 0:
                    new_flood_pollution += poll_increase
                
                if flood_rules.get("destroyed", False):
                    # On détruit avec is_flood=True pour ne pas perdre les stats
                    self.execute_action(fx, fy, b_name, -1, is_flood=True) 
                    count_destroyed += 1

        if new_flood_pollution > 0:
            self.flood_pollution_total += new_flood_pollution
            
        self.message = f"CRUE ! {len(flooded_selection)} zones inondées. {count_destroyed} bâtiments détruits."
        if new_flood_pollution > 0:
            self.message += f" (Pollution +{new_flood_pollution})"
        self.message_color = (255, 100, 100)
        
        self.flood_clear_timer = FLOOD_DURATION
        self.floods_occurred += 1  # Incrémentation du compteur de crues

    def clear_flood(self):
        self.flooded_grid.fill(False)
        self.message = "L'eau se retire. La terre sèche."
        self.message_color = (200, 200, 100)
    # =========================================================================

    def update_game_logic(self, dt_seconds):
        if not self.game_over:
            self.time_left -= dt_seconds
            if self.time_left <= 0:
                self.time_left = 0
                self.game_over = True
                
                virtuosity_globale = self.resources["virtuosity"]
                
                pol_const = np.sum(self.pol_build_grid)
                pol_duree = np.sum(self.pol_duration_grid)
                pol_flood = self.flood_pollution_total
                
                pollution_totale = pol_const + pol_duree + pol_flood
                
                score_final = virtuosity_globale - pollution_totale
                
                # --- SAUVEGARDE DETAILLEE DES STATS POUR AFFICHAGE ---
                self.final_stats = {
                    "virtuosity": int(virtuosity_globale),
                    "pollution_total": int(pollution_totale),
                    "pol_const": int(pol_const),
                    "pol_duree": int(pol_duree),
                    "pol_flood": int(pol_flood),
                    "score": int(score_final)
                }
                
                self.message = f"PARTIE TERMINÉE ! Score: {int(score_final)}"
                self.message_color = (255, 215, 0)
                self.save_game_results()

        if self.game_over:
            return

        now_ms = pygame.time.get_ticks()
        now_sec = now_ms / 1000.0
        
        # --- GESTION INONDATION (Limitée par max_floods_game) ---
        if self.floods_occurred < self.max_floods_game:
            self.flood_timer += dt_seconds
            if self.flood_timer >= self.next_flood_time:
                self.trigger_flood()
                self.flood_timer = 0
                self.next_flood_time = random.randint(FLOOD_MIN_INTERVAL, FLOOD_MAX_INTERVAL)
            
        if self.flood_clear_timer > 0:
            self.flood_clear_timer -= dt_seconds
            if self.flood_clear_timer <= 0:
                self.clear_flood()
        # --------------------------

        if now_ms - self.last_action_check_time > (ACTION_FILE_CHECK_INTERVAL * 1000):
            self.check_external_actions()
            self.last_action_check_time = now_ms

        if now_ms - self.last_matrix_save_time > (MATRIX_SAVE_INTERVAL * 1000):
            self.save_matrix_snapshot()
            self.last_matrix_save_time = now_ms

        # Production Logic
        if now_ms - self.last_production_time > 1000: 
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    b_name = self.buildings_grid[y][x]
                    if b_name:
                        if self.flooded_grid[y][x]: 
                            continue

                        rules = BUILDING_RULES[b_name]
                        prod = rules.get("production")
                        
                        if prod and prod["amount"] > 0 and prod["resource"]:
                            needed_terrain = rules.get("needs_adj_terrain")
                            
                            if needed_terrain:
                                deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                for dx, dy in deltas:
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                                        if self.map_data[ny][nx] in needed_terrain:
                                            if self.tile_resources[ny][nx] > 0:
                                                amount = prod["amount"]
                                                self.tile_resources[ny][nx] -= amount
                                                self.resources[prod["resource"]] += amount
                                                
                                                if self.tile_resources[ny][nx] <= 0:
                                                    if self.map_data[ny][nx] == "forest":
                                                        self.forests_destroyed_count += 1
                                                        count = self.forests_destroyed_count
                                                        
                                                        loss_pct = 0.0
                                                        if count <= 10: loss_pct = 0.01 
                                                        elif count <= 15: loss_pct = 0.02 
                                                        elif count <= 25: loss_pct = 0.05 
                                                        elif count <= 30: loss_pct = 0.10 
                                                        else: loss_pct = 0.20 
                                                        
                                                        amount_lost = int(self.resources["virtuosity"] * loss_pct)
                                                        self.resources["virtuosity"] -= amount_lost
                                                        if self.resources["virtuosity"] < 0: self.resources["virtuosity"] = 0
                                                        
                                                        self.message = f"Forêt détruite ! -{amount_lost} Virtuosité ({int(loss_pct*100)}%)"
                                                        self.message_color = (255, 50, 50)

                                                    self.tile_resources[ny][nx] = 0
                                                    self.map_data[ny][nx] = "plain"
                                                break 
                            else:
                                self.resources[prod["resource"]] += prod["amount"]
                                
            self.last_production_time = now_ms

        # Pollution & Virtuosity per second
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                b_name = self.buildings_grid[y][x]
                if b_name:
                    rules = BUILDING_RULES[b_name]
                    age = now_sec - self.building_timestamps[y][x]
                    
                    virt_gain = rules.get("virtuosity_per_sec", 0) * dt_seconds
                    if virt_gain > 0:
                        self.resources["virtuosity"] += virt_gain
                        self.virt_duration_grid[y][x] += virt_gain

                    emission = rules.get("emits_per_sec", 0) * dt_seconds
                    if emission > 0:
                        self.pol_duration_grid[y][x] += emission
                        
                        spread_delay = rules.get("pollution_spread_after_sec", 0)
                        if rules.get("spreads_pollution"):
                            if age >= spread_delay:
                                deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                for dx, dy in deltas:
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                                        neighbor = self.buildings_grid[ny][nx]
                                        mod = ADJACENT_MODIFIERS.get(neighbor, 1.0) if neighbor else 1.0
                                        self.pol_duration_grid[ny][nx] += (emission * 0.5) * mod
                    
                    target_amount = rules.get("river_pollution_amount", 0)
                    delay = rules.get("pollutes_river_after_sec", 0)
                    
                    if target_amount > 0:
                        if delay > 0:
                            fill_rate = target_amount / delay
                            if self.check_adjacency(x, y, "river", is_terrain=True):
                                deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                for dx, dy in deltas:
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                                        if self.map_data[ny][nx] == "river":
                                            current_val = self.pol_duration_grid[ny][nx]
                                            if current_val < target_amount:
                                                addition = fill_rate * dt_seconds
                                                if current_val + addition > target_amount:
                                                    self.pol_duration_grid[ny][nx] = target_amount
                                                else:
                                                    self.pol_duration_grid[ny][nx] += addition
                        else:
                            if self.check_adjacency(x, y, "river", is_terrain=True):
                                deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                for dx, dy in deltas:
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                                        if self.map_data[ny][nx] == "river":
                                            self.pol_duration_grid[ny][nx] += target_amount * dt_seconds

    def draw(self):
        self.screen.fill(COLORS["ui_bg"])
        
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # --- DESSIN DU SOL ---
                # EFFET DE TRANSITION BOUE -> COULEUR NORMALE
                if self.flooded_grid[y][x]:
                    if self.flood_clear_timer <= FLOOD_FADE_DURATION:
                        # Calcul du ratio de mélange (0.0 = boue pure, 1.0 = couleur normale)
                        t = 1.0 - (self.flood_clear_timer / FLOOD_FADE_DURATION)
                        t = max(0.0, min(1.0, t))
                        
                        original_color = COLORS.get(self.map_data[y][x], (0,0,0))
                        mud_color = COLORS["mud"]
                        
                        # Interpolation linéaire
                        r = mud_color[0] + (original_color[0] - mud_color[0]) * t
                        g = mud_color[1] + (original_color[1] - mud_color[1]) * t
                        b = mud_color[2] + (original_color[2] - mud_color[2]) * t
                        draw_color = (int(r), int(g), int(b))
                        
                        pygame.draw.rect(self.screen, draw_color, rect)
                    else:
                        pygame.draw.rect(self.screen, COLORS["mud"], rect)
                else:
                    color = COLORS.get(self.map_data[y][x], (0,0,0))
                    pygame.draw.rect(self.screen, color, rect)
                
                pygame.draw.rect(self.screen, (30,30,30), rect, 1)

                if self.map_data[y][x] in ["forest", "mountain"] and not self.flooded_grid[y][x]:
                    qty = int(self.tile_resources[y][x])
                    if qty > 0:
                        if self.map_data[y][x] == "forest":
                            txt_color = (180, 255, 180); bg_color = (20, 60, 20)
                        else:
                            txt_color = (220, 220, 220); bg_color = (40, 40, 40)
                        res_surf = self.score_font.render(str(qty), True, txt_color)
                        res_rect = res_surf.get_rect(topleft=(rect.left + 5, rect.top + 5))
                        bg_rect = res_rect.inflate(8, 4)
                        pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=4)
                        pygame.draw.rect(self.screen, (200,200,200), bg_rect, 1, border_radius=4)
                        self.screen.blit(res_surf, res_rect)

                building = self.buildings_grid[y][x]
                if building:
                    b_color = BUILDING_RULES[building]["color"]
                    b_rect = rect.inflate(-10, -10)
                    pygame.draw.rect(self.screen, b_color, b_rect)
                    pygame.draw.rect(self.screen, (0,0,0), b_rect, 2)
                    
                    symbol = BUILDING_SYMBOLS.get(building, "?")
                    if building == "wind_turbine":
                        anim_frame = (pygame.time.get_ticks() // 150) % 4
                        symbol = ["|", "/", "-", "\\"][anim_frame]

                    font_to_use = getattr(self, 'icon_font', self.font)
                    txt_surf = font_to_use.render(symbol, True, (40, 40, 40))
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    self.screen.blit(txt_surf, txt_rect)

                    river_delay = BUILDING_RULES[building].get("pollutes_river_after_sec", 0)
                    spread_delay = BUILDING_RULES[building].get("pollution_spread_after_sec", 0)
                    age = (pygame.time.get_ticks()/1000.0) - self.building_timestamps[y][x]
                    
                    if river_delay > 0 and age < river_delay:
                        progress = age / river_delay
                        pygame.draw.arc(self.screen, (255, 50, 50), b_rect, 0, progress * 6.28, 3)
                    elif spread_delay > 0 and age < spread_delay:
                         pygame.draw.circle(self.screen, (255, 255, 0), b_rect.topleft, 4)

                p_build = self.pol_build_grid[y][x]
                p_dur = self.pol_duration_grid[y][x]
                
                # --- EFFET VISUEL DE POLLUTION RETIRÉ ---
                # ----------------------------------------

                if p_build > 0:
                    txt_b = f"{int(p_build)}"
                    surf_b = self.score_font.render(txt_b, True, (255, 200, 50))
                    bg_rect_b = surf_b.get_rect(midleft=(rect.left + 5, rect.centery - 8))
                    bg_rect_b.inflate_ip(6, 4)
                    pygame.draw.rect(self.screen, (0, 0, 0), bg_rect_b, border_radius=4)
                    self.screen.blit(surf_b, surf_b.get_rect(center=bg_rect_b.center))

                if p_dur > 1:
                    txt_d = f"{int(p_dur)}"
                    surf_d = self.score_font.render(txt_d, True, (255, 80, 80))
                    bg_rect_d = surf_d.get_rect(bottomleft=(rect.left + 5, rect.bottom - 5))
                    bg_rect_d.inflate_ip(6, 4)
                    pygame.draw.rect(self.screen, (0, 0, 0), bg_rect_d, border_radius=4)
                    self.screen.blit(surf_d, surf_d.get_rect(center=bg_rect_d.center))

                v_build = self.virt_build_grid[y][x]
                v_dur = self.virt_duration_grid[y][x]

                if v_build > 0:
                    txt_vb = f"{int(v_build)}"
                    surf_vb = self.score_font.render(txt_vb, True, (0, 255, 255))
                    bg_rect_vb = surf_vb.get_rect(topright=(rect.right - 5, rect.top + 5))
                    bg_rect_vb.inflate_ip(6, 4)
                    pygame.draw.rect(self.screen, (0, 50, 50), bg_rect_vb, border_radius=4)
                    self.screen.blit(surf_vb, surf_vb.get_rect(center=bg_rect_vb.center))

                if v_dur > 1:
                    txt_vo = f"{int(v_dur)}"
                    surf_vo = self.score_font.render(txt_vo, True, (100, 255, 100))
                    bg_rect_vo = surf_vo.get_rect(bottomright=(rect.right - 5, rect.bottom - 5))
                    bg_rect_vo.inflate_ip(6, 4)
                    pygame.draw.rect(self.screen, (0, 50, 0), bg_rect_vo, border_radius=4)
                    self.screen.blit(surf_vo, surf_vo.get_rect(center=bg_rect_vo.center))

        ui_x = MAP_WIDTH * TILE_SIZE + 10
        y_offset = 10

        mins = int(self.time_left // 60)
        secs = int(self.time_left % 60)
        color_timer = (255, 255, 255)
        if self.time_left < 60: color_timer = (255, 50, 50) 
        timer_txt = f"TEMPS RESTANT: {mins:02}:{secs:02}"
        self.screen.blit(self.timer_font.render(timer_txt, True, color_timer), (ui_x, y_offset))
        y_offset += 30
        
        # Timer prochaine crue
        if self.floods_occurred < self.max_floods_game:
            flood_in = int(self.next_flood_time - self.flood_timer)
            flood_col = (100, 200, 255) if flood_in > 10 else (255, 50, 50)
            self.screen.blit(self.small_font.render(f"Prochaine crue : {flood_in}s", True, flood_col), (ui_x, y_offset))
        else:
            self.screen.blit(self.small_font.render("Aucune crue prévue", True, (100, 255, 100)), (ui_x, y_offset))
        y_offset += 20
        
        total_build = int(np.sum(self.pol_build_grid))
        total_dur = int(np.sum(self.pol_duration_grid))
        lbl1 = self.font.render(f"POL CONSTR: {total_build}", True, (255, 200, 50))
        lbl2 = self.font.render(f"POL DUREE:  {total_dur}", True, (255, 80, 80))
        # Affichage pollution inondation en temps réel
        lbl3 = self.font.render(f"POL CRUE:   {int(self.flood_pollution_total)}", True, (200, 100, 255))
        
        self.screen.blit(lbl1, (ui_x, y_offset))
        self.screen.blit(lbl2, (ui_x, y_offset + 20))
        self.screen.blit(lbl3, (ui_x, y_offset + 40))
        y_offset += 70

        for res, amount in self.resources.items():
            color = COLORS["text"]
            if res == "virtuosity": color = (100, 255, 200)
            txt = f"{res.capitalize()}: {int(amount)}"
            self.screen.blit(self.font.render(txt, True, color), (ui_x, y_offset))
            y_offset += 20
        y_offset += 20
        pygame.draw.line(self.screen, (100,100,100), (ui_x, y_offset), (SCREEN_WIDTH-10, y_offset), 1)
        y_offset += 20
        
        mouse_pos = pygame.mouse.get_pos()

        demolish_rect = pygame.Rect(ui_x, y_offset, SIDEBAR_WIDTH-20, 40)
        is_demolish_mode = (self.selected_building == "demolish")
        
        if is_demolish_mode:
            pygame.draw.rect(self.screen, (100, 40, 40), demolish_rect)
            pygame.draw.rect(self.screen, (255, 80, 80), demolish_rect, 2)
        elif demolish_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (70, 40, 40), demolish_rect)
        else:
            pygame.draw.rect(self.screen, (50, 30, 30), demolish_rect)

        self.screen.blit(self.font.render("DÉMOLIR", True, (255, 100, 100)), (ui_x + 40, y_offset + 10))
        try:
            ico = self.icon_font.render("💣", True, (255, 100, 100))
            self.screen.blit(ico, (ui_x + 5, y_offset - 2))
        except: pass

        if pygame.mouse.get_pressed()[0] and demolish_rect.collidepoint(mouse_pos):
            self.selected_building = "demolish"
            self.message = "Mode Destruction actif"
            self.message_color = (255, 100, 100)
        y_offset += 50

        for b_key, b_data in BUILDING_RULES.items():
            click_rect = pygame.Rect(ui_x, y_offset, SIDEBAR_WIDTH-20, 40)
            
            if self.selected_building == b_key:
                pygame.draw.rect(self.screen, (60,60,80), click_rect)
                pygame.draw.rect(self.screen, COLORS["highlight"], click_rect, 2)
            elif click_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (50,50,60), click_rect)
                
            name = self.font.render(b_data['name'], True, COLORS["text"])
            self.screen.blit(name, (ui_x + 30, y_offset + 2))
            
            pygame.draw.rect(self.screen, b_data['color'], (ui_x + 5, y_offset+10, 15, 15))
            pygame.draw.rect(self.screen, (200,200,200), (ui_x + 5, y_offset+10, 15, 15), 1)
            
            w, s = b_data['cost'].get('wood',0), b_data['cost'].get('stones',0)
            
            is_free_display = False
            if b_key in ["sawmill", "quarry"]:
                if self.building_counts[b_key] == 0:
                    if self.resources["wood"] < w or self.resources["stones"] < s:
                        is_free_display = True
            
            cost_txt = "Gratuit (Secours)" if is_free_display else f"Bois:{w}  Pierre:{s}"
            col_cost = (150, 255, 150) if is_free_display else (180,180,180)
            self.screen.blit(self.small_font.render(cost_txt, True, col_cost), (ui_x+30, y_offset+20))

            if pygame.mouse.get_pressed()[0]:
                if click_rect.collidepoint(mouse_pos):
                    self.selected_building = b_key
                    self.message = f"Mode Construction : {b_data['name']}"
                    self.message_color = COLORS["text"]
            y_offset += 45

        pygame.draw.line(self.screen, (100,100,100), (ui_x, SCREEN_HEIGHT - 40), (SCREEN_WIDTH-10, SCREEN_HEIGHT - 40), 1)
        self.screen.blit(self.small_font.render(self.message, True, self.message_color), (ui_x, SCREEN_HEIGHT - 30))

        if self.game_over and self.final_stats:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0,0))
            
            # Augmentation de la taille de la boîte pour afficher le détail
            box_w, box_h = 420, 420 
            box_x, box_y = (SCREEN_WIDTH - box_w)//2, (SCREEN_HEIGHT - box_h)//2
            box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            
            pygame.draw.rect(self.screen, (40, 40, 50), box_rect, border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 2, border_radius=10)
            
            title = self.title_font.render("SIMULATION TERMINÉE", True, (255, 255, 255))
            self.screen.blit(title, title.get_rect(center=(box_x + box_w//2, box_y + 40)))
            
            # Récupération des données détaillées
            virt = self.final_stats['virtuosity']
            pol_total = self.final_stats['pollution_total']
            
            p_const = self.final_stats.get('pol_const', 0)
            p_dur = self.final_stats.get('pol_duree', 0)
            p_flood = self.final_stats.get('pol_flood', 0)
            
            score = self.final_stats['score']
            
            # --- AFFICHAGE CALCUL ---
            txt_v = self.timer_font.render(f"Virtuosité Totale : +{virt}", True, (100, 255, 100))
            self.screen.blit(txt_v, txt_v.get_rect(center=(box_x + box_w//2, box_y + 100)))

            txt_p = self.timer_font.render(f"Pollution Totale : -{pol_total}", True, (255, 80, 80))
            self.screen.blit(txt_p, txt_p.get_rect(center=(box_x + box_w//2, box_y + 140)))
            
            detail_str = f"(Constr: -{p_const} | Durée: -{p_dur} | Crue: -{p_flood})"
            txt_detail = self.small_font.render(detail_str, True, (200, 150, 150))
            self.screen.blit(txt_detail, txt_detail.get_rect(center=(box_x + box_w//2, box_y + 165)))
            
            pygame.draw.line(self.screen, (150,150,150), (box_x+50, box_y+190), (box_x+box_w-50, box_y+190), 2)
            
            txt_score = self.title_font.render(f"SCORE FINAL : {score}", True, (255, 215, 0))
            self.screen.blit(txt_score, txt_score.get_rect(center=(box_x + box_w//2, box_y + 240)))
            
            calc_str = "Score = Virtuosité - Pollution"
            txt_calc = self.small_font.render(calc_str, True, (150, 150, 150))
            self.screen.blit(txt_calc, txt_calc.get_rect(center=(box_x + box_w//2, box_y + 270)))

            self.retry_rect = pygame.Rect(box_x + box_w//2 - 170, box_y + 320, 160, 50)
            pygame.draw.rect(self.screen, (50, 150, 50), self.retry_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 255, 100), self.retry_rect, 2, border_radius=8)
            txt_retry = self.font.render("RECOMMENCER", True, (255, 255, 255))
            self.screen.blit(txt_retry, txt_retry.get_rect(center=self.retry_rect.center))

            self.quit_rect = pygame.Rect(box_x + box_w//2 + 10, box_y + 320, 160, 50)
            pygame.draw.rect(self.screen, (150, 50, 50), self.quit_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 100, 100), self.quit_rect, 2, border_radius=8)
            txt_quit = self.font.render("QUITTER", True, (255, 255, 255))
            self.screen.blit(txt_quit, txt_quit.get_rect(center=self.quit_rect.center))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.game_over:
                            mx, my = event.pos
                            if self.retry_rect and self.retry_rect.collidepoint(mx, my):
                                self.reset_game()
                            elif self.quit_rect and self.quit_rect.collidepoint(mx, my):
                                running = False
                        else:
                            mx, my = event.pos
                            if mx < MAP_WIDTH * TILE_SIZE:
                                self.place_building(mx // TILE_SIZE, my // TILE_SIZE)
            self.update_game_logic(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()