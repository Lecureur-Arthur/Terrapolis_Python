import random
import time
import numpy as np
from tqdm import tqdm
import sys
from torch.utils.tensorboard import SummaryWriter

# Importation sécurisée
try:
    from terrapolis_logic import TerrapolisGame, TOTAL_STEPS
    try:
        from terrapolis_logic import MAP_H, MAP_W, BUILDINGS
    except ImportError:
        MAP_H, MAP_W = 10, 15
        BUILDINGS = ['sawmill', 'quarry', 'coal_plant', 'wind_turbine', 'nuclear_plant', 'residence']
except ImportError:
    print("❌ ERREUR : 'terrapolis_logic.py' est introuvable.")
    sys.exit()

def run_benchmark():
    print("\n" + "="*60)
    print("      BENCHMARK IA ALÉATOIRE (AVG100 + INTERVALLE)")
    print("="*60)
    
    run_name = f"runs/Random_Agent"

    writer = SummaryWriter(run_name)
    print(f"--> Logs TensorBoard : {run_name}")

    NUM_EPISODES = 1500
    all_scores = []
    
    start_time = time.time()

    # Barre de progression
    for i in tqdm(range(NUM_EPISODES), desc="Simulation Filtrée"):
        game = TerrapolisGame()
        
        while game.turn < TOTAL_STEPS:
            legal_actions = game.get_legal_actions()
            if not legal_actions: break
            
            action = random.choice(legal_actions)
            game.step(action)
        
        final_score = game.virtuosity - game.pollution_total
        all_scores.append(final_score)

        # =========================================================
        # === TENSORBOARD : AVG100 + INTERVALLE ===
        # =========================================================
        
        # 1. Score
        writer.add_scalar('Training/Score', final_score, i)

        # 2. La Moyenne Glissante (L'ESSENTIEL)
        # On calcule la moyenne des 100 dernières parties
        if len(all_scores) >= 10:
            recent_scores = all_scores[-100:]
            avg_100 = np.mean(recent_scores)
            
            # --- COURBE CLASSIQUE (Celle que vous aviez avant) ---
            writer.add_scalar('Training/AvgScore_100', avg_100, i)

            # --- COURBE GROUPÉE (Moyenne au milieu + Bornes autour) ---
            std_recent = np.std(recent_scores)
            n = len(recent_scores)
            margin_error = 1.96 * (std_recent / np.sqrt(n))
            
            # Ici, on trace 3 lignes sur le MÊME graphique
            writer.add_scalars('Analysis/Performance', {
                'Moyenne_Avg100': avg_100,             # La ligne centrale
                'Borne_Haute_95': avg_100 + margin_error,
                'Borne_Basse_95': avg_100 - margin_error
            }, i)
        
        # =========================================================

        if i % 50 == 0: writer.flush()

    writer.close()

    # --- RÉSULTATS CONSOLE ---
    scores_arr = np.array(all_scores)
    avg = np.mean(scores_arr)
    std = np.std(scores_arr)
    n = len(scores_arr)
    
    margin_error = 1.96 * (std / np.sqrt(n))
    ci_lower = avg - margin_error
    ci_upper = avg + margin_error
    
    print("\n" + "="*60)
    print("           RÉSULTATS FINAUX")
    print("="*60)
    print(f"TEMPS TOTAL       : {time.time() - start_time:.2f} s")
    print("-" * 60)
    print(f"SCORE MOYEN       : {avg:.0f}")
    print(f"INTERVALLE 95%    : [{ci_lower:.2f}, {ci_upper:.2f}]")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_benchmark()