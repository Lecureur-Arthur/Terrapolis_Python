import torch
import torch.nn as nn
import os
from terrapolis_models import CityCNN

# ===========================
# CONFIGURATION
# ===========================
conf = {}
conf["path_save"] = "save_terrapolis_models"
conf["batch_size"] = 64
conf["lr"] = 0.001       
conf["weight_decay"] = 1e-5
conf["episodes"] = 1500  

# Gestion du GPU
if torch.cuda.is_available():
    device = torch.device("cuda:0")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("CPU")

# ===========================
# LOGIQUE DE REPRISE (LOAD)
# ===========================
model_path = os.path.join(conf["path_save"], "model_latest.pt")
model = None
start_epsilon = 1.0  

if os.path.exists(model_path):
    print(f"--- REPRISE : Chargement du cerveau existant ({model_path}) ---")
    try:
        model = torch.load(model_path, map_location=device, weights_only=False)
        
        # --- CORRECTION DE L'ERREUR : AJOUT MANUEL DU DROPOUT ---
        # Si le vieux modèle n'a pas la couche 'dropout', on la lui ajoute de force.
        if not hasattr(model, 'dropout'):
            print("⚠️ ATTENTION : Vieux modèle détecté sans Dropout. Ajout de la couche manquante...")
            model.dropout = nn.Dropout(p=0.3).to(device)
        # --------------------------------------------------------

        model.eval() 
        start_epsilon = 0.4 
        print(f"Modèle chargé avec succès ! Epsilon réglé à {start_epsilon}")

    except Exception as e:
        print(f"Erreur chargement: {e}. On repart de zéro.")
        model = None
        start_epsilon = 1.0 

if model is None:
    print("--- NOUVEAU : Création d'un cerveau vierge ---")
    model = CityCNN(conf).to(device)
    start_epsilon = 1.0
    print(f"Modèle vierge créé. Epsilon réglé à {start_epsilon}")

# Optimiseur
optimizer = torch.optim.Adam(
    model.parameters(), 
    lr=conf["lr"], 
    weight_decay=conf["weight_decay"]
)

# ===========================
# LANCEMENT
# ===========================
print("Démarrage de l'entraînement...")

model.train_self_play(conf["episodes"], device, optimizer, start_epsilon=start_epsilon)

print("Entraînement terminé.")