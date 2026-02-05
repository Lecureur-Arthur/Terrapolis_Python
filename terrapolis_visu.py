import torch
import numpy as np
import os
import sys

# --- IMPORT LOGIQUE ---
try:
    import terrapolis_logic as game_logic
    from terrapolis_logic import TerrapolisGame, MAP_H, MAP_W, TOTAL_STEPS
    # On importe votre classe CityCNN pour que torch.load la reconnaisse
    from terrapolis_models import CityCNN 
except ImportError as e:
    print(f"❌ ERREUR D'IMPORT : {e}")
    sys.exit()

# --- CONFIGURATION ---
MODEL_PATH = "save_terrapolis_models/model_latest.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"--- Tentative de chargement : {MODEL_PATH} ---")

if not os.path.exists(MODEL_PATH):
    print(f"❌ ERREUR : Le fichier '{MODEL_PATH}' n'existe pas.")
    sys.exit()

# --- CHARGEMENT DU MODÈLE ---
try:
    # On charge l'objet complet car vous avez utilisé torch.save(self)
    # weights_only=False est nécessaire ici car on charge une structure de classe
    model = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
    model.eval() # Mode lecture seule
    print("✅ Modèle CityCNN chargé avec succès !")
except Exception as e:
    print(f"❌ ERREUR CRITIQUE : Impossible de charger le modèle.\n{e}")
    sys.exit()

# --- INITIALISATION JEU ---
game = TerrapolisGame()

print(f"\n--- DÉBUT PARTIE (Tour 0 à {TOTAL_STEPS}) ---")
print(f"Ressources Départ -> Bois: {int(game.wood)} | Pierre: {int(game.stone)}")

# --- BOUCLE DE JEU ---
for turn in range(TOTAL_STEPS):
    
    actions = game.get_legal_actions()
    
    # Si pas d'actions (bloqué), on arrête
    if not actions:
        print("AUCUNE ACTION POSSIBLE.")
        break

    best_action = None
    best_score = -float('inf')

    # --- SIMULATION ---
    for action in actions:
        # 1. On copie le jeu pour ne pas toucher au vrai
        virtual_game = game.copy()
        
        # 2. On joue l'action (en SILENCE, verbose=False)
        virtual_game.step(action, verbose=False)
        
        # 3. On demande au modèle : "Combien vaut cette situation ?"
        # Votre méthode encode_state renvoie (map_tensor, res_tensor)
        m_tensor, r_tensor = model.encode_state(virtual_game)
        
        # Passage sur GPU si besoin
        m_tensor = m_tensor.to(DEVICE)
        r_tensor = r_tensor.to(DEVICE)

        with torch.no_grad():
            predicted_score = model(m_tensor, r_tensor).item()
        
        # 4. On garde le meilleur score
        if predicted_score > best_score:
            best_score = predicted_score
            best_action = action

    # --- AFFICHAGE & EXÉCUTION RÉELLE ---
    
    # On affiche la prédiction (sauf si c'est WAIT pour ne pas spammer, sauf au début)
    if best_action[0] != "WAIT" or turn < 3:
        print(f"T{turn}: {best_action} (Score Prédit: {int(best_score)})")

    # On joue le coup pour de vrai, AVEC LES EMOJIS (verbose=True)
    game.step(best_action, verbose=True)


# --- RÉSULTATS FINAUX ---
print("\n=== FIN DE LA PARTIE ===")
print(f"SCORE RÉEL : {int(game.virtuosity - game.pollution_total)}")
print(f"Virtuosité : {int(game.virtuosity)}")
print(f"Pollution  : {int(game.pollution_total)}")
print(f"Ressources : Bois {int(game.wood)} | Pierre {int(game.stone)}")

print("\n--- Carte Finale ---")
symbols = {
    "sawmill": "S", "quarry": "Q", "residence": "R", 
    "wind_turbine": "W", "coal_plant": "C", "nuclear_plant": "N",
    "": "."
}

# Affichage de la grille
for r in range(MAP_H):
    line = ""
    for c in range(MAP_W):
        b_type = game.grid_types[r, c]
        if b_type != "":
            char = symbols.get(b_type, "?")
        else:
            if game.mountain_mask[r, c]: char = "^"
            elif game.forest_mask[r, c]: char = "T"
            elif game.river_mask[r, c]: char = "~"
            else: char = "."
        line += char + " "
    print(line)


# --- LÉGENDE DE LA CARTE ---
print("-" * 30)
print("       LÉGENDE CARTE")
print("-" * 30)
print(" [S] = Scierie        [C] = Carrière")
print(" [H] = Habitation     [E] = Éolienne")
print(" [U] = Usine Charbon  [N] = Centrale Nucléaire")
print("-" * 30)
print(" [^] = Montagne       [*] = Forêt")
print(" [~] = Rivière        [.] = Plaine")
print("-" * 30)

# --- BILAN STATISTIQUE ---
print("\n" + "="*50)
print("       📊 BILAN DES OPÉRATIONS 📊")
print("="*50)

print(f"\n🏗️  CONSTRUCTIONS TOTALES : {sum(game.stats_built.values())}")
if game.stats_built:
    for b_name, count in game.stats_built.items():
        print(f"   - {b_name}: {count}")
else:
    print("   (Rien)")

total_destroyed_player = sum(game.stats_lost_player.values())
if total_destroyed_player > 0:
    print(f"\n🧨  DÉTRUITS PAR L'IA : {total_destroyed_player}")
    for b_name, count in game.stats_lost_player.items():
        print(f"   - {b_name}: {count}")
else:
    print("\n🧨  DÉTRUITS PAR L'IA : 0")

total_lost_flood = sum(game.stats_lost_flood.values())
if total_lost_flood > 0:
    print(f"\n🌊  PERDUS PAR INONDATION : {total_lost_flood}")
    for b_name, count in game.stats_lost_flood.items():
        print(f"   - {b_name}: {count}")
else:
    print("\n🌊  PERDUS PAR INONDATION : 0")

print("="*50)