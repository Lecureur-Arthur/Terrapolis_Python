import numpy as np
import random
import json
import os
import time
import math
from datetime import datetime

# --- CONFIGURATION ---
_H, _W = 10, 15
_cells = _H * _W

# Liste des bâtiments (Doit correspondre aux clés du JSON)
_building_names = [
    'sawmill', 'quarry', 'coal_plant', 'wind_turbine', 'nuclear_plant', 'residence'
]

# Delay between iterations (seconds). Default 15s, can be overridden
# by environment variable `TERRAPOLIS_ITERATION_DELAY` (float).
ITERATION_DELAY = float(os.environ.get('TERRAPOLIS_ITERATION_DELAY', 15.0))

# Génération DES MATRIces DUMMY : valeurs uniques dans [-100000,100000]
# On garde aussi une copie VIDE pour affichage (dummy_zero_<bname>)
rng = np.random.default_rng()
_needed = _cells * len(_building_names)
possible_values = np.arange(-100000, 100001, dtype=int)
# Tirage sans remplacement pour garantir valeurs uniques
_vals = rng.choice(possible_values, size=_needed, replace=False)

for i, bname in enumerate(_building_names):
    start = i * _cells
    stop = start + _cells
    mat = _vals[start:stop].reshape((_H, _W))
    globals()[f'dummy_{bname}'] = mat
    # copie vide pour affichage séparé
    globals()[f'dummy_zero_{bname}'] = np.zeros((_H, _W), dtype=int)

# Créer des matrices séparées positives / négatives dérivées des dummies
for bname in _building_names:
    mat = globals().get(f'dummy_{bname}')
    if isinstance(mat, np.ndarray):
        pos_mat = mat.copy()
        pos_mat[pos_mat < 0] = 0
        neg_mat = mat.copy()
        neg_mat[neg_mat > 0] = 0
        globals()[f'dummy_pos_{bname}'] = pos_mat
        globals()[f'dummy_neg_{bname}'] = neg_mat

# --- DATA ENVIRONNEMENT ---

mountain = np.array([
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
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

# Fonction appelée par terrapolis_logic.py
def generate_map_masks():
    return {
        'mountain': mountain,
        'forest': forest,
        'river': river,
        'plain': plain
    }

# --- CHARGEMENT DES RÈGLES DEPUIS rules.json ---
def load_rules(filename="Rules.json"):
    """Try to load Rules.json robustly from multiple candidate locations.

    Search order:
      1. If filename is an absolute path and exists -> use it
      2. Current working directory
      3. The directory containing this module
      4. The parent directory of this module (useful when module is in a subfolder)
      5. Parent of parent (two levels up)
      6. Path from environment variable TERRAPOLIS_RULES_PATH

    Returns parsed JSON dict or None on failure (prints helpful message).
    """
    candidates = []
    # if given as absolute or relative path directly, prefer it
    candidates.append(filename)
    # cwd
    candidates.append(os.path.join(os.getcwd(), filename))
    # directory of this file
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, filename))
    # parent directories (one and two levels up)
    candidates.append(os.path.join(here, '..', filename))
    candidates.append(os.path.join(here, '..', '..', filename))
    # environment override
    envp = os.environ.get('TERRAPOLIS_RULES_PATH')
    if envp:
        candidates.insert(0, envp)

    tried = []
    for p in candidates:
        if not p:
            continue
        p_norm = os.path.abspath(os.path.expanduser(p))
        if p_norm in tried:
            continue
        tried.append(p_norm)
        if os.path.exists(p_norm):
            try:
                with open(p_norm, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded Rules.json from: {p_norm}")
                    return data
            except json.JSONDecodeError as e:
                print(f"ERREUR: Fichier trouvé mais JSON invalide at {p_norm}: {e}")
                return None
            except Exception as e:
                print(f"ERREUR: Impossible de lire {p_norm}: {e}")
                return None

    # nothing found
    print("ERREUR: Rules.json introuvable. Emplacements testés:")
    for p in tried:
        print(" -", p)
    return None
# --- FONCTIONS ---

def _detect_tile_at(tile_layers, r, c):
    """Retourne le type de tuile à la position r,c.
    Ordre de priorité : river > mountain > forest > plain.
    """
    if tile_layers is None: return None
    # Priorités
    if 'river' in tile_layers and int(tile_layers['river'][r, c]) == 1: return 'river'
    if 'mountain' in tile_layers and int(tile_layers['mountain'][r, c]) == 1: return 'mountain'
    if 'forest' in tile_layers and int(tile_layers['forest'][r, c]) == 1: return 'forest'
    if 'plain' in tile_layers and int(tile_layers['plain'][r, c]) == 1: return 'plain'
    return 'empty'


def _parse_matrix_state_header(path='matrix_state.txt'):
    """Return header lines (everything before first '===') and section order.

    If file not found, returns a minimal header and reasonable section order.
    """
    header_lines = []
    section_names = []
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matrix_state.txt')
    if not os.path.exists(p):
        # fallback
        header_lines = [f"Snapshot Date: {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"]
        section_names = ['mountain', 'plain', 'forest', 'river'] + _building_names
        return header_lines, section_names

    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('==='):
                # collect section name
                name = line.strip().strip('= ').strip()
                section_names.append(name)
                break
            header_lines.append(line.rstrip('\n'))
        # continue to find remaining section names
        for line in f:
            if line.strip().startswith('==='):
                name = line.strip().strip('= ').strip()
                section_names.append(name)
    return header_lines, section_names


def parse_matrix_state_file(path):
    """Parse the full `matrix_state.txt` file and return (header_lines, sections).

    sections is a dict mapping section name -> numpy int array of shape (H, W).
    If a section has fewer than H rows the missing rows are padded with zeros.
    """
    H, W = _H, _W
    header_lines = []
    sections = {}
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f]

    i = 0
    # collect header until first '==='
    while i < len(lines) and not lines[i].strip().startswith('==='):
        header_lines.append(lines[i])
        i += 1

    # parse sections
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('==='):
            name = line.strip('= ').strip()
            i += 1
            rows = []
            # collect up to H non-empty lines for this section
            while i < len(lines) and len(rows) < H:
                ln = lines[i].strip()
                if ln == '':
                    i += 1
                    continue
                if ln.startswith('==='):
                    break
                parts = ln.split()
                # convert to ints, pad/truncate to W
                nums = [int(x) for x in parts[:W]]
                if len(nums) < W:
                    nums += [0] * (W - len(nums))
                rows.append(nums)
                i += 1
            # if fewer rows, pad
            while len(rows) < H:
                rows.append([0] * W)
            try:
                arr = np.array(rows, dtype=int)
            except Exception:
                arr = np.zeros((H, W), dtype=int)
            sections[name] = arr
        else:
            i += 1

    return header_lines, sections


def _write_iteration_winner(iteration, chosen, outdir=None, header_lines=None, section_names=None):
    """Write a file `iteration{iteration}_winner` matching format of matrix_state.

    `chosen` should be a tuple (real_val, bname, r, c) or None. If chosen is None,
    write zeros for all building sections. If chosen present and action is destruction
    (real_val < 0) write -1 at that position in corresponding building section.
    Terrain sections are written using the in-memory arrays `mountain`, `plain`,
    `forest`, `river`.
    """
    if header_lines is None or section_names is None:
        header_lines, section_names = _parse_matrix_state_header()

    out_lines = []
    out_lines.extend(header_lines)
    out_lines.append('')

    # helper to render a numpy array
    def render_matrix(mat):
        return [' '.join(str(int(x)) for x in row) for row in mat]

    # terrains in known order
    terrains = {'mountain': globals().get('mountain'),
                'plain': globals().get('plain'),
                'forest': globals().get('forest'),
                'river': globals().get('river')}

    # write terrains first (if in section_names order, follow that order)
    for name in section_names:
        if name in terrains and terrains[name] is not None:
            out_lines.append(f"=== {name} ===")
            out_lines.extend(render_matrix(terrains[name]))
            out_lines.append('')

    # write building sections
    H, W = _H, _W
    for bname in _building_names:
        out_lines.append(f"=== {bname} ===")
        # default zeros
        mat_lines = []
        for r in range(H):
            row = ['0'] * W
            mat_lines.append(row)

        if chosen is not None:
            real_val, win_bname, win_r, win_c = chosen
            if win_bname == bname:
                sign = '1' if real_val >= 0 else '-1'
                mat_lines[win_r][win_c] = sign

        # append rows
        for row in mat_lines:
            out_lines.append(' '.join(row))
        out_lines.append('')

    # default output folder: project root (directory containing this file)
    proj_root = os.path.dirname(os.path.abspath(__file__))
    if outdir is None:
        outdir = proj_root
    outdir = os.path.abspath(outdir)

    # Two destinations directly under project root:
    # - Action/action (overwritten each iteration)
    # - Iteration/iteration{iteration} (keeps history)
    action_dir = os.path.join(outdir, 'Action')
    iterations_dir = os.path.join(outdir, 'Iteration')
    os.makedirs(action_dir, exist_ok=True)
    os.makedirs(iterations_dir, exist_ok=True)

    action_path = os.path.join(action_dir, 'action.txt')
    hist_path = os.path.join(iterations_dir, f'iteration{iteration}.txt')

    # Ensure the action file has a fresh timestamp in first line so main.py
    # detects new actions (it compares the first line to a stored date).
    now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if out_lines:
        out_lines[0] = f"Snapshot Date: {now_str}"
    else:
        out_lines.insert(0, f"Snapshot Date: {now_str}")

    with open(action_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))

    # For history file keep the same content (with same fresh timestamp)
    with open(hist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))


def _save_batiment_snapshot_from_zero_copies(zero_copies, outdir=None):
    """Write a full matrix_state.txt under `Batiment_Maps/matrix_state.txt` using
    the provided `zero_copies` dict which holds -1/0/1 per building.
    """
    H, W = _H, _W
    proj_root = os.path.dirname(os.path.abspath(__file__))
    if outdir is None:
        outdir = os.path.join(proj_root, 'Batiment_Maps')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'matrix_state.txt')

    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    lines = [f"Snapshot Date: {now_str}", ""]

    # terrains
    for tname in ('mountain', 'plain', 'forest', 'river'):
        lines.append(f"=== {tname} ===")
        mat = globals().get(tname)
        if isinstance(mat, np.ndarray) and mat.shape == (H, W):
            for r in range(H):
                row = ' '.join(str(int(x)) for x in mat[r])
                lines.append(row)
        else:
            for r in range(H):
                lines.append(' '.join('0' for _ in range(W)))
        lines.append('')

    # building sections (use zero_copies values; default 0)
    for bname in _building_names:
        lines.append(f"=== {bname} ===")
        mat = zero_copies.get(bname)
        if isinstance(mat, np.ndarray) and mat.shape == (H, W):
            for r in range(H):
                row = ' '.join(str(int(x)) for x in mat[r])
                lines.append(row)
        else:
            for r in range(H):
                lines.append(' '.join('0' for _ in range(W)))
        lines.append('')

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        # diagnostic
        # print(f"Wrote Batiment snapshot: {path}")
    except Exception as e:
        print(f"Erreur écriture Batiment_Maps/matrix_state.txt: {e}")


def compute_signed_action_matrices(building_matrices=None, tile_layers=None, rules=None):
    """
    Calcule l'action optimale unique selon Magnitude > Premier trouvé.
    """
    # 1. Récupération des matrices
    if building_matrices is None:
        building_matrices = {}
        for name, val in globals().items():
            if name.startswith('dummy_') and isinstance(val, np.ndarray):
                bname = name.replace('dummy_', '')
                if bname in _building_names:
                    building_matrices[bname] = val

    if len(building_matrices) == 0: return {}
    any_mat = next(iter(building_matrices.values()))
    H, W = any_mat.shape

    # 2. Liste des candidats (Tri par Magnitude)
    sorted_bnames = sorted(list(building_matrices.keys()))
    candidates = []
    for bname in sorted_bnames:
        mat = building_matrices[bname]
        if mat.shape != (H, W): continue
        for r in range(H):
            for c in range(W):
                val = int(mat[r, c])
                candidates.append((abs(val), val, bname, r, c))

    # Tri stable sur la valeur absolue (Magnitude décroissante)
    candidates.sort(key=lambda x: x[0], reverse=True)

    chosen = None

    # 3. Sélection avec règles JSON chargées
    for abs_val, real_val, bname, r, c in candidates:
        allowed = True
        if rules is not None:
            b_rules = rules.get('buildings', {}).get(bname, {})
            placement = b_rules.get('placement', {})
            
            # A. Vérification : Tuile Interdite (Forbidden Tiles)
            current_tile = _detect_tile_at(tile_layers, r, c)
            forbidden = placement.get('placementForbiddenTiles', [])
            
            if forbidden and current_tile in forbidden:
                allowed = False
            
            # B. Vérification : Adjacence Requise (RequiresAdjacentTile)
            # Certains fichiers de règles indiquent 'operatesIfAdjacentTo' (ex: scierie,
            # carrière) pour signifier que l'établissement fonctionne seulement
            # s'il est adjacent à tel type de tuile. Ici on considère que si
            # 'placementRequiresAdjacentTile' est présent OR 'operatesIfAdjacentTo'
            # est présent, alors l'adjacence doit être vérifiée au placement.
            if allowed and (not placement.get('placementAllowedAnywhere', True) or placement.get('operatesIfAdjacentTo')):
                required_adj_types = placement.get('placementRequiresAdjacentTile', []) + placement.get('operatesIfAdjacentTo', [])
                
                if not required_adj_types:
                    allowed = False
                else:
                    has_valid_neighbor = False
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            neigh_tile = _detect_tile_at(tile_layers, rr, cc)
                            if neigh_tile in required_adj_types:
                                has_valid_neighbor = True
                                break
                    
                    if not has_valid_neighbor:
                        allowed = False
            
        if allowed:
            chosen = (real_val, bname, r, c)
            break

    # 4. Output
    outputs = {b: np.zeros((H, W), dtype=int) for b in building_matrices.keys()}
    if chosen is not None:
        real_val, win_bname, win_r, win_c = chosen
        sign = 1 if real_val >= 0 else -1
        outputs[win_bname][win_r, win_c] = sign
        tile_type = _detect_tile_at(tile_layers, win_r, win_c)
        print(f"\n>>> DÉCISION FINALE : {win_bname}")
        # Affiche les coordonnées en 1-based pour l'utilisateur (1..H, 1..W)
        print(f"    Position : ({win_r+1}, {win_c+1})")
        print(f"    Terrain  : {tile_type}")
        print(f"    Score    : {real_val}")
    else:
        print("\n>>> AUCUN CHOIX POSSIBLE (Toutes les actions violent les règles)")

    return outputs


def get_sorted_candidates(building_matrices=None):
    """Return a list of candidates sorted by magnitude (abs) descending.

    Each candidate is (abs_val, real_val, bname, r, c).
    This function does NOT apply any Rules.json filtering.
    """
    if building_matrices is None:
        building_matrices = {}
        for name, val in list(globals().items()):
            if name.startswith('dummy_') and isinstance(val, np.ndarray) and not name.startswith('dummy_zero_'):
                bname = name.replace('dummy_', '')
                if bname in _building_names:
                    building_matrices[bname] = val

    if len(building_matrices) == 0:
        return []

    any_mat = next(iter(building_matrices.values()))
    H, W = any_mat.shape

    candidates = []
    sorted_bnames = sorted(list(building_matrices.keys()))
    for bname in sorted_bnames:
        mat = building_matrices[bname]
        if mat.shape != (H, W):
            continue
        for r in range(H):
            for c in range(W):
                val = int(mat[r, c])
                candidates.append((abs(val), val, bname, r, c))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


def apply_candidates_with_rules(candidates, tile_layers, rules, H, W):
    """Iterate candidates (already sorted) and apply the first one that passes Rules.json.

    Returns (outputs, chosen) where outputs is a dict of zero matrices with the chosen cell
    set to +1 or -1 (sign of the real value). If none allowed, chosen is None.
    """
    outputs = {b: np.zeros((H, W), dtype=int) for b in _building_names}
    chosen = None

    for abs_val, real_val, bname, r, c in candidates:
        allowed = True
        if rules is not None:
            b_rules = rules.get('buildings', {}).get(bname, {})
            placement = b_rules.get('placement', {})

            current_tile = _detect_tile_at(tile_layers, r, c)
            forbidden = placement.get('placementForbiddenTiles', [])
            if forbidden and current_tile in forbidden:
                allowed = False

            if allowed and (not placement.get('placementAllowedAnywhere', True) or placement.get('operatesIfAdjacentTo')):
                required_adj_types = placement.get('placementRequiresAdjacentTile', []) + placement.get('operatesIfAdjacentTo', [])
                if not required_adj_types:
                    allowed = False
                else:
                    has_valid_neighbor = False
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            neigh_tile = _detect_tile_at(tile_layers, rr, cc)
                            if neigh_tile in required_adj_types:
                                has_valid_neighbor = True
                                break
                    if not has_valid_neighbor:
                        allowed = False

        if allowed:
            sign = 1 if real_val >= 0 else -1
            outputs[bname][r, c] = sign
            chosen = (real_val, bname, r, c)
            break

    return outputs, chosen

# =============================================================================
# 3. BOUCLE DE SIMULATION VISUELLE (15 min)
# =============================================================================
# C'est ce qui tournait avant. Je le mets dans une fonction pour ne pas qu'il se lance tout seul.

def run_visual_simulation_15min():
    print(">>> Démarrage de la simulation visuelle (15 min)...")
    # (Ici se trouvait votre énorme boucle while time.time() < DURATION)
    # Si vous n'utilisez plus l'interface pour le mode random, on peut laisser ça vide.
    # Si l'interface a besoin de lancer ce fichier, elle appellera cette fonction.
    pass


    # --- EXECUTION ---

if __name__ == "__main__":
    tile_layers_data = {
        'mountain': mountain,
        'plain': plain,
        'forest': forest,
        'river': river
    }

    # Charge les règles dans la variable 'rules' (nommée ainsi pour éviter le NameError)
    rules = load_rules("Rules.json")

if __name__ == "__main__" and rules:
    # 1. PRINT DES MATRICES DUMMY (affiche les matrices elles-mêmes)
    print("="*60)
    print(" 1. MATRICES DUMMY (SCORES BRUTS)")
    print("="*60)
    for bname in _building_names:
        mat = globals().get(f'dummy_{bname}')
        if mat is not None:
            try:
                maxv = np.max(mat)
                minv = np.min(mat)
            except Exception:
                maxv = None
                minv = None
            print(f"--- {bname} (Max: {maxv}, Min: {minv}) ---")
            # Affichage original (10 lignes × 15 colonnes)
            print(mat)

    # 1.b AFFICHER LES COPIES VIDES (dummy_zero_<bname>)
    print("\n" + "="*60)
    print(" 1.b COPIES VIDES (dummy_zero_<building>)")
    print("="*60)
    for bname in _building_names:
        zmat = globals().get(f'dummy_zero_{bname}')
        if zmat is not None:
            print(f"--- {bname} (empty copy) ---")
            # Affichage original (10 lignes × 15 colonnes)
            print(zmat)

    # 1.c Matrices POS/NEG: suppression des impressions détaillées (temporaire)

    # 2. CALCUL / Application des règles lors de la modification des matrices vides
    # 2.a Récupère les matrices de scores (dummy_<bname>)
    building_matrices = {}
    for name, val in list(globals().items()):
        if name.startswith('dummy_') and isinstance(val, np.ndarray) and not name.startswith('dummy_zero_'):
            bname = name.replace('dummy_', '')
            if bname in _building_names:
                building_matrices[bname] = val

    # 2.b Récupère les zéros copies (dummy_zero_<bname>) — celles qu'on doit modifier si placement autorisé
    zero_copies = {}
    any_mat = next(iter(building_matrices.values())) if building_matrices else None
    H, W = any_mat.shape if any_mat is not None else (_H, _W)
    for bname in _building_names:
        z = globals().get(f'dummy_zero_{bname}')
        if z is None:
            zero_copies[bname] = np.zeros((H, W), dtype=int)
        else:
            zero_copies[bname] = z.copy()

    # If a `matrix_state.txt` exists in the project root (updated by `main.py`),
    # parse it and apply terrain layers and building sections to our state
    try:
        proj_root = os.path.dirname(os.path.abspath(__file__))
        # Try multiple candidate locations where main.py may write the snapshot
        candidate_paths = [
            os.path.join(proj_root, 'matrix_state.txt'),
            os.path.join(proj_root, 'Batiment_Maps', 'matrix_state.txt'),
            os.path.join(proj_root, 'Batiment_state.txt'),
        ]
        matrix_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                matrix_path = p
                break
        if matrix_path is not None:
            hdr, secs = parse_matrix_state_file(matrix_path)
            print(f"Chargé matrix_state.txt depuis: {matrix_path}")
            # override terrain layers if provided
            for tname in ('mountain', 'plain', 'forest', 'river'):
                if tname in secs:
                    try:
                        tile_layers_data[tname] = secs[tname].copy()
                    except Exception:
                        pass
            # override zero_copies (built state) if building sections present
            for bname in _building_names:
                if bname in secs:
                    arr = secs[bname]
                    if isinstance(arr, np.ndarray) and arr.shape == (H, W):
                        zero_copies[bname] = arr.copy()
    except Exception as e:
        print(f"Erreur lors du parsing de matrix_state.txt: {e}")

    # 2.c Construire la liste de candidats triée par magnitude (ignore les règles pour ce tri)
    candidates = get_sorted_candidates(building_matrices)

    # 2.d Appliquer les règles maintenant, uniquement au moment d'écrire dans la copie vide
    # Boucle dynamique : on réitère l'expérience en reprenant les matrices mises à jour
    # Utilisation : on démarre avec les matrices de scores `building_matrices` (scores initiaux)
    # puis à chaque itération on remplace ces matrices par les copies mises à jour (zero_copies)
    # afin de faire évoluer l'état. La boucle tourne pendant ~10 minutes.

    # Prépare les copies vides si nécessaire
    for bname in _building_names:
        if bname not in zero_copies:
            zero_copies[bname] = np.zeros((H, W), dtype=int)
        else:
            zero_copies[bname] = zero_copies[bname].copy()

    # current_matrices : sera utilisée pour construire les candidats à chaque itération
    current_matrices = {k: v.copy() for k, v in building_matrices.items()}

    # masque d'occupation : empêche de re-choisir la même case
    occupied = np.zeros((H, W), dtype=bool)
    # masque temporaire pour interdire une nouvelle destruction sur la même
    # case lors de l'itération suivante : neg_ban[bname][r,c] == True
    neg_ban = {b: np.zeros((H, W), dtype=bool) for b in _building_names}

    start_time = time.time()
    last_full_print = start_time
    iteration = 0
    DURATION = 15 * 60  # secondes

    # --- SKIP STRATEGY ---
    # --- SKIP STRATEGY ---
    # On utilise désormais une stratégie basée sur les scores pour décider
    # de sauter (eviter les biais de max-of-N). Options :
    #  - 'score_ratio'   : probabilité de saut basée sur le rapport
    #                      top/second_best (par défaut)
    #  - 'probabilistic' : probabilité fixe `SKIP_RATE` chaque itération
    #  - 'periodic'      : sauter toutes les `SKIP_PERIOD` itérations
    #
    # EXPLICATION SCORE_RATIO :
    # ------------------------
    # Le score MAX de l'itération est comparé au 2e meilleur score.
    # Si le ratio (MAX / 2e) est élevé, cela suggère que le MAX est un "outlier"
    # dû au hasard (tirage aléatoire). La stratégie calcule alors une probabilité
    # de SAUTER cette itération entièrement (continue dans la boucle).
    #
    # Formule : skip_prob = (1 - exp(-SKIP_ALPHA * (ratio-1))) * SKIP_AGGRESSIVITY
    # Plus le ratio est élevé, plus skip_prob est haute → plus de chances de sauter.
    #
    # RÉSULTAT : Même si le score MAX respecte les règles, il peut être IGNORÉ
    # par cette stratégie. L'itération est alors sautée (aucune action appliquée),
    # et on passe à l'itération suivante avec de nouveaux scores aléatoires.
    #
    SKIP_METHOD = 'score_ratio'    # 'score_ratio' | 'probabilistic' | 'periodic'
    SKIP_PERIOD = 10               # utilisé si SKIP_METHOD == 'periodic'
    SKIP_RATE = 0.10               # utilisé si SKIP_METHOD == 'probabilistic'
    # paramètres pour score_ratio
    SKIP_RATIO_EXP = 2.0           # exponent mapping ratio -> probability
    SKIP_MIN_SECOND = 1            # valeur minimale pour second best (évite division par 0)
    # Aggressivité supplémentaire : multiplie la probabilité calculée
    # (valeurs >1 augmentent la fréquence des sauts)
    SKIP_AGGRESSIVITY = 3.0
    # Paramètre pour la fonction exponentielle ratio->prob
    SKIP_ALPHA = 8.0

    while time.time() - start_time < DURATION:
        iteration += 1
        # start time for this iteration (used to ensure fixed spacing)
        iter_start = time.time()
        
        # --- CALCUL DES COMPTEURS ACTUELS (POUR LE FIX DÉMARRAGE) ---
        # On vérifie combien de bâtiments de ressource sont présents sur la carte (via zero_copies)
        # On utilise np.abs pour compter les 1 (construits) et ignorer les -1 (détruits) si présents par erreur
        current_sawmills = 0
        current_quarries = 0
        
        if 'sawmill' in zero_copies:
            # On compte les cases strictement positives (construit = 1)
            current_sawmills = np.sum(zero_copies['sawmill'] == 1)
            
        if 'quarry' in zero_copies:
            current_quarries = np.sum(zero_copies['quarry'] == 1)

        # Génère deux matrices de scores par bâtiment pour cette itération
        pos_scores = {}
        neg_scores = {}
        
        for bname in _building_names:
            # Génère deux matrices aléatoires 0..100000
            has_building = np.zeros((H, W), dtype=bool)
            for bb in _building_names:
                z = zero_copies.get(bb)
                if z is not None:
                    has_building |= (z == 1)

            pos = rng.integers(0, 100001, size=(H, W), dtype=int)
            neg = rng.integers(0, 100001, size=(H, W), dtype=int)

            # Neutraliser les cases occupées pour POS
            pos[has_building] = 0

            # Appliquer l'interdiction de destruction héritée (neg_ban)
            if neg_ban.get(bname) is not None and np.any(neg_ban[bname]):
                neg_ban[bname][:] = neg_ban[bname]

            # --- Filtrage par Rules.json (met à 0 les zones inconstructibles) ---
            if rules is not None:
                b_rules = rules.get('buildings', {}).get(bname, {})
                placement = b_rules.get('placement', {})

                # A. Interdire les tuiles explicites
                forbidden = placement.get('placementForbiddenTiles', [])
                if forbidden:
                    for r0 in range(H):
                        for c0 in range(W):
                            t = _detect_tile_at(tile_layers_data, r0, c0)
                            if t in forbidden:
                                pos[r0, c0] = 0
                                neg[r0, c0] = 0

                # B. Exiger l'adjacence
                if (not placement.get('placementAllowedAnywhere', True)) or placement.get('operatesIfAdjacentTo'):
                    required_adj_types = placement.get('placementRequiresAdjacentTile', []) + placement.get('operatesIfAdjacentTo', [])
                    if required_adj_types:
                        for r0 in range(H):
                            for c0 in range(W):
                                has_valid_neighbor = False
                                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    rr, cc = r0 + dr, c0 + dc
                                    if 0 <= rr < H and 0 <= cc < W:
                                        neigh_tile = _detect_tile_at(tile_layers_data, rr, cc)
                                        if neigh_tile in required_adj_types:
                                            has_valid_neighbor = True
                                            break
                                if not has_valid_neighbor:
                                    pos[r0, c0] = 0
                                    neg[r0, c0] = 0

            # =================================================================
            # --- FIX DÉMARRAGE À FROID (COLD START) ---
            # =================================================================
            # Si aucun collecteur de ressource n'est présent, on force un score
            # massif sur les emplacements valides pour garantir leur sélection.
            
            if bname == 'sawmill' and current_sawmills == 0:
                # On booste uniquement les cases valides (score > 0 après filtrage règles)
                valid_spots = pos > 0
                if np.any(valid_spots):
                    # Ajout de 1 million de points -> passe devant tout aléatoire (max 100k)
                    pos[valid_spots] += 1000000
                    # print(f"[IA DEBUG] BOOST PRIORITAIRE activé pour SCIERIE")

            if bname == 'quarry' and current_quarries == 0:
                valid_spots = pos > 0
                if np.any(valid_spots):
                    pos[valid_spots] += 1000000
                    # print(f"[IA DEBUG] BOOST PRIORITAIRE activé pour CARRIÈRE")
            # =================================================================

            # Matrice NEG finale (destruction uniquement là où le bâtiment existe)
            neg_final = np.zeros((H, W), dtype=int)
            zmat = zero_copies.get(bname)
            if zmat is not None:
                present_mask = (zmat == 1)
                if np.any(present_mask):
                    neg_final[present_mask] = neg[present_mask]

            # appliquer neg_ban
            if neg_ban.get(bname) is not None and np.any(neg_ban[bname]):
                neg_final[neg_ban[bname]] = 0
                neg_ban[bname][:] = False

            # Stocker les matrices filtrées
            pos_scores[bname] = pos
            neg_scores[bname] = neg_final
            globals()[f'pos_scores_{bname}'] = pos.copy()
            globals()[f'neg_scores_{bname}'] = neg_final.copy()

        # Conserver le concept d'une seule action par itération.
        final_outputs = {b: np.zeros((H, W), dtype=int) for b in _building_names}
        chosen = None

        # Construire la liste globale des candidats
        candidates = []
        for bname in _building_names:
            pos = pos_scores.get(bname)
            neg = neg_scores.get(bname)
            if pos is None or neg is None:
                continue
            for r in range(H):
                for c in range(W):
                    # construction
                    sval = int(pos[r, c])
                    if sval > 0:
                        candidates.append((sval, 1, bname, r, c))
                    # destruction
                    nval = int(neg[r, c])
                    if nval > 0:
                        candidates.append((nval, -1, bname, r, c))

        # Trier décroissant par score
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Tester un seul candidat
        if not candidates:
            chosen = None
        else:
            score, sign, b_try, r, c = candidates[0]
            
            # --- SKIP STRATEGY ---
            skip_action = False
            skip_reason = ''
            
            # IMPORTANT : On désactive le SKIP si on est en mode "Urgence Démarrage"
            # Si le score dépasse 500 000, c'est un boost artificiel, on ne saute pas !
            is_emergency_boost = (score > 500000)

            if not is_emergency_boost:
                if SKIP_METHOD == 'periodic':
                    if SKIP_PERIOD > 0 and iteration % SKIP_PERIOD == 0:
                        skip_action = True
                        skip_reason = f"périodique"
                elif SKIP_METHOD == 'probabilistic':
                    if rng.random() < SKIP_RATE:
                        skip_action = True
                        skip_reason = f"aléatoire"
                elif SKIP_METHOD == 'score_ratio':
                    if len(candidates) > 1:
                        second = int(candidates[1][0])
                    else:
                        second = SKIP_MIN_SECOND
                    second = max(second, SKIP_MIN_SECOND)
                    ratio = float(score) / float(second)
                    delta = max(0.0, ratio - 1.0)
                    skip_prob = 1.0 - math.exp(-SKIP_ALPHA * delta)
                    skip_prob = float(skip_prob) * float(SKIP_AGGRESSIVITY)
                    if skip_prob < 0.0: skip_prob = 0.0
                    elif skip_prob > 1.0: skip_prob = 1.0
                    
                    if rng.random() < skip_prob:
                        skip_action = True
                        skip_reason = f"score_ratio (r={ratio:.2f})"

            if skip_action:
                print(f"[Iter {iteration}] Saut de l'action ({skip_reason})")
                continue # Passe à l'itération suivante
            
            # --- FIN SKIP ---

            allowed = True
            # Double vérification Rules (redondante mais sécuritaire)
            if rules is not None:
                b_rules = rules.get('buildings', {}).get(b_try, {})
                placement = b_rules.get('placement', {})
                current_tile = _detect_tile_at(tile_layers_data, r, c)
                forbidden = placement.get('placementForbiddenTiles', [])
                if forbidden and current_tile in forbidden:
                    allowed = False
                if allowed and (not placement.get('placementAllowedAnywhere', True) or placement.get('operatesIfAdjacentTo')):
                    required_adj_types = placement.get('placementRequiresAdjacentTile', []) + placement.get('operatesIfAdjacentTo', [])
                    if not required_adj_types:
                        allowed = False
                    else:
                        has_valid_neighbor = False
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            rr, cc = r + dr, c + dc
                            if 0 <= rr < H and 0 <= cc < W:
                                neigh_tile = _detect_tile_at(tile_layers_data, rr, cc)
                                if neigh_tile in required_adj_types:
                                    has_valid_neighbor = True
                                    break
                        if not has_valid_neighbor:
                            allowed = False

            if not allowed:
                print(f"[Iter {iteration}] Candidat refusé: {b_try} at ({r+1},{c+1}) (rules)")
                chosen = None
            else:
                if sign == -1:
                    prev_mat = building_matrices.get(b_try)
                    prev_val = None
                    try:
                        if prev_mat is not None:
                            prev_val = int(prev_mat[r, c])
                    except Exception:
                        prev_val = None
                    # Vérification un peu lâche ici : on fait confiance à zero_copies via neg_final
                    final_outputs[b_try][r, c] = -1
                    chosen = (-score, b_try, r, c)
                else:
                    final_outputs[b_try][r, c] = 1
                    chosen = (score, b_try, r, c)

                if chosen is not None:
                    if sign == 1:
                        occupied[r, c] = True
                        for other in _building_names:
                            if other == b_try:
                                try: building_matrices[other][r, c] = 1
                                except: pass
                            else:
                                try: building_matrices[other][r, c] = 0
                                except: pass
                        zero_copies[b_try][r, c] = 1
                    else:
                        try: building_matrices[b_try][r, c] = -1
                        except: pass
                        zero_copies[b_try][r, c] = -1
                        try: occupied[r, c] = False
                        except: pass
                        try: neg_ban[b_try][r, c] = True
                        except: pass

        if chosen is not None:
            real_val, win_bname, win_r, win_c = chosen
            print(f"[Iter {iteration}] Gagnant: {win_bname} at ({win_r+1},{win_c+1}) val={real_val}")
        else:
            print(f"[Iter {iteration}] Aucun emplacement autorisé")

        try:
            _write_iteration_winner(iteration, chosen)
        except Exception as e:
            print(f"Erreur écriture iteration file: {e}")

        try:
            _save_batiment_snapshot_from_zero_copies(zero_copies)
        except Exception as e:
            print(f"Erreur écriture snapshot Batiment_Maps: {e}")

        now = time.time()
        if now - last_full_print >= 30 or now - start_time < 1:
            print("\n" + "="*60)
            print(f" ETAT COMPLET - Iteration {iteration} - elapsed {int(now-start_time)}s")
            print("="*60)
            # Affichage optionnel des matrices si besoin...
            last_full_print = now

        if chosen is not None:
            real_val, win_bname, win_r, win_c = chosen
            occupied[win_r, win_c] = True if real_val >= 0 else False
            sign = 1 if real_val >= 0 else -1
            try: zero_copies[win_bname][win_r, win_c] = sign
            except: pass
            try:
                for bname in _building_names:
                    if bname in pos_scores: pos_scores[bname][win_r, win_c] = 0
                    if bname in neg_scores: neg_scores[bname][win_r, win_c] = 0
            except: pass

        elapsed_iter = time.time() - iter_start
        sleep_time = max(0.0, float(ITERATION_DELAY) - elapsed_iter)
        if sleep_time > 0:
            print(f"[Iter {iteration}] Attente {sleep_time:.1f}s avant prochaine itération...")
            time.sleep(sleep_time)

    print(f"\nBoucle terminée après {DURATION} secondes ({iteration} itérations).")

    if chosen is None:
        print("\n>>> AUCUN EMPLACEMENT AUTORISÉ PAR LES RÈGLES pour les meilleurs candidats")
    # Nettoyage final : remettre à 0 toutes les marques -1 dans `zero_copies`
    # afin que l'on voie uniquement ce qui est construit à la fin.
    for bname in _building_names:
        z = zero_copies.get(bname)
        if z is not None:
            z[z < 0] = 0
            zero_copies[bname] = z

    # Afficher les matrices finales des bâtiments en -1/0/+1 seulement
    print("\n" + "="*60)
    print(" MATRICES FINALES DES BATIMENTS (valeurs réduites à -1/0/+1)")
    print("="*60)
    for bname in _building_names:
        mat_full = building_matrices.get(bname, np.zeros((H, W), dtype=int))
        # Afficher uniquement les positions construites (+1) —
        # les anciennes destructions (-1) sont remises à 0 pour la vue finale.
        mat_sign = np.zeros((H, W), dtype=int)
        mat_sign[mat_full > 0] = 1
        print(f"\n--- {bname} ---")
        print(mat_sign)
        nonzeros = list(zip(*np.nonzero(mat_sign)))
        if nonzeros:
            coords = ', '.join(f"({r+1},{c+1})" for r, c in nonzeros)
            print(f"Positions (1-based): {coords}")
        else:
            print("Positions (1-based): none")


if __name__ == "__main__":
    if not rules:
        print("Arrêt du script : fichier de règles manquant ou invalide.")