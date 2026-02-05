import sys
import torch
import torch.nn as nn  # <--- Il faut importer nn pour lister les calques
import engine
from terrapolis_models import CityCNN

if __name__ == "__main__":
    try:
        # ✅ FIX COMPLET : On autorise CityCNN ET ses composants internes
        # PyTorch 2.6 vérifie récursivement chaque objet dans le fichier
        torch.serialization.add_safe_globals([
            CityCNN,        # Ton IA
            nn.Conv2d,      # Tes couches de convolution
            nn.Linear,      # Tes couches linéaires (fully connected)
            nn.Dropout,     # Ta couche de dropout
            nn.ReLU         # Juste au cas où (parfois stocké comme module)
        ])

        game_instance = engine.Game()
        game_instance.run()
    except KeyboardInterrupt:
        sys.exit()