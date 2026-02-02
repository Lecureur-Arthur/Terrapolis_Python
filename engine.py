import pygame
import numpy as np
import sys
import os
import random
import math
from datetime import datetime

import network
import settings as cfg
from terrain_data import MapTemplates
from rules_manager import BUILDING_RULES, ADJACENT_MODIFIERS
import map as map_ai

BUILDING_TO_ID = {
    "quarry": 5,
    "sawmill": 6,
    "coal_plant": 7,
    "wind_turbine": 8,
    "nuclear_plant": 9,
    "residence": 10,
}

ID_TO_BUILDING = {v: k for k, v in BUILDING_TO_ID.items()}

class Game:
    def __init__(self):
        pygame.init()
        self._init_display()
        self._init_fonts()
        self._init_assets()
        self._init_io()
        self.reset_game()

        self.network = network.TerrapolisServer(self)
        self.mobile_addr = None

    def _init_display(self):
        # La taille de l'écran est maintenant la somme de la bande AR + la carte + le menu
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        pygame.display.set_caption("City Builder - Terrapolis AR")
        self.clock = pygame.time.Clock()

        # On prépare l'image de la bande latérale AR
        self.qr_sidebar_surface = self._load_ar_marker_image()

    def _load_ar_marker_image(self):
        """Charge l'image du marqueur AR et la redimensionne."""
        target_width = cfg.QR_MARGIN_WIDTH
        target_height = cfg.SCREEN_HEIGHT
        
        # Chemin vers votre image
        image_path = os.path.join("Assets", "image_3.png")

        if os.path.exists(image_path):
            try:
                print(f"Info: Chargement du marqueur AR depuis '{image_path}'...")
                # Chargement et conversion pour optimiser
                raw_image = pygame.image.load(image_path).convert()
                
                # Redimensionnement pour coller parfaitement à la zone prévue
                scaled_surface = pygame.transform.smoothscale(raw_image, (target_width, target_height))
                return scaled_surface
                
            except Exception as e:
                print(f"ERREUR lors du chargement de l'image AR : {e}")
        else:
            print(f"ATTENTION : L'image '{image_path}' est introuvable !")

        # Surface de secours (rouge) si l'image n'est pas trouvée, pour ne pas faire planter le jeu
        fallback = pygame.Surface((target_width, target_height))
        fallback.fill((200, 50, 50))
        font = pygame.font.SysFont("Arial", 20)
        txt = font.render("IMAGE INTROUVABLE", True, (255, 255, 255))
        fallback.blit(txt, (10, target_height // 2))
        return fallback

    def _init_fonts(self):
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

    def _init_assets(self):
        self.building_sprites = {}
        self.ui_icons = {}
        assets_dir = "Assets"
        if not os.path.exists(assets_dir):
            print(f"Info: Dossier '{assets_dir}' introuvable. Mode sans images.")
        else:
            for key, filename in cfg.BUILDING_IMAGES.items():
                path = os.path.join(assets_dir, filename)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        img = pygame.transform.smoothscale(img, (cfg.TILE_SIZE, cfg.TILE_SIZE))
                        self.building_sprites[key] = img
                        icon = pygame.transform.smoothscale(img, (25, 25))
                        self.ui_icons[key] = icon
                    except Exception as e:
                        print(f"Erreur image {filename}: {e}")

    def _init_io(self):
        self.ai_engine = map_ai.TerrapolisAI()
        if os.path.exists("action.txt"):
            try: os.remove("action.txt")
            except: pass

    # --- INITIALISATION ET RESET ---

    def reset_game(self):
        self.resources = {"wood": 0, "stones": 0, "virtuosity": 0}
        self.building_counts = {k: 0 for k in BUILDING_RULES.keys()}
        self.destroyed_counts = {k: 0 for k in BUILDING_RULES.keys()}
        self.forests_destroyed_count = 0
        self.selected_building = None
        self.retry_rect = None
        self.quit_rect = None
        self.ai_btn_rect = None
        self.popup_active = False
        self.popup_data = {}
        self.popup_rect_ok = None
        self.popup_rect_cancel = None
        self.last_production_time = pygame.time.get_ticks()
        self.last_matrix_save_time = pygame.time.get_ticks()
        self.last_action_check_time = pygame.time.get_ticks()
        self.last_action_file_date = ""
        self.time_left = cfg.GAME_DURATION
        self.game_over = False
        self.final_stats = {}
        self.ai_suggestion = None
        self.ai_suggestion_end_time = 0
        self.flooded_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=bool)
        self.max_floods_game = random.randint(0, 2)
        self.floods_occurred = 0
        self.next_flood_time = random.randint(cfg.FLOOD_MIN_INTERVAL, cfg.FLOOD_MAX_INTERVAL)
        self.flood_timer = 0
        self.flood_clear_timer = 0
        self.flood_pollution_total = 0
        self.river_risk_factor = 1.0
        self.message = "Bienvenue."
        self.message_color = cfg.COLORS["text"]
        self.map_data = self._generate_map()
        self.buildings_grid = [[None for _ in range(cfg.MAP_WIDTH)] for _ in range(cfg.MAP_HEIGHT)]
        self.tile_resources = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self.building_timestamps = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self.pol_build_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self.pol_duration_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self.virt_build_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self.virt_duration_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=float)
        self._init_tile_resources()

    def _generate_map(self):
        game_map = np.full((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), "void", dtype=object)
        game_map[MapTemplates.plain == 1] = "plain"
        game_map[MapTemplates.forest == 1] = "forest"
        game_map[MapTemplates.mountain == 1] = "mountain"
        game_map[MapTemplates.river == 1] = "river"
        return game_map

    def _init_tile_resources(self):
        terrain_values = {}
        for b_key, rules in BUILDING_RULES.items():
            prod = rules.get("production", {})
            yield_map = prod.get("tile_yield", {})
            for terrain_type, amount in yield_map.items():
                terrain_values[terrain_type] = float(amount)
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                terrain = self.map_data[y][x]
                if terrain in terrain_values:
                    self.tile_resources[y][x] = terrain_values[terrain]

    # --- LOGIQUE ---

    def update_game_logic(self, dt_seconds):
        if dt_seconds == 0: return

        self._process_network_commands()

        if not self.game_over:
            self.time_left -= dt_seconds
            if self.time_left <= 0:
                self._end_game()
        if self.game_over: return
        now_ms = pygame.time.get_ticks()
        self._handle_flood_timers(dt_seconds)
        if now_ms - self.last_action_check_time > (cfg.ACTION_FILE_CHECK_INTERVAL * 1000):
            self._check_external_actions()
            self.last_action_check_time = now_ms
        if now_ms - self.last_matrix_save_time > (cfg.MATRIX_SAVE_INTERVAL * 1000):
            self.save_matrix_snapshot()
            self.last_matrix_save_time = now_ms
        if now_ms - self.last_production_time > 1000:
            self._process_production_cycle()
            self.last_production_time = now_ms
        self._process_continuous_effects(dt_seconds, now_ms)

    def _end_game(self):
        self.time_left = 0
        self.game_over = True
        
        # Calcul des scores (Code existant)
        virt = self.resources["virtuosity"]
        p_build = np.sum(self.pol_build_grid)
        p_dur = np.sum(self.pol_duration_grid)
        p_flood = self.flood_pollution_total
        total_poll = p_build + p_dur + p_flood
        score = virt - total_poll
        
        self.final_stats = {
            "virtuosity": int(virt),
            "pollution_total": int(total_poll),
            "pol_const": int(p_build),
            "pol_duree": int(p_dur),
            "pol_flood": int(p_flood),
            "score": int(score)
        }

        # --- AJOUT : ENVOI DU POPUP DE FIN AU MOBILE ---
        # On prépare un message concis pour l'écran du téléphone
        msg_mobile = f"Score Final : {int(score)}\n"
        msg_mobile += f"Virtuosité : {int(virt)}\n"
        msg_mobile += f"Pollution : -{int(total_poll)}"
        
        # On utilise "CONFIRM" pour avoir le titre en vert sur le mobile
        self.trigger_popup("CONFIRM", "SIMULATION TERMINÉE", msg_mobile)
        # -----------------------------------------------

        self.message = f"PARTIE TERMINÉE ! Score: {int(score)}"
        self.message_color = (255, 215, 0)
        self.save_game_results()

    def _handle_flood_timers(self, dt):
        if self.floods_occurred < self.max_floods_game:
            self.river_risk_factor = self._calculate_risk_factor()
            self.flood_timer += dt * self.river_risk_factor
            if self.flood_timer >= self.next_flood_time:
                self.trigger_flood()
                self.flood_timer = 0
                self.next_flood_time = random.randint(cfg.FLOOD_MIN_INTERVAL, cfg.FLOOD_MAX_INTERVAL)
        if self.flood_clear_timer > 0:
            self.flood_clear_timer -= dt
            if self.flood_clear_timer <= 0:
                # L'eau se retire
                self.flooded_grid.fill(False) 
                self.message = "L'eau se retire. La terre sèche."
                
                # --- AJOUT : ENVOYER LA CARTE PROPRE ---
                if self.mobile_address:
                    print(f"[RESEAU] Fin inondation -> Mise à jour Mobile")
                    self._send_map_to_mobile(self.mobile_address)

    def _calculate_risk_factor(self):
        count = 0
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                if self.buildings_grid[y][x]:
                    if self.check_adjacency(x, y, "river", is_terrain=True):
                        count += 1
        return 1.0 + (count * 0.15)
    
    def _process_network_commands(self):
        """Lit la file d'attente du réseau et exécute les actions."""
        try:
            while not self.network.command_queue.empty():
                message, addr = self.network.command_queue.get_nowait()

                if message == "READY":
                    print(f"[JEU] Mobile connecté depuis {addr}")
                    self.mobile_address = addr
                    self._send_map_to_mobile(addr)

                if message.startswith("BUILD"):
                    # Format : BUILD,index,typeID
                    parts = message.split(",")
                    if len(parts) == 3:
                        idx = int(parts[1])
                        b_id = int(parts[2])
                        self._handle_mobile_build(idx, b_id, addr)

                if message.startswith("DESTROY"):
                    try:
                        _, idx_str = message.split(",")
                        tile_index = int(idx_str)

                        # 1. On utilise EXACTEMENT la même logique que pour le BUILD
                        # La grille mobile est remplie ligne par ligne.
                        # La largeur de la grille mobile correspond à la HAUTEUR de la grille PC (car rotation 90°)
                        
                        mobile_width = cfg.MAP_HEIGHT  # C'est la largeur de la grille sur le téléphone (10 par défaut)
                        
                        u_row = tile_index // mobile_width
                        u_col = tile_index % mobile_width
                        
                        # 2. Conversion coordonnées Mobile -> PC (Rotation k=1 inversée)
                        # Cette formule doit être identique à celle de _handle_mobile_build
                        py_row = u_col 
                        py_col = (cfg.MAP_WIDTH - 1) - u_row
                        
                        print(f"[DEBUG DESTROY] Index {tile_index} (Mob: {u_col},{u_row}) -> PC ({py_col}, {py_row})")

                        # 3. Vérification et Destruction
                        if 0 <= py_col < cfg.MAP_WIDTH and 0 <= py_row < cfg.MAP_HEIGHT:
                            
                            # On récupère le bâtiment à cet endroit précis
                            b_name = self.buildings_grid[py_row][py_col]
                            
                            if b_name:
                                print(f"[SUCCÈS] Destruction de {b_name} en ({py_col}, {py_row})")
                                
                                # Suppression
                                self.buildings_grid[py_row][py_col] = None
                                
                                # (Optionnel) Nettoyage pollution locale du bâtiment
                                self.pol_build_grid[py_row][py_col] = 0
                                
                                # (Optionnel) Si le sol n'est pas spécial (rivière/montagne), on remet de la plaine
                                # pour effacer la trace visuelle du bâtiment
                                current_terrain = self.map_data[py_row][py_col]
                                if current_terrain not in ["river", "mountain", "forest"]:
                                     self.map_data[py_row][py_col] = "plain"

                                # Mise à jour immédiate du mobile
                                self._send_map_to_mobile(addr)
                                self.trigger_popup("CONFIRM", "DESTRUCTION", f"Bâtiment détruit !")
                            else:
                                print(f"[ECHEC] Case vide sur le serveur en ({py_col}, {py_row}).")
                                # Astuce Debug : On affiche ce qu'il y a autour pour comprendre le décalage
                                self.trigger_popup("ERROR", "ERREUR", "Le serveur ne voit pas de bâtiment ici.")
                        else:
                            print(f"[ERREUR] Hors limites : ({py_col}, {py_row})")

                    except Exception as e:
                        print(f"[ERREUR] Exception Destruction : {e}")           

        except Exception as e:
            print(f"[JEU] Erreur traitement commande réseau : {e}")
            pass

    def _process_production_cycle(self):
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                b_name = self.buildings_grid[y][x]
                if not b_name or self.flooded_grid[y][x]: continue
                rules = BUILDING_RULES[b_name]
                prod = rules.get("production")
                if prod and prod["amount"] > 0 and prod["resource"]:
                    needed_terrain = rules.get("needs_adj_terrain")
                    if needed_terrain:
                        self._extract_resource_from_neighbors(x, y, prod, needed_terrain)
                    else:
                        self.resources[prod["resource"]] += prod["amount"]

    def _extract_resource_from_neighbors(self, x, y, prod, needed_terrain):
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                if self.map_data[ny][nx] in needed_terrain:
                    if self.tile_resources[ny][nx] > 0:
                        amount = prod["amount"]
                        self.tile_resources[ny][nx] -= amount
                        self.resources[prod["resource"]] += amount
                        if self.tile_resources[ny][nx] <= 0:
                            self._destroy_terrain_resource(nx, ny)
                        return

    def _destroy_terrain_resource(self, x, y):
        if self.map_data[y][x] == "forest":
            self.forests_destroyed_count += 1
            count = self.forests_destroyed_count
            loss_pct = 0.01 if count <= 10 else 0.02 if count <= 15 else 0.05 if count <= 25 else 0.10 if count <= 30 else 0.20
            amount_lost = int(self.resources["virtuosity"] * loss_pct)
            self.resources["virtuosity"] = max(0, self.resources["virtuosity"] - amount_lost)
            self.message = f"Forêt détruite ! -{amount_lost} Virtuosité ({int(loss_pct*100)}%)"
            self.message_color = (255, 50, 50)
            
        self.tile_resources[y][x] = 0
        self.map_data[y][x] = "plain"  # <--- C'est ici que la forêt disparait visuellement

        # --- AJOUT À FAIRE ICI ---
        # On prévient le mobile immédiatement que le terrain a changé
        if self.mobile_address:
            # On utilise send_to directement pour éviter d'attendre
            self._send_map_to_mobile(self.mobile_address)
        # -------------------------

    def _process_continuous_effects(self, dt, now_ms):
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                b_name = self.buildings_grid[y][x]
                if not b_name: continue
                rules = BUILDING_RULES[b_name]
                is_working = True
                if b_name in ["sawmill", "quarry"]:
                    needed = rules.get("needs_adj_terrain")
                    if needed and not self._has_adjacent_resource(x, y, needed):
                        is_working = False
                if not is_working: continue
                virt_gain = rules.get("virtuosity_per_sec", 0) * dt
                if virt_gain > 0:
                    self.resources["virtuosity"] += virt_gain
                    self.virt_duration_grid[y][x] += virt_gain
                emission = rules.get("emits_per_sec", 0) * dt
                if emission > 0:
                    self.pol_duration_grid[y][x] += emission
                    self._spread_pollution(x, y, rules, emission, now_ms)
                self._process_river_pollution(x, y, rules, dt, now_ms)

    def _has_adjacent_resource(self, x, y, terrain_list):
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                if self.map_data[ny][nx] in terrain_list and self.tile_resources[ny][nx] > 0:
                    return True
        return False

    def _spread_pollution(self, x, y, rules, emission, now_ms):
        age = (now_ms / 1000.0) - self.building_timestamps[y][x]
        spread_delay = rules.get("pollution_spread_after_sec", 0)
        if rules.get("spreads_pollution") and age >= spread_delay:
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in deltas:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                    neighbor = self.buildings_grid[ny][nx]
                    mod = ADJACENT_MODIFIERS.get(neighbor, 1.0) if neighbor else 1.0
                    self.pol_duration_grid[ny][nx] += (emission * 0.5) * mod

    def _process_river_pollution(self, x, y, rules, dt, now_ms):
        target_amount = rules.get("river_pollution_amount", 0)
        if target_amount <= 0: return
        if self.check_adjacency(x, y, "river", is_terrain=True):
            delay = rules.get("pollutes_river_after_sec", 0)
            age = (now_ms / 1000.0) - self.building_timestamps[y][x]
            if delay > 0 and age < delay: return
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            fill_rate = target_amount / max(1, delay) if delay > 0 else target_amount
            for dx, dy in deltas:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                    if self.map_data[ny][nx] == "river":
                        if delay > 0:
                            current_val = self.pol_duration_grid[ny][nx]
                            if current_val < target_amount:
                                addition = fill_rate * dt
                                self.pol_duration_grid[ny][nx] = min(target_amount, current_val + addition)
                        else:
                            self.pol_duration_grid[ny][nx] += target_amount * dt

    # --- ACTIONS ---

    def place_building(self, x, y):
        if self.game_over or self.popup_active or not self.selected_building: return
        if self.selected_building == "demolish":
            if self.buildings_grid[y][x]:
                self.execute_action(x, y, self.buildings_grid[y][x], -1, is_flood=False)
            else:
                self.message = "Rien à détruire ici."
            return
        if self.buildings_grid[y][x]:
            self.trigger_popup("error", "IMPOSSIBLE", "Cet emplacement est déjà occupé.")
            return
        if self.flooded_grid[y][x]:
            self.trigger_popup("error", "IMPOSSIBLE", "Terrain inondé ou boueux.")
            return
        rules = BUILDING_RULES.get(self.selected_building)
        if not self._check_building_constraints(x, y, rules): return
        if not self._check_resources_cost(rules): return
        viability = random.randint(0, 100)
        warning = self._get_pollution_warning(x, y)
        msg = f"VIABILITÉ DU SITE : {viability}%\n"
        if warning: msg += f"\n--- ATTENTION ---\n{warning}\n"
        msg += "\nConfirmer la construction ?"
        self.trigger_popup("confirm", "ANALYSE DU TERRAIN", msg, {"x": x, "y": y, "building": self.selected_building})

    def _check_building_constraints(self, x, y, rules):
        terrain = self.map_data[y][x]
        if terrain in rules.get("forbidden", []):
            self.trigger_popup("error", "EMPLACEMENT INVALIDE", f"Interdit sur : {terrain}.")
            return False
        req_adj = rules.get("requires_adj_terrain")
        if req_adj and not self.check_adjacency(x, y, req_adj, is_terrain=True):
            self.trigger_popup("error", "EMPLACEMENT INVALIDE", f"Doit toucher : {req_adj}")
            return False
        needs_adj = rules.get("needs_adj_terrain")
        if needs_adj and not self.check_adjacency(x, y, needs_adj, is_terrain=True):
            self.trigger_popup("error", "EMPLACEMENT INVALIDE", f"Doit toucher : {needs_adj}")
            return False
        return True

    def _check_resources_cost(self, rules):
        cost_w = rules["cost"].get("wood", 0)
        cost_s = rules["cost"].get("stones", 0)
        if self.selected_building in ["sawmill", "quarry"] and self.building_counts[self.selected_building] == 0:
            if self.resources["wood"] < cost_w or self.resources["stones"] < cost_s:
                return True
        if self.resources["wood"] < cost_w or self.resources["stones"] < cost_s:
            missing_w = max(0, cost_w - self.resources["wood"])
            missing_s = max(0, cost_s - self.resources["stones"])
            msg = f"Manque :\n• {int(missing_w)} Bois\n• {int(missing_s)} Pierre"
            self.trigger_popup("error", "RESSOURCES INSUFFISANTES", msg)
            return False
        return True

    def execute_action(self, x, y, b_key, action_type, is_flood=False):
        if self.game_over: return
        if action_type == 0: return
        if action_type == -1:
            current_b = self.buildings_grid[y][x]
            if current_b and (current_b == b_key or b_key == "ANY"):
                if not is_flood:
                    b_rules = BUILDING_RULES[current_b]
                    virt_lost = b_rules.get("virtuosity_loss_on_destroy", 0)
                    self.resources["virtuosity"] = max(0, self.resources["virtuosity"] - virt_lost)
                    self.virt_build_grid[y][x] = 0
                    self.message = f"Détruit ! -{virt_lost} Virtuosité (Pollution persistante)."
                    self.message_color = (255, 100, 100)
                self.buildings_grid[y][x] = None
                self.building_counts[current_b] -= 1
                self.destroyed_counts[current_b] += 1
            return
        if action_type == 1:
            rules = BUILDING_RULES.get(b_key)
            if not rules: return
            cost_wood = rules["cost"].get("wood", 0)
            cost_stones = rules["cost"].get("stones", 0)
            is_free = False
            if b_key in ["sawmill", "quarry"]:
                if self.building_counts[b_key] == 0:
                    if self.resources["wood"] < cost_wood or self.resources["stones"] < cost_stones:
                        is_free = True
            if is_free: cost_wood, cost_stones = 0, 0
            self.resources["wood"] -= cost_wood
            self.resources["stones"] -= cost_stones
            self.buildings_grid[y][x] = b_key
            self.building_counts[b_key] += 1
            self.building_timestamps[y][x] = pygame.time.get_ticks() / 1000.0
            self.pol_build_grid[y][x] += rules.get("pollution_on_build", 0)
            v_val = rules.get("virtuosity_on_build", 0)
            self.virt_build_grid[y][x] += v_val
            self.resources["virtuosity"] += v_val
            suffix = " (Secours)" if is_free else ""
            self.message = f"{rules['name']}{suffix} construit !"
            self.message_color = (80, 255, 80)

    def trigger_flood(self):
        candidates = set()
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                if self.map_data[y][x] == "river":
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                            if self.map_data[ny][nx] not in ["river", "void"]:
                                candidates.add((nx, ny))
        if not candidates: return
        count = len(candidates)
        target = random.randint(max(1, count // 3), max(2, int(count * 2 / 3)))
        flooded_selection = set()
        cand_list = list(candidates)
        while len(flooded_selection) < target and cand_list:
            start = random.choice(cand_list)
            frontier = [start]
            while frontier and len(flooded_selection) < target:
                curr = frontier.pop(random.randint(0, len(frontier)-1))
                if curr in flooded_selection: continue
                flooded_selection.add(curr)
                if curr in cand_list: cand_list.remove(curr)
                cx, cy = curr
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in candidates and neighbor not in flooded_selection and neighbor not in frontier:
                        frontier.append(neighbor)
        destroyed = 0
        poll_increase = 0
        for fx, fy in flooded_selection:
            self.flooded_grid[fy][fx] = True
            b_name = self.buildings_grid[fy][fx]
            if b_name:
                rules = BUILDING_RULES[b_name].get("on_flood", {})
                poll_increase += rules.get("floodScoreIncrease", 0)
                if rules.get("destroyed", False):
                    self.execute_action(fx, fy, b_name, -1, is_flood=True)
                    destroyed += 1
        self.flood_pollution_total += poll_increase
        self.message = f"CRUE ! {len(flooded_selection)} zones inondées. {destroyed} détruits."
        self.message_color = (255, 100, 100)
        self.flood_clear_timer = cfg.FLOOD_DURATION
        self.floods_occurred += 1

        if self.mobile_address:
            print(f"[RESEAU] Envoi de la carte INONDÉE vers {self.mobile_address}")
            self._send_map_to_mobile(self.mobile_address)
            
            # Optionnel : Envoyer aussi un Popup d'alerte
            msg = f"Attention !\n{len(flooded_selection)} zones touchées\n{destroyed} bâtiments détruits"
            self.trigger_popup("ERROR", "INONDATION !", msg)

    def check_adjacency(self, x, y, target, is_terrain=True):
        targets = [target] if isinstance(target, str) else target
        if not targets: return False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                val = self.map_data[ny][nx] if is_terrain else self.buildings_grid[ny][nx]
                if val in targets: return True
        return False

    def _get_pollution_warning(self, x, y):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cfg.MAP_WIDTH and 0 <= ny < cfg.MAP_HEIGHT:
                neighbor = self.buildings_grid[ny][nx]
                if neighbor and ADJACENT_MODIFIERS.get(neighbor, 1.0) > 1.0:
                    return f"Zone à risque : {BUILDING_RULES[neighbor]['name']} (x{ADJACENT_MODIFIERS[neighbor]})"
        return None

    def trigger_popup(self, type_popup, title, message, action_data=None):
        """
        Envoie le popup au mobile via UDP.
        Version sécurisée : ne plante pas si mobile_address n'est pas défini.
        """
        # Nettoyage du message (remplace les retours à la ligne par |)
        clean_message = message.replace("\n", "|")
        
        # Construction du paquet
        packet = f"POPUP,{type_popup.upper()},{title},{clean_message}"
        
        # Récupération sécurisée de l'adresse (évite le crash AttributeError)
        addr = getattr(self, 'mobile_address', None)
        print(f"[DEBUG] Adresse mobile pour popup : {addr}")

        if addr:
            print(f"[RESEAU] Envoi Popup vers {addr} : {packet}")
            self.network.send_to(packet, addr)
        else:
            print(f"[INFO] Popup (Pas de mobile connecté) : {title} - {message}")

        # Désactive l'affichage local Pygame
        self.popup_active = False 
        self.popup_data = {}

    def _check_external_actions(self):
        filename = "action.txt"
        if not os.path.exists(filename): return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines: return
            file_date = lines[0].strip()
            if file_date == self.last_action_file_date: return
            self.last_action_file_date = file_date
            self.ai_suggestion = None
            curr_b, row = None, 0
            for line in lines[1:]:
                line = line.strip()
                if not line: continue
                if line.startswith("===") and line.endswith("==="):
                    b_name = line.replace("=", "").strip()
                    if b_name in BUILDING_RULES:
                        curr_b, row = b_name, 0
                    continue
                if curr_b and row < cfg.MAP_HEIGHT:
                    parts = line.split()
                    if len(parts) >= cfg.MAP_WIDTH:
                        for col, val_str in enumerate(parts[:cfg.MAP_WIDTH]):
                            try:
                                val = int(val_str)
                                if val != 0:
                                    self.ai_suggestion = {'x': col, 'y': row, 'building': curr_b, 'action': val}
                                    self.ai_suggestion_end_time = pygame.time.get_ticks() + (cfg.AI_SUGGESTION_DURATION * 1000)
                                    act_str = "construire" if val > 0 else "détruire"
                                    self.message = f"IA Suggère : {act_str} {BUILDING_RULES[curr_b]['name']}"
                                    self.message_color = (0, 255, 255) if val > 0 else (255, 100, 100)
                            except: pass
                        row += 1
        except Exception as e:
            print(f"Erreur lecture action.txt : {e}")

    def save_matrix_snapshot(self):
        folder = "Batiment_Maps"
        if not os.path.exists(folder): os.makedirs(folder)
        filename = f"{folder}/matrix_state.txt"
        content = f"Snapshot Date: {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}\n\n"
        for t in ['mountain', 'plain', 'forest', 'river']:
            content += f"=== {t} ===\n"
            for y in range(cfg.MAP_HEIGHT):
                content += " ".join(["1" if self.map_data[y][x] == t else "0" for x in range(cfg.MAP_WIDTH)]) + "\n"
            content += "\n"
        content += f"=== FLOOD ===\n"
        for y in range(cfg.MAP_HEIGHT):
            content += " ".join(["1" if self.flooded_grid[y][x] else "0" for x in range(cfg.MAP_WIDTH)]) + "\n"
        content += "\n"
        for b in ['sawmill', 'quarry', 'coal_plant', 'wind_turbine', 'nuclear_plant', 'residence']:
            content += f"=== {b} ===\n"
            for y in range(cfg.MAP_HEIGHT):
                content += " ".join(["1" if self.buildings_grid[y][x] == b else "0" for x in range(cfg.MAP_WIDTH)]) + "\n"
            content += "\n"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e: print(f"Erreur snapshot : {e}")

    def save_game_results(self):
        folder = "Terrapolis_Save"
        if not os.path.exists(folder): os.makedirs(folder)
        filename = f"{folder}/Save_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        content = f"=== RAPPORT DE FIN DE PARTIE - TERRAPOLIS ===\n"
        content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        content += f"SCORE FINAL : {self.final_stats['score']}\n"
        content += f"---------------------------------------\n"
        content += f"Virtuosité      : {self.final_stats['virtuosity']}\n"
        content += f"Pollution Totale: {self.final_stats['pollution_total']}\n"
        content += f"  > Construction: {self.final_stats['pol_const']}\n"
        content += f"  > Durée       : {self.final_stats['pol_duree']}\n"
        content += f"  > Inondation  : {self.final_stats['pol_flood']}\n\n"
        content += f"BÂTIMENTS (Construits / Détruits):\n"
        for k, v in self.building_counts.items():
            content += f"- {BUILDING_RULES[k]['name']:<18} : {v} / {self.destroyed_counts[k]}\n"
        try:
            with open(filename, "w", encoding="utf-8") as f: f.write(content)
            self.message = f"Sauvegardé : {os.path.basename(filename)}"
        except Exception as e: print(f"Erreur save : {e}")

    # --- DRAWING ---

    def draw(self):
        self.screen.fill(cfg.COLORS["ui_bg"])
        
        # 1. On dessine le marqueur AR sur la bande de gauche
        self.screen.blit(self.qr_sidebar_surface, (0, 0))
        
        # 2. On dessine la carte (qui est décalée)
        self._draw_map_area()
        
        # 3. L'interface
        self._draw_sidebar_ui()
        self._draw_popups_and_overlays()

    def _draw_map_area(self):
        # On applique le décalage pour ne pas dessiner sur le marqueur AR
        off_x = cfg.MAP_OFFSET_X
        off_y = cfg.MAP_OFFSET_Y

        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                rect = pygame.Rect(off_x + x * cfg.TILE_SIZE, off_y + y * cfg.TILE_SIZE, cfg.TILE_SIZE, cfg.TILE_SIZE)
                self._draw_tile_base(x, y, rect)
                self._draw_tile_resources(x, y, rect)
                if self.buildings_grid[y][x]:
                    self._draw_building(x, y, rect, self.buildings_grid[y][x])
        self._draw_selection_ghost()
        self._draw_ai_suggestion()

    def _draw_tile_base(self, x, y, rect):
        if self.flooded_grid[y][x]:
            color = cfg.COLORS["mud"]
            if self.flood_clear_timer <= cfg.FLOOD_FADE_DURATION:
                t = max(0.0, min(1.0, 1.0 - (self.flood_clear_timer / cfg.FLOOD_FADE_DURATION)))
                base = cfg.COLORS.get(self.map_data[y][x], (0,0,0))
                r = color[0] + (base[0] - color[0]) * t
                g = color[1] + (base[1] - color[1]) * t
                b = color[2] + (base[2] - color[2]) * t
                color = (int(r), int(g), int(b))
            pygame.draw.rect(self.screen, color, rect)
        else:
            pygame.draw.rect(self.screen, cfg.COLORS.get(self.map_data[y][x], (0,0,0)), rect)
        pygame.draw.rect(self.screen, (30,30,30), rect, 1)

    def _draw_tile_resources(self, x, y, rect):
        if self.map_data[y][x] in ["forest", "mountain"] and not self.flooded_grid[y][x]:
            qty = int(self.tile_resources[y][x])
            if qty > 0:
                is_forest = self.map_data[y][x] == "forest"
                fg = (180, 255, 180) if is_forest else (220, 220, 220)
                bg = (20, 60, 20) if is_forest else (40, 40, 40)
                surf = self.score_font.render(str(qty), True, fg)
                r_bg = surf.get_rect(topleft=(rect.left+5, rect.top+5)).inflate(8, 4)
                pygame.draw.rect(self.screen, bg, r_bg, border_radius=4)
                pygame.draw.rect(self.screen, (200,200,200), r_bg, 1, border_radius=4)
                self.screen.blit(surf, r_bg.move(4, 2))

    def _draw_building(self, x, y, rect, b_key):
        b_rect = rect.inflate(-4, -4)
        sprite = self.building_sprites.get(b_key)
        if sprite:
            self.screen.blit(sprite, rect)
            pygame.draw.rect(self.screen, (0,0,0), b_rect, 1)
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), b_rect)
            pygame.draw.rect(self.screen, (0,0,0), b_rect, 2)
            txt = self.icon_font.render("?", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def _draw_selection_ghost(self):
        if self.selected_building and self.selected_building != "demolish" and not self.popup_active:
            mx, my = pygame.mouse.get_pos()
            # Calcul avec le décalage de la carte
            gx = (mx - cfg.MAP_OFFSET_X) // cfg.TILE_SIZE
            gy = (my - cfg.MAP_OFFSET_Y) // cfg.TILE_SIZE
            if 0 <= gx < cfg.MAP_WIDTH and 0 <= gy < cfg.MAP_HEIGHT:
                # Dessin avec le décalage
                r = pygame.Rect(cfg.MAP_OFFSET_X + gx*cfg.TILE_SIZE, cfg.MAP_OFFSET_Y + gy*cfg.TILE_SIZE, cfg.TILE_SIZE, cfg.TILE_SIZE)
                sprite = self.building_sprites.get(self.selected_building)
                if sprite:
                    ghost = sprite.copy()
                    ghost.set_alpha(128)
                    self.screen.blit(ghost, r)
                else:
                    pygame.draw.rect(self.screen, (255, 255, 255), r, 2)

    def _draw_ai_suggestion(self):
        if not self.ai_suggestion: return
        if pygame.time.get_ticks() >= self.ai_suggestion_end_time:
            self.ai_suggestion = None; self.message = "IA : En attente..."; return
        sx, sy = self.ai_suggestion['x'], self.ai_suggestion['y']
        b_key = self.ai_suggestion['building']
        action = self.ai_suggestion['action']
        # Dessin avec le décalage
        rect = pygame.Rect(cfg.MAP_OFFSET_X + sx * cfg.TILE_SIZE, cfg.MAP_OFFSET_Y + sy * cfg.TILE_SIZE, cfg.TILE_SIZE, cfg.TILE_SIZE)
        col = (0, 255, 255) if action > 0 else (255, 50, 50)
        sprite = self.building_sprites.get(b_key)
        if sprite:
            ghost = sprite.copy()
            ghost.set_alpha(180)
            self.screen.blit(ghost, rect)
        else:
            txt = self.icon_font.render("?", True, col)
            self.screen.blit(txt, txt.get_rect(center=rect.center))
        pygame.draw.rect(self.screen, col, rect, 4)
        txt = f"{'CONSEIL' if action > 0 else 'DÉTRUIRE'}: {BUILDING_RULES[b_key]['name']}"
        lbl = self.tiny_font.render(txt, True, (255,255,255))
        r_lbl = lbl.get_rect(midbottom=(rect.centerx, rect.top-5)).inflate(8,4)
        pygame.draw.rect(self.screen, (0,0,0), r_lbl, border_radius=4)
        pygame.draw.rect(self.screen, col, r_lbl, 1, border_radius=4)
        self.screen.blit(lbl, lbl.get_rect(center=r_lbl.center))

    def _draw_sidebar_ui(self):
        # Position du menu = Marge QR + Largeur Carte + Petite marge
        ui_x = cfg.QR_MARGIN_WIDTH + (cfg.MAP_WIDTH * cfg.TILE_SIZE) + 10
        y = 10
        mins, secs = divmod(int(self.time_left), 60)
        col = (255, 50, 50) if self.time_left < 60 else (255, 255, 255)
        self.screen.blit(self.timer_font.render(f"TEMPS RESTANT: {mins:02}:{secs:02}", True, col), (ui_x, y))
        y += 30
        if self.floods_occurred < self.max_floods_game:
            f_in = int(self.next_flood_time - self.flood_timer)
            col_f = (100, 200, 255) if f_in > 10 else (255, 50, 50)
            self.screen.blit(self.small_font.render(f"Prochaine crue : {f_in}s", True, col_f), (ui_x, y))
            risk = self.river_risk_factor
            col_r = (100, 255, 100) if risk <= 1.5 else (255, 165, 0) if risk <= 2.0 else (255, 50, 50)
            self.screen.blit(self.small_font.render(f"Risque Crue : x{risk:.1f}", True, col_r), (ui_x, y+15))
            y += 35
        else:
            self.screen.blit(self.small_font.render("Aucune crue prévue", True, (100, 255, 100)), (ui_x, y))
            y += 20
        lbls = [
            (f"POL CONSTR: {int(np.sum(self.pol_build_grid))}", (255, 200, 50)),
            (f"POL DUREE:  {int(np.sum(self.pol_duration_grid))}", (255, 80, 80)),
            (f"POL CRUE:   {int(self.flood_pollution_total)}", (200, 100, 255))
        ]
        for txt, c in lbls:
            self.screen.blit(self.font.render(txt, True, c), (ui_x, y))
            y += 20
        y += 10
        noms_fr = {
            "wood": "Bois",
            "stones": "Pierre",
            "virtuosity": "Virtuosité"
        }
        for r, v in self.resources.items():
            c = (100, 255, 200) if r == "virtuosity" else cfg.COLORS["text"]
            nom_affiche = noms_fr.get(r, r.capitalize())
            self.screen.blit(self.font.render(f"{nom_affiche}: {int(v)}", True, c), (ui_x, y))
            y += 20
        y += 10
        pygame.draw.line(self.screen, (100,100,100), (ui_x, y), (cfg.SCREEN_WIDTH-10, y), 1)
        y += 15
        self.ai_btn_rect = pygame.Rect(ui_x, y, cfg.SIDEBAR_WIDTH-20, 35)
        m_pos = pygame.mouse.get_pos()
        bg_ai = (50, 100, 150) if self.ai_btn_rect.collidepoint(m_pos) else (40, 80, 120)
        pygame.draw.rect(self.screen, bg_ai, self.ai_btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, (100, 200, 255), self.ai_btn_rect, 2, border_radius=6)
        t_ai = self.font.render("IA : CONSEILLER", True, (255, 255, 255))
        self.screen.blit(t_ai, t_ai.get_rect(center=self.ai_btn_rect.center))
        y += 45
        demolish_rect = pygame.Rect(ui_x, y, cfg.SIDEBAR_WIDTH-20, 40)
        is_dem = (self.selected_building == "demolish")
        bg_dem = (100, 40, 40) if is_dem else (70, 40, 40) if demolish_rect.collidepoint(m_pos) else (50, 30, 30)
        pygame.draw.rect(self.screen, bg_dem, demolish_rect)
        if is_dem: pygame.draw.rect(self.screen, (255, 80, 80), demolish_rect, 2)
        self.screen.blit(self.font.render("DÉMOLIR", True, (255, 100, 100)), (ui_x + 40, y + 10))
        try: self.screen.blit(self.icon_font.render("💣", True, (255, 100, 100)), (ui_x + 5, y - 2))
        except: pass
        if pygame.mouse.get_pressed()[0] and demolish_rect.collidepoint(m_pos) and not self.popup_active:
            self.selected_building = "demolish"
            self.message = "Mode Destruction actif"
            self.message_color = (255, 100, 100)
        y += 50
        for k, v in BUILDING_RULES.items():
            r_btn = pygame.Rect(ui_x, y, cfg.SIDEBAR_WIDTH-20, 40)
            if self.selected_building == k:
                pygame.draw.rect(self.screen, (60,60,80), r_btn)
                pygame.draw.rect(self.screen, cfg.COLORS["highlight"], r_btn, 2)
            elif r_btn.collidepoint(m_pos):
                pygame.draw.rect(self.screen, (50,50,60), r_btn)
            icon_mini = self.ui_icons.get(k)
            if icon_mini:
                r_icon = icon_mini.get_rect(topleft=(ui_x+5, y+10))
                self.screen.blit(icon_mini, r_icon)
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), (ui_x+5, y+10, 25, 25))
            self.screen.blit(self.font.render(v['name'], True, cfg.COLORS["text"]), (ui_x + 35, y+2))
            cw, cs = v['cost'].get('wood',0), v['cost'].get('stones',0)
            is_free = (k in ["sawmill", "quarry"] and self.building_counts[k] == 0 and (self.resources["wood"] < cw or self.resources["stones"] < cs))
            cost_str = "Gratuit (Secours)" if is_free else f"Bois:{cw}  Pierre:{cs}"
            self.screen.blit(self.small_font.render(cost_str, True, (150, 255, 150) if is_free else (180,180,180)), (ui_x+35, y+20))
            if pygame.mouse.get_pressed()[0] and r_btn.collidepoint(m_pos) and not self.popup_active:
                self.selected_building = k
                self.message = f"Mode Construction : {v['name']}"
                self.message_color = cfg.COLORS["text"]
            y += 45
        pygame.draw.line(self.screen, (100,100,100), (ui_x, cfg.SCREEN_HEIGHT-40), (cfg.SCREEN_WIDTH-10, cfg.SCREEN_HEIGHT-40), 1)
        self.screen.blit(self.small_font.render(self.message, True, self.message_color), (ui_x, cfg.SCREEN_HEIGHT-30))

    def _draw_popups_and_overlays(self):
        if self.game_over:
            s = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, (0,0))
            cx, cy = cfg.SCREEN_WIDTH//2, cfg.SCREEN_HEIGHT//2
            box = pygame.Rect(0, 0, 420, 420); box.center = (cx, cy)
            pygame.draw.rect(self.screen, (40, 40, 50), box, border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), box, 2, border_radius=10)
            def center_text(txt, font, color, dy):
                ts = font.render(txt, True, color)
                self.screen.blit(ts, ts.get_rect(center=(cx, cy - 210 + dy)))
            center_text("SIMULATION TERMINÉE", self.title_font, (255,255,255), 40)
            center_text(f"Virtuosité Totale : +{self.final_stats['virtuosity']}", self.timer_font, (100,255,100), 100)
            center_text(f"Pollution Totale : -{self.final_stats['pollution_total']}", self.timer_font, (255,80,80), 140)
            center_text(f"(Constr: -{self.final_stats['pol_const']} | Durée: -{self.final_stats['pol_duree']} | Crue: -{self.final_stats['pol_flood']})", self.small_font, (200,150,150), 165)
            pygame.draw.line(self.screen, (150,150,150), (box.left+50, cy-20), (box.right-50, cy-20), 2)
            center_text(f"SCORE FINAL : {self.final_stats['score']}", self.title_font, (255,215,0), 240)
            center_text("Score = Virtuosité - Pollution", self.small_font, (150,150,150), 270)
            self.retry_rect = pygame.Rect(0, 0, 160, 50); self.retry_rect.center = (cx - 85, cy + 110)
            self.quit_rect = pygame.Rect(0, 0, 160, 50); self.quit_rect.center = (cx + 85, cy + 110)
            pygame.draw.rect(self.screen, (50, 150, 50), self.retry_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 255, 100), self.retry_rect, 2, border_radius=8)
            t_re = self.font.render("RECOMMENCER", True, (255,255,255))
            self.screen.blit(t_re, t_re.get_rect(center=self.retry_rect.center))
            pygame.draw.rect(self.screen, (150, 50, 50), self.quit_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 100, 100), self.quit_rect, 2, border_radius=8)
            t_qu = self.font.render("QUITTER", True, (255,255,255))
            self.screen.blit(t_qu, t_qu.get_rect(center=self.quit_rect.center))
            return
        if self.popup_active:
            s = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            self.screen.blit(s, (0,0))
            w, h = 440, 260
            px, py = (cfg.SCREEN_WIDTH - w)//2, (cfg.SCREEN_HEIGHT - h)//2
            p_rect = pygame.Rect(px, py, w, h)
            border_col = (200,200,200)
            if self.popup_data["type"] == "confirm":
                border_col = (255, 100, 100)
                if "VIABILITÉ" in self.popup_data["message"]:
                    try:
                        val = int(self.popup_data["message"].split('\n')[0].split(":")[1].replace("%",""))
                        border_col = (50, 255, 50) if val >= 70 else (255, 50, 50) if val < 50 else (180, 180, 180)
                    except: pass
            else:
                border_col = (255, 80, 80)
            pygame.draw.rect(self.screen, (50, 50, 60), p_rect, border_radius=12)
            pygame.draw.rect(self.screen, border_col, p_rect, 3, border_radius=12)
            t = self.timer_font.render(self.popup_data["title"], True, border_col)
            self.screen.blit(t, t.get_rect(center=(px+w//2, py+40)))
            y_txt = py + 90
            for i, line in enumerate(self.popup_data["message"].split('\n')):
                c = border_col if (i==0 and "VIABILITÉ" in line) else (255,255,255)
                l = self.font.render(line, True, c)
                self.screen.blit(l, l.get_rect(center=(px+w//2, y_txt)))
                y_txt += 25
            btn_w, btn_h = 120, 40
            if self.popup_data["type"] == "confirm":
                self.popup_rect_cancel = pygame.Rect(px + 40, py + h - 60, btn_w, btn_h)
                self.popup_rect_ok = pygame.Rect(px + w - 40 - btn_w, py + h - 60, btn_w, btn_h)
                pygame.draw.rect(self.screen, (100, 50, 50), self.popup_rect_cancel, border_radius=8)
                tc = self.font.render("ANNULER", True, (255,255,255))
                self.screen.blit(tc, tc.get_rect(center=self.popup_rect_cancel.center))
                bg_ok = (border_col[0]//3, border_col[1]//3, border_col[2]//3)
                pygame.draw.rect(self.screen, bg_ok, self.popup_rect_ok, border_radius=8)
                pygame.draw.rect(self.screen, border_col, self.popup_rect_ok, 1, border_radius=8)
                tok = self.font.render("CONFIRMER", True, border_col)
                self.screen.blit(tok, tok.get_rect(center=self.popup_rect_ok.center))
            else:
                self.popup_rect_ok = pygame.Rect(px + (w-btn_w)//2, py + h - 60, btn_w, btn_h)
                self.popup_rect_cancel = None
                pygame.draw.rect(self.screen, (100, 100, 120), self.popup_rect_ok, border_radius=8)
                tok = self.font.render("OK", True, (255,255,255))
                self.screen.blit(tok, tok.get_rect(center=self.popup_rect_ok.center))

    def _handle_click(self, pos):
        mx, my = pos
        # CORRECTION SOURIS : On décale les coordonnées pour tenir compte de la bande AR
        grid_mx = mx - cfg.MAP_OFFSET_X
        grid_my = my - cfg.MAP_OFFSET_Y
        map_pixel_width = cfg.MAP_WIDTH * cfg.TILE_SIZE
        map_pixel_height = cfg.MAP_HEIGHT * cfg.TILE_SIZE

        if self.popup_active:
            if self.popup_rect_cancel and self.popup_rect_cancel.collidepoint(mx, my):
                self.popup_active = False; self.popup_data = {}; self.message = "Annulé."
            elif self.popup_rect_ok and self.popup_rect_ok.collidepoint(mx, my):
                if self.popup_data["type"] == "confirm":
                    d = self.popup_data["action"]
                    self.execute_action(d["x"], d["y"], d["building"], 1)
                self.popup_active = False; self.popup_data = {}
            return
        if self.game_over:
            if self.retry_rect and self.retry_rect.collidepoint(mx, my): self.reset_game()
            elif self.quit_rect and self.quit_rect.collidepoint(mx, my): pygame.quit(); sys.exit()
            return
        if self.ai_btn_rect and self.ai_btn_rect.collidepoint(mx, my):
            self.message = "IA Réfléchit..."
            self.draw(); pygame.display.flip()
            self.save_matrix_snapshot()
            self.ai_engine.run_turn()
            self._check_external_actions()
            return
        # Vérification si le clic est dans la zone de la carte
        if 0 <= grid_mx < map_pixel_width and 0 <= grid_my < map_pixel_height:
            gx = grid_mx // cfg.TILE_SIZE
            gy = grid_my // cfg.TILE_SIZE
            self.place_building(gx, gy)

    # --- NETWORK ---

    def _get_game_state_string(self):
        """
        Génère la grille complète pour le mobile.
        PRIORITÉ : INONDATION (99) > BÂTIMENT > TERRAIN
        """
        combined_grid = np.zeros((cfg.MAP_HEIGHT, cfg.MAP_WIDTH), dtype=int)
        
        for y in range(cfg.MAP_HEIGHT):
            for x in range(cfg.MAP_WIDTH):
                # 1. PRIORITÉ ABSOLUE : L'INONDATION
                if hasattr(self, 'flooded_grid') and self.flooded_grid[y][x]:
                    combined_grid[y][x] = 99  # Code 99 = Boue / Inondation
                else:
                    # 2. Sinon, on regarde le terrain
                    terrain = self.map_data[y][x]
                    val = 0
                    if terrain == "plain": val = 1
                    elif terrain == "mountain": val = 2
                    elif terrain == "forest": val = 3
                    elif terrain == "river": val = 4
                    combined_grid[y][x] = val
                    
                    # 3. Et on regarde s'il y a un bâtiment par dessus
                    b_name = self.buildings_grid[y][x]
                    if b_name and b_name in BUILDING_TO_ID:
                        combined_grid[y][x] = BUILDING_TO_ID[b_name]

        # Rotation pour correspondre à l'orientation du mobile
        rotated_grid = np.rot90(combined_grid, k=1)
        
        # Conversion en une seule ligne de texte (ex: "1,1,2,99,1...")
        return ",".join(map(str, rotated_grid.flatten()))

    def _send_map_to_mobile(self, addr):
        map_data = self._get_game_state_string()
        self.network.send_to(map_data, addr)

    def _handle_mobile_build(self, tile_index, building_id, addr):
        """Reçoit un index Mobile, convertit et construit (Correction Coordonnées)."""
        # 1. Coordonnées MOBILE (Grille 10 colonnes)
        u_row = tile_index // 10
        u_col = tile_index % 10
        
        # 2. ROTATION INVERSE (Basée sur k=1 Anti-Horaire)
        # L'axe X du mobile devient l'axe Y du PC
        py_row = u_col 
        
        # L'axe Y du mobile devient l'axe X du PC (Inversé : Droite vers Gauche)
        py_col = (cfg.MAP_WIDTH - 1) - u_row

        # Debug console pour vérifier
        print(f"[DEBUG] Mobile({u_col}, {u_row}) -> PC({py_col}, {py_row})")

        # Vérification des limites de la carte PC
        if not (0 <= py_row < cfg.MAP_HEIGHT and 0 <= py_col < cfg.MAP_WIDTH):
            print(f"[ERREUR] Hors limites : ({py_col}, {py_row})")
            self.network.send_to("RESULT,ERROR", addr)
            return

        # Identification Bâtiment
        building_name = ID_TO_BUILDING.get(building_id)
        if not building_name:
            self.network.send_to("RESULT,ERROR", addr)
            return

        # Case déjà occupée ?
        if self.buildings_grid[py_row][py_col] is not None:
             print("[ERREUR] Case occupée")
             self.network.send_to("RESULT,ERROR", addr)
             return

        # Règles et Coûts
        rules = BUILDING_RULES.get(building_name)
        
        # Sauvegarde de la sélection actuelle
        old_selection = self.selected_building
        self.selected_building = building_name
        
        if self._check_building_constraints(py_col, py_row, rules) and \
           self._check_resources_cost(rules):
            
            # SUCCÈS : On construit
            self.execute_action(py_col, py_row, building_name, 1)
            print(f"[SUCCÈS] Bâtiment {building_name} placé en ({py_col},{py_row})")
            
            self.network.send_to("RESULT,OK", addr)
            self._send_map_to_mobile(addr) 
        else:
            print(f"[ECHEC] Pas assez de ressources ou terrain invalide")
            self.network.send_to("RESULT,ERROR", addr)
        
        self.selected_building = old_selection

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(cfg.FPS) / 1000.0
            if self.popup_active: dt = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
            self.update_game_logic(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()