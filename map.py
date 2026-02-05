import numpy as np
import json
import os
import time
from datetime import datetime

# --- CONFIGURATION ---
_H, _W = 10, 15
_building_names = [
    'sawmill', 'quarry', 'coal_plant', 'wind_turbine', 'nuclear_plant', 'residence'
]

# --- DATA ENVIRONNEMENT (Statique) ---
# 1 = Présence du terrain, 0 = Absence
mountain = np.array([
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
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

class TerrapolisAI:
    def __init__(self):
        self.rules = self.load_rules("Rules.json")
        self.tile_layers_data = {
            'mountain': mountain,
            'plain': plain,
            'forest': forest,
            'river': river
        }
        self.rng = np.random.default_rng()
        
        # Initialisation des matrices dummy (état interne de l'IA)
        self.building_matrices = {}
        self.zero_copies = {}
        self.flooded_mask = np.zeros((_H, _W), dtype=int)
        
        # Génération initiale aléatoire (pour avoir une base de scores)
        _cells = _H * _W
        _needed = _cells * len(_building_names)
        possible_values = np.arange(-100000, 100001, dtype=int)
        _vals = self.rng.choice(possible_values, size=_needed, replace=False)

        for i, bname in enumerate(_building_names):
            start = i * _cells
            stop = start + _cells
            self.building_matrices[bname] = _vals[start:stop].reshape((_H, _W))
            self.zero_copies[bname] = np.zeros((_H, _W), dtype=int)

        self.neg_ban = {b: np.zeros((_H, _W), dtype=bool) for b in _building_names}
        self.iteration_count = 0

    def load_rules(self, filename="Rules.json"):
        candidates = [
            filename,
            os.path.join(os.getcwd(), filename),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        print(f"[IA] Règles chargées depuis: {p}")
                        return json.load(f)
                except:
                    pass
        print("[IA] ERREUR: Rules.json non trouvé.")
        return None

    def _detect_tile_at(self, r, c):
        # Cette fonction reste utile pour l'adjacence, mais on ne l'utilisera plus
        # pour le filtrage "Interdit", on utilisera des masques directs.
        if 'river' in self.tile_layers_data and int(self.tile_layers_data['river'][r, c]) == 1: return 'river'
        if 'mountain' in self.tile_layers_data and int(self.tile_layers_data['mountain'][r, c]) == 1: return 'mountain'
        if 'forest' in self.tile_layers_data and int(self.tile_layers_data['forest'][r, c]) == 1: return 'forest'
        if 'plain' in self.tile_layers_data and int(self.tile_layers_data['plain'][r, c]) == 1: return 'plain'
        return 'empty'

    def update_state_from_file(self):
        """Lit matrix_state.txt (sauvegardé par le jeu) pour mettre à jour la vision du monde de l'IA"""
        proj_root = os.path.dirname(os.path.abspath(__file__))
        paths = [
            os.path.join(proj_root, 'Batiment_Maps', 'matrix_state.txt'),
            os.path.join(proj_root, 'matrix_state.txt'),
            'matrix_state.txt'
        ]
        
        found_path = None
        for p in paths:
            if os.path.exists(p):
                found_path = p
                break
        
        if not found_path:
            return

        with open(found_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines()]
        
        current_section = None
        temp_sections = {}
        
        for line in lines:
            if line.startswith("==="):
                current_section = line.replace("===", "").strip()
                temp_sections[current_section] = []
                continue
            
            if current_section and line:
                try:
                    vals = [int(x) for x in line.split()]
                    if len(vals) == _W:
                        temp_sections[current_section].append(vals)
                except:
                    pass

        # Mise à jour des copies zéros (état actuel des bâtiments)
        for bname in _building_names:
            if bname in temp_sections:
                arr = np.array(temp_sections[bname])
                if arr.shape == (_H, _W):
                    self.zero_copies[bname] = arr
        
        # Mise à jour du masque inondation (pour ne pas construire dessus)
        if "FLOOD" in temp_sections:
            flood_arr = np.array(temp_sections["FLOOD"])
            if flood_arr.shape == (_H, _W):
                self.flooded_mask = flood_arr

    def write_action_file(self, chosen):
        """Écrit le fichier action.txt lu par le jeu"""
        out_lines = []
        now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        out_lines.append(f"{now_str}") 

        if chosen:
            val, bname, r, c = chosen
            sign = 1 if val > 0 else -1
            
            out_lines.append(f"=== {bname} ===")
            for y in range(_H):
                row_str = []
                for x in range(_W):
                    if y == r and x == c:
                        row_str.append(str(sign)) 
                    else:
                        row_str.append("0")
                out_lines.append(" ".join(row_str))
            
            try:
                with open("action.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(out_lines))
                print(f"[IA] Action écrite : {bname} en ({c},{r}) sign={sign}")
            except Exception as e:
                print(f"[IA] Erreur écriture action.txt: {e}")
        else:
            print("[IA] Pas de candidat valide trouvé cette fois-ci.")

    def run_turn(self):
        """Exécute UNE itération de décision"""
        self.iteration_count += 1
        print(f"\n[IA] --- Tour {self.iteration_count} ---")
        
        # 1. Mise à jour de la vision
        self.update_state_from_file()

        pos_scores = {}
        neg_scores = {}

        # Vérification si un bâtiment existe déjà (globalement)
        has_building = np.zeros((_H, _W), dtype=bool)
        for b in _building_names:
            if b in self.zero_copies:
                has_building |= (self.zero_copies[b] == 1)

        for bname in _building_names:
            # Random scores 0..10000
            pos = self.rng.integers(0, 10001, size=(_H, _W), dtype=int)
            neg = self.rng.integers(0, 10001, size=(_H, _W), dtype=int)

            # Règle universelle : pas de construction sur case occupée
            pos[has_building] = 0
            
            # Règle universelle : pas de construction sur inondation
            if np.any(self.flooded_mask):
                pos[self.flooded_mask == 1] = 0

            # Règles de destruction : uniquement là où le batiment existe
            neg_final = np.zeros((_H, _W), dtype=int)
            if bname in self.zero_copies:
                present = (self.zero_copies[bname] == 1)
                neg_final[present] = neg[present]
            
            # Application ban temporaire
            if np.any(self.neg_ban[bname]):
                neg_final[self.neg_ban[bname]] = 0
                self.neg_ban[bname][:] = False

            # --- FILTRAGE JSON RULES (MODIFIÉ) ---
            if self.rules:
                b_rules = self.rules.get('buildings', {}).get(bname, {})
                placement = b_rules.get('placement', {})
                
                # 1. Terrains interdits (Utilisation de masques pour être sûr)
                forbidden = placement.get('placementForbiddenTiles', [])
                
                # Si 'mountain' est interdit, on annule le score partout où mountain == 1
                if 'mountain' in forbidden:
                    pos[self.tile_layers_data['mountain'] == 1] = 0
                    
                if 'river' in forbidden:
                    pos[self.tile_layers_data['river'] == 1] = 0
                    
                if 'forest' in forbidden:
                    pos[self.tile_layers_data['forest'] == 1] = 0
                    
                if 'plain' in forbidden:
                    pos[self.tile_layers_data['plain'] == 1] = 0
                
                # 2. Adjacence requise (requiresAdjacentTile et operatesIfAdjacentTo)
                # On combine les deux listes car si l'un manque, c'est bloquant pour l'IA
                req_list = placement.get('placementRequiresAdjacentTile', [])
                needs_list = placement.get('operatesIfAdjacentTo', [])
                
                # Fusionner les listes si elles existent
                all_reqs = []
                if req_list: all_reqs.extend(req_list)
                if needs_list: all_reqs.extend(needs_list)
                
                if all_reqs:
                    # On crée un masque des zones valides (qui ont au moins un voisin requis)
                    valid_mask = np.zeros((_H, _W), dtype=bool)
                    
                    # Pour chaque type de terrain requis
                    for req_type in all_reqs:
                        if req_type in self.tile_layers_data:
                            layer = self.tile_layers_data[req_type]
                            # On regarde si chaque case a un voisin == 1 dans ce layer
                            # (Technique simple: décalage des matrices)
                            padded = np.pad(layer, pad_width=1, mode='constant', constant_values=0)
                            
                            # Voisins Haut, Bas, Gauche, Droite
                            up = padded[:-2, 1:-1]
                            down = padded[2:, 1:-1]
                            left = padded[1:-1, :-2]
                            right = padded[1:-1, 2:]
                            
                            # Si un voisin existe, la case devient valide pour ce type
                            has_neighbor = (up | down | left | right)
                            valid_mask |= (has_neighbor == 1)
                    
                    # On ne garde que les scores sur les cases valides
                    pos[~valid_mask] = 0

            pos_scores[bname] = pos
            neg_scores[bname] = neg_final

        # 3. Sélection du meilleur candidat
        candidates = []
        for bname in _building_names:
            p = pos_scores[bname]
            n = neg_scores[bname]
            
            # Construction candidates
            ys, xs = np.nonzero(p)
            for i in range(len(ys)):
                candidates.append((p[ys[i], xs[i]], 1, bname, ys[i], xs[i]))
            
            # Destruction candidates
            ys, xs = np.nonzero(n)
            for i in range(len(ys)):
                candidates.append((n[ys[i], xs[i]], -1, bname, ys[i], xs[i]))

        # Tri décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)

        if candidates:
            # On prend le premier
            best = candidates[0]
            val_abs, sign, bname, r, c = best
            
            # Si c'est une destruction, on ban pour le tour suivant
            if sign == -1:
                self.neg_ban[bname][r, c] = True
            
            final_val = val_abs * sign
            self.write_action_file((final_val, bname, r, c))
        else:
            self.write_action_file(None)