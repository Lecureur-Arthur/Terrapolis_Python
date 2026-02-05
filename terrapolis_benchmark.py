import random
import time
import numpy as np
from tqdm import tqdm
import sys

# Importation sécurisée
try:
    from terrapolis_logic import TerrapolisGame, TOTAL_STEPS
except ImportError:
    print("❌ ERREUR : 'terrapolis_logic.py' est introuvable.")
    sys.exit()

def run_benchmark():
    print("\n" + "="*60)
    print("      BENCHMARK IA ALÉATOIRE (1000 PARTIES)")
    print("="*60)
    
    NUM_EPISODES = 1000
    all_scores = []
    wins = 0
    
    start_time = time.time()

    # Barre de chargement
    for i in tqdm(range(NUM_EPISODES), desc="Simulation"):
        game = TerrapolisGame()
        
        while game.turn < TOTAL_STEPS:
            actions = game.get_legal_actions()
            if not actions: break
            
            # --- IA DUMB : CHOIX ALÉATOIRE ---
            action = random.choice(actions)
            game.step(action)
        
        final_score = game.virtuosity - game.pollution_total
        all_scores.append(final_score)
        if final_score > 0: wins += 1

    # --- RÉSULTATS ---
    scores_arr = np.array(all_scores)
    avg = np.mean(scores_arr)
    
    print("\n" + "="*60)
    print("           RÉSULTATS FINAUX")
    print("="*60)
    print(f"TEMPS TOTAL       : {time.time() - start_time:.2f} secondes")
    print("-" * 60)
    print(f"SCORE MOYEN       : {avg:.0f}  <-- LA RÉFÉRENCE")
    print(f"MEILLEUR SCORE    : {int(np.max(scores_arr))}")
    print(f"PIRE SCORE        : {int(np.min(scores_arr))}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_benchmark()