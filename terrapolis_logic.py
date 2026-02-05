import numpy as np
import random
import copy
import json
import os
import sys

# --- IMPORT SECURISE ---
try:
    import IA_Dumb
except ImportError:
    print("ERREUR CRITIQUE: Le fichier 'IA_Dumb.py' est introuvable.")
    sys.exit()

# --- CONFIGURATION TEMPORELLE ---
MAP_H, MAP_W = 10, 15
SECONDS_PER_STEP = 13
TOTAL_STEPS = 60

# --- CHARGEMENT INTELLIGENT DU JSON ---
def load_and_flatten_rules():
    if not os.path.exists('Rules.json'):
        print("ERREUR: Rules.json introuvable.")
        sys.exit()
        
    with open('Rules.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flat_buildings = {}
    
    for b_name, b_data in data['buildings'].items():
        costs = b_data.get('additionalInstances', {}).get('cost', {})
        construct = b_data.get('construction', {})
        operation = b_data.get('operation', {})
        events = b_data.get('events', {})
        production = b_data.get('production', {}) # Connexion Production
        
        placement = b_data.get('placement', {})
        adj_req = None
        if 'operatesIfAdjacentTo' in placement:
            adj_req = placement['operatesIfAdjacentTo'][0]
        elif 'placementRequiresAdjacentTile' in placement:
            adj_req = placement['placementRequiresAdjacentTile'][0]

        flat_buildings[b_name] = {
            "cost_wood": costs.get('wood', 0),
            "cost_stone": costs.get('stones', 0),
            "virt": construct.get('virtuosityGain', 0),      
            "virt_sec": operation.get('virtuosityPerSec', 0),
            "poll": construct.get('pollutionOnBuild', 0),
            "poll_sec": operation.get('emitsPerSec', 0),
            
            # Paramètres de Production
            "prod_resource": production.get('resource', None),
            "prod_rate": production.get('ratePerSec', 0),
            
            "adj_req": adj_req,
            "firstFree": b_data.get('firstFree', False),
            "destroy_penalty": events.get('onPlayerDestroy', {}).get('loseVirtuosityAmount', 0)
        }
        
    return flat_buildings

BUILDINGS = load_and_flatten_rules()

class TerrapolisGame:
    def __init__(self):
        # 1. Gestion de la Carte
        if hasattr(IA_Dumb, 'generate_map_masks'):
            self.masks = IA_Dumb.generate_map_masks()
        elif hasattr(IA_Dumb, 'get_map'):
            self.masks = IA_Dumb.get_map()
        else:
            self.masks = {
                'mountain': getattr(IA_Dumb, 'mountain', getattr(IA_Dumb, 'MOUNTAIN_MASK', np.zeros((MAP_H, MAP_W)))),
                'forest':   getattr(IA_Dumb, 'forest',   getattr(IA_Dumb, 'FOREST_MASK',   np.zeros((MAP_H, MAP_W)))),
                'river':    getattr(IA_Dumb, 'river',    getattr(IA_Dumb, 'RIVER_MASK',    np.zeros((MAP_H, MAP_W)))),
                'plain':    getattr(IA_Dumb, 'plain',    getattr(IA_Dumb, 'PLAIN_MASK',    np.ones((MAP_H, MAP_W)))),
            }
        
        self.mountain_mask = np.array(self.masks.get('mountain'))
        self.forest_mask   = np.array(self.masks.get('forest'))
        self.river_mask    = np.array(self.masks.get('river'))
        self.plain_mask    = np.array(self.masks.get('plain'))

        # 2. État du jeu
        self.occupied_mask = np.zeros((MAP_H, MAP_W), dtype=bool)
        self.grid_types = np.full((MAP_H, MAP_W), "", dtype=object)
        
        # PHASE 3 : PAUVRETÉ (Ressources à 0)
        self.wood = 0 
        self.stone = 0
        
        self.virtuosity = 0
        self.pollution_total = 0
        self.turn = 0

        # FORCE 3 INONDATIONS (Plus de hasard à 0)
        self.flood_turns = set(random.sample(range(TOTAL_STEPS), 3))

        # STATISTIQUES
        self.stats_built = {}
        self.stats_lost_flood = {}
        self.stats_lost_player = {}
        
    def copy(self):
        return copy.deepcopy(self)

    def is_valid_pos(self, r, c, b_name):
        if r < 0 or r >= MAP_H or c < 0 or c >= MAP_W: return False
        if self.occupied_mask[r, c]: return False
        if self.plain_mask[r, c] == 0: return False 

        req_type = BUILDINGS[b_name].get('adj_req')
        target_mask = None
        if req_type == 'forest': target_mask = self.forest_mask
        elif req_type == 'mountain': target_mask = self.mountain_mask
        elif req_type == 'river': target_mask = self.river_mask
        
        if target_mask is not None:
            has_adj = False
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < MAP_H and 0 <= nc < MAP_W:
                    if target_mask[nr, nc]: has_adj = True; break
            if not has_adj: return False
        return True

    def get_legal_actions(self):
        actions = [("WAIT", -1, -1)]
        affordable = []
        
        # Options Construction
        for b_name, stats in BUILDINGS.items():
            count = np.sum(self.grid_types == b_name)
            cw = stats.get('cost_wood', 0)
            cs = stats.get('cost_stone', 0)
            if stats.get('firstFree', False) and count == 0: cw, cs = 0, 0
            if self.wood >= cw and self.stone >= cs: affordable.append(b_name)
        
        for b in affordable:
            attempts = 0; found = 0
            while attempts < 30 and found < 3:
                r = random.randint(0, MAP_H-1)
                c = random.randint(0, MAP_W-1)
                if self.is_valid_pos(r, c, b):
                    actions.append((b, r, c)); found += 1
                attempts += 1
                
        # Options Destruction
        rows, cols = np.where(self.occupied_mask)
        for i in range(len(rows)):
            actions.append(("DESTROY", rows[i], cols[i]))

        return list(set(actions))

    # PARAMETRE VERBOSE=FALSE PAR DEFAUT (Pour l'entraînement)
    def step(self, action, verbose=False):
        b_name, r, c = action
        
        # 1. PRODUCTION DYNAMIQUE (JSON)
        prod_wood = 0
        prod_stone = 0
        for b_key, stats in BUILDINGS.items():
            count = np.sum(self.grid_types == b_key)
            if count > 0:
                res_type = stats.get('prod_resource')
                rate = stats.get('prod_rate', 0)
                amount = count * rate * SECONDS_PER_STEP
                if res_type == 'wood': prod_wood += amount
                elif res_type == 'stones': prod_stone += amount
        self.wood += prod_wood
        self.stone += prod_stone
        
        # 2. Temps
        tick_poll = 0; tick_virt = 0  
        for b_key, stats in BUILDINGS.items():
            count = np.sum(self.grid_types == b_key)
            if count > 0:
                tick_poll += count * stats.get('poll_sec', 0)
                tick_virt += count * stats.get('virt_sec', 0)
        self.pollution_total += tick_poll * SECONDS_PER_STEP
        self.virtuosity += tick_virt * SECONDS_PER_STEP 

        # 3. Actions
        if b_name == "WAIT":
            pass
            
        elif b_name == "DESTROY":
            target_b = self.grid_types[r, c]
            if target_b != "":
                penalty = BUILDINGS[target_b].get('destroy_penalty', 0)
                self.occupied_mask[r, c] = False
                self.grid_types[r, c] = ""
                self.virtuosity -= penalty
                self.stats_lost_player[target_b] = self.stats_lost_player.get(target_b, 0) + 1
                
                if verbose:
                    print(f"DESTRUCTION : {target_b} en ({r}, {c}) (Malus: -{penalty})")

        else:
            self.occupied_mask[r, c] = True
            self.grid_types[r, c] = b_name
            stats = BUILDINGS[b_name]
            
            cw = stats.get('cost_wood', 0)
            cs = stats.get('cost_stone', 0)
            count = np.sum(self.grid_types == b_name)
            if stats.get('firstFree', False) and count == 1: cw, cs = 0, 0
            
            self.wood -= cw
            self.stone -= cs

            self.virtuosity += stats.get('virt', 0)
            self.pollution_total += stats.get('poll', 0)
            self.stats_built[b_name] = self.stats_built.get(b_name, 0) + 1
            
            if verbose:
                print(f"CONSTRUCTION : {b_name} en ({r}, {c})")

        # 4. Inondation
        if self.turn in self.flood_turns:
            if verbose:
                print(f"\n[ALERTE] INNONDATION au Tour {self.turn} !")
            
            rows, cols = np.where(self.occupied_mask)
            damage_count = 0
            for i in range(len(rows)):
                rr, cc = rows[i], cols[i]
                adj_river = False
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < MAP_H and 0 <= nc < MAP_W:
                        if self.river_mask[nr, nc]: adj_river = True; break
                
                if adj_river:
                    destroyed = self.grid_types[rr, cc]
                    if destroyed:
                        if verbose:
                            print(f"DÉSASTRE : {destroyed} en ({rr}, {cc}) a été détruit par l'inondation !")
                        
                        self.occupied_mask[rr, cc] = False
                        self.grid_types[rr, cc] = ""
                        self.pollution_total += 200 
                        self.virtuosity -= BUILDINGS[destroyed].get('virt', 0)
                        self.stats_lost_flood[destroyed] = self.stats_lost_flood.get(destroyed, 0) + 1
                        damage_count += 1
            
            if verbose:
                if damage_count == 0: print("Aucun bâtiment touché.")
                else: print(f"Bilan : {damage_count} bâtiment(s) perdu(s).")

        self.turn += 1

        
        return self.virtuosity - self.pollution_total