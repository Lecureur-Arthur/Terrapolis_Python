import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
import os
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter
from terrapolis_logic import TerrapolisGame, MAP_H, MAP_W, TOTAL_STEPS, BUILDINGS

class CityCNN(nn.Module):
    def __init__(self, conf):
        super(CityCNN, self).__init__()
        self.path_save = conf["path_save"]
        
        # Entrée CNN : 4 Terrains + Batiments + Occupé
        self.num_buildings = len(BUILDINGS)
        input_channels = 4 + self.num_buildings + 1
        
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        self.flatten_size = 128 * MAP_H * MAP_W
        
        # Entrée Dense : Flatten Map + 2 scalaires (Bois, Pierre)
        self.fc1 = nn.Linear(self.flatten_size + 2, 256)
        
        # --- AJOUT DROPOUT ---
        # p=0.3 signifie que 30% des neurones sont désactivés aléatoirement à chaque passage d'apprentissage
        self.dropout = nn.Dropout(p=0.3)
        
        self.fc2 = nn.Linear(256, 1) # Value Function


    def forward(self, map_tensor, res_tensor):
        x = F.relu(self.conv1(map_tensor))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        
        x = x.view(x.size(0), -1) # Flatten
        x = torch.cat((x, res_tensor), dim=1) 

        x = F.relu(self.fc1(x))
        
        # --- APPLICATION DU DROPOUT ---
        x = self.dropout(x)
        
        return self.fc2(x)

    def encode_state(self, game):
        layers = []
        # Terrains
        layers.append(game.mountain_mask)
        layers.append(game.forest_mask)
        layers.append(game.river_mask)
        layers.append(game.plain_mask)
        
        # Batiments
        for b_name in BUILDINGS.keys():
            layer = np.zeros((MAP_H, MAP_W))
            layer[game.grid_types == b_name] = 1.0
            layers.append(layer)
            
        # Occupation
        layers.append(game.occupied_mask.astype(float))
        
        np_layers = np.array(layers, dtype=np.float32)
        map_tensor = torch.tensor(np_layers).unsqueeze(0) 
        res_tensor = torch.tensor([[game.wood/1000.0, game.stone/1000.0]], dtype=torch.float32)
        return map_tensor, res_tensor

    def train_self_play(self, num_episodes, device, optimizer, start_epsilon=1.0, gamma=0.99):
        """
        Entraînement avec GAMMA, DROPOUT et Intervalle de Confiance.
        """
        if not os.path.exists(self.path_save): os.makedirs(self.path_save)
        
        # Nom explicite pour TensorBoard
        run_name = f"runs/Training_AI_Gamma_Dropout_0.3"
        writer = SummaryWriter(run_name)

        loss_fn = nn.HuberLoss(delta=1.0) 
        epsilon = start_epsilon

        all_scores = []
        best_overall_score = -float('inf')

        print(f"--> Demarrage : Gamma {gamma} | Dropout 30% | Epsilon {epsilon}")
        
        for episode in tqdm(range(1, num_episodes+1)):
            game = TerrapolisGame() 
            memory = []
            
            # MODE JEU : On désactive le Dropout pour jouer le mieux possible
            self.eval() 
            
            while game.turn < TOTAL_STEPS:
                actions = game.get_legal_actions()
                if not actions: break
                
                # --- Epsilon Greedy ---
                if random.random() < epsilon:
                    chosen = random.choice(actions)
                    virtual = game.copy(); virtual.step(chosen)
                    mt, rt = self.encode_state(virtual)
                else:
                    sample = actions if len(actions)<60 else random.sample(actions, 60)
                    batch_m, batch_r = [], []
                    for a in sample:
                        v = game.copy(); v.step(a)
                        m, r = self.encode_state(v)
                        batch_m.append(m); batch_r.append(r)
                    
                    if batch_m:
                        bm = torch.cat(batch_m).to(device)
                        br = torch.cat(batch_r).to(device)
                        with torch.no_grad():
                            preds = self(bm, br)
                        best_idx = torch.argmax(preds).item()
                        chosen = sample[best_idx]
                        mt, rt = batch_m[best_idx], batch_r[best_idx]
                    else:
                        chosen = ("WAIT", -1, -1)
                        mt, rt = self.encode_state(game)

                game.step(chosen)
                memory.append({'m': mt, 'r': rt})
            
            final_raw_score = game.virtuosity - game.pollution_total
            all_scores.append(final_raw_score)

            if final_raw_score > best_overall_score:
                best_overall_score = final_raw_score
                torch.save(self, f"{self.path_save}/model_best.pt")
                if episode % 10 == 0: 
                    tqdm.write(f"[*] NOUVEAU RECORD : {int(best_overall_score)}")

            # =========================================================
            # === APPLICATION DU GAMMA (Discounted Returns) ===
            # =========================================================
            discounted_returns = []
            R = final_raw_score
            
            # On remonte le temps : Score Final * Gamma^t
            for _ in range(len(memory)):
                discounted_returns.insert(0, R)
                R = R * gamma
            
            targets_tensor = torch.tensor(discounted_returns, device=device).unsqueeze(1).float()
            # =========================================================

            # --- APPRENTISSAGE ---
            loss_val = 0
            if memory:
                # MODE ENTRAINEMENT : On active le Dropout pour apprendre de manière robuste
                self.train() 
                
                batch_m = torch.cat([x['m'] for x in memory]).to(device)
                batch_r = torch.cat([x['r'] for x in memory]).to(device)
                
                optimizer.zero_grad()
                preds = self(batch_m, batch_r)
                
                loss = loss_fn(preds, targets_tensor)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
                optimizer.step()
                loss_val = loss.item()
            
            if epsilon > 0.01: epsilon *= 0.998
            
            # =========================================================
            # === TENSORBOARD UNIFIÉ ===
            # =========================================================
            
            # 1. Infos Brutes
            writer.add_scalar('Training/Score', final_raw_score, episode)
            writer.add_scalar('Training/Loss', loss_val, episode)
            writer.add_scalar('Training/Epsilon', epsilon, episode)

            # 2. Analyse Groupée (Moyenne + Intervalle Confiance)
            if len(all_scores) >= 10:
                recent_scores = all_scores[-100:]
                avg_100 = np.mean(recent_scores)
                
                # Ancienne courbe seule
                writer.add_scalar('Training/AvgScore_100', avg_100, episode)
                
                # Nouvelle courbe groupée
                std_recent = np.std(recent_scores)
                n = len(recent_scores)
                margin_error = 1.96 * (std_recent / np.sqrt(n))
                
                writer.add_scalars('Analysis/Performance', {
                    'Moyenne_Avg100': avg_100,
                    'Borne_Haute_95': avg_100 + margin_error,
                    'Borne_Basse_95': avg_100 - margin_error
                }, episode)
            
            # =========================================================

            if episode % 10 == 0:
                print(f"Ep {episode} | Score: {int(final_raw_score)} | Loss: {loss_val:.2f} | Eps: {epsilon:.2f}")
                
            if episode % 50 == 0:
                torch.save(self, f"{self.path_save}/model_latest.pt")
                writer.flush()

        writer.close()

        # --- BILAN ---
        scores_arr = np.array(all_scores)
        count_above = np.sum(scores_arr > 50000)
        total = len(scores_arr)
        
        if total > 0:
            pct = (count_above / total) * 100.0
            print("\n" + "="*60)
            print("             BILAN FINAL")
            print("="*60)
            print(f"SCORE MOYEN       : {np.mean(scores_arr):.0f}")
            print(f"MEILLEUR SCORE    : {np.max(scores_arr):.0f}")
            print(f"PARTIES > 50k     : {pct:.2f}%")
            print("="*60 + "\n")