# Terrapolis - Moteur de Simulation & IA

**Terrapolis** est un moteur de simulation de gestion urbaine et de ressources développé en Python. Conçu comme une architecture modulaire, il combine une boucle de rendu temps réel (Pygame), une couche réseau UDP et des modules d'Intelligence Artificielle hybrides (CNN + Heuristiques).

Ce dépôt contient le code source du moteur ("Back-end logic"), les assets graphiques 2D, ainsi que les modèles d'IA pré-entraînés.

## Écosystème & Client Mobile

Ce projet fonctionne en architecture **Client-Serveur**.

* **Ce dépôt (Serveur/Engine)** : Gère la logique, l'IA, la simulation et la sauvegarde des données.
* **Le dépôt Mobile (Client)** : Application de visualisation en Réalité Augmentée (AR) développée sous Unity.

L'application mobile se connecte à ce moteur via UDP pour envoyer les commandes de l'utilisateur et recevoir l'état de la ville en temps réel.

> **Accéder au dépôt Client Mobile (Unity) :**
> [ **Lien vers le repo Terrapolis Mobile** ]
 
---

## Architecture Technique

Le projet est structuré autour de quatre piliers fondamentaux : le **Core Loop**, le **State Manager**, l'**Interface Réseau** et le **Module IA**.

### 1. Core & Rendu (Engine)

Le moteur graphique repose sur `pygame`.

* **`main.py`** : Point d'entrée. Initialise les sous-systèmes et lance la boucle principale.
* **`engine.py`** : Chef d'orchestre visuel et événementiel.
    * Gère la boucle `run()` (Update/Draw).
    * Traite les interruptions locales (Clavier/Souris).
    * Synchronise l'état logique (`terrapolis_logic`) avec le rendu visuel local.



### 2. Réseau & I/O (UDP)

* **`network.py`** : Serveur UDP multithreadé (Port `5005` par défaut).
    * **Rôle** : Passerelle bidirectionnelle avec le **Client Mobile Unity**.
    * **Flux** :
        * *Input (Client -> Python)* : Commandes de placement, destruction, interactions UI.
        * *Output (Python -> Client)* : Sérialisation de la matrice d'état (Grid) et update des scores.


    * Exécuté dans un thread démon pour assurer une simulation fluide côté Python, indépendamment de la latence réseau.



### 3. Logique de Simulation (State Management)

La logique métier est découplée du rendu.

* **`terrapolis_logic.py`** : Contient la classe `TerrapolisGame`.
    * Gère la grille (Grid System) et la matrice d'état.
    * Calcule les métriques en temps réel : Pollution, Score de Virtuosité, Production.
    * Gère les événements stochastiques (inondations, catastrophes).


* **`terrain_data.py`** : Base de données topographique statique (Numpy) définissant les biomes.

### 4. Système Data-Driven

* **`rules_manager.py`** & **`Rules.json`** : Configuration externalisée.
    * Les coûts, productions, pollutions et contraintes d'adjacence sont injectés au démarrage.
    * Permet un équilibrage rapide sans recompilation, impactant simultanément le moteur Python et les données renvoyées au mobile.



---

## Intelligence Artificielle

Le projet utilise une approche hybride pour l'aide à la décision (conseil au joueur mobile) et l'automatisation.

### Architecture des Modèles

* **`terrapolis_models.py` (PyTorch)** :
    * Définit l'architecture **CityCNN**.
    * Traite la grille de jeu comme une image multi-canaux (Terrain, Bâtiments, Pollution).
    * Utilisé pour l'apprentissage par renforcement (RL) et l'évaluation globale de la ville.


* **`map.py` (Analyse Heuristique)** :
    * Utilise des convolutions manuelles pour générer des "Heatmaps" d'attractivité.
    * Détermine les meilleurs emplacements de construction basés sur les règles de voisinage immédiat.



### Agents

* **`IA_Dumb.py`** : Agent de base (Baseline) effectuant des actions aléatoires ou scriptées. Sert aux tests de robustesse et de charge du réseau UDP.

---

## Structure du Projet

```text
Terrapolis_Python
├── engine.py                 # Moteur graphique et boucle d'événements
├── main.py                   # Point d'entrée
├── network.py                # Serveur UDP (Interface avec l'App Mobile)
├── rules_manager.py          # Parser de règles JSON
├── terrapolis_logic.py       # Logique métier (State Machine)
├── terrapolis_models.py      # Architecture Réseaux de Neurones (Torch)
├── map.py                    # Analyseur de carte (Matrices de score)
├── IA_Dumb.py                # IA de test (Baseline)
├── Rules.json                # Configuration du Gameplay (Data)
│
├── Assets/                   # Sprites 2D (.png)
├── Batiment_Maps/            # Templates et états initiaux (Txt)
├── save_terrapolis_models/   # Checkpoints IA (.pt)
└── Terrapolis_Save/          # Sauvegardes de session (Logs/Pickle)

```

---

## Installation et Démarrage

### Pré-requis

Le projet nécessite **Python 3.10** ou supérieur.
Il est vivement recommandé d'utiliser **Conda** (Anaconda ou Miniconda) pour gérer l'environnement, afin de faciliter l'installation des librairies scientifiques (PyTorch, Numpy).

### Configuration de l'environnement

1. **Création de l'environnement Conda** :
```bash
conda create -n terrapolis_env python=3.12.7
conda activate terrapolis_env

```


2. **Installation des dépendances** :
Installez PyTorch via le canal officiel (recommandé pour la gestion des drivers), puis les autres librairies :
```bash
# Installation de PyTorch et Torchvision
conda install pytorch torchvision -c pytorch

# Installation du moteur graphique et des utilitaires
pip install pygame numpy
```



### Lancement

Pour démarrer le serveur de jeu :

```bash
python main.py
```

Le moteur lance l'interface graphique locale et ouvre le socket UDP sur le port `5005`. Assurez-vous que l'appareil exécutant l'application mobile est sur le même réseau local et pointe vers l'IP de cette machine.

---

## 📝 Auteur & Crédits

**Projet Terrapolis**
Développé dans le cadre du projet de recherche et développement Terrapolis.

* **Moteur & Logique :** Python / Pygame ***[LECUREUR Arthur]***
* **IA & Data :** PyTorch / Numpy ***[PLATET Thibaut]***
* **Client Mobile AR :** Unity / C# (Voir dépôt associé) ***[TOURNAY Clara | LECRUEUR Arthur]***