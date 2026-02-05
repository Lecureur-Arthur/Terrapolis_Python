import socket
import threading
import queue
import json
import time

class TerrapolisServer:
    def __init__(self, game_instance, host='0.0.0.0', port=5005):
        self.game = game_instance
        self.host = host
        self.port = port
        
        # Création du socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Permet de réutiliser l'adresse immédiatement après fermeture
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind((self.host, self.port))
        except Exception as e:
            print(f"Erreur liaison port {port}: {e}")
            
        self.sock.setblocking(False)
        
        self.running = True
        self.client_address = None # On stockera l'adresse du téléphone ici
        self.command_queue = queue.Queue()
        
        # Lancement du thread d'écoute
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"Serveur UDP démarré sur le port {port}")

    def _listen_loop(self):
        """Boucle d'écoute en arrière-plan."""
        while self.running:
            try:
                # Réception des paquets (Buffer 4096 bytes)
                data, addr = self.sock.recvfrom(4096)
                
                # On enregistre l'adresse du téléphone pour lui répondre (Broadcast)
                self.client_address = addr
                
                message = data.decode('utf-8').strip()
                
                # 1. Commande Simple
                if message == "READY":
                    self.command_queue.put({"command": "READY"})
                
                # 2. Commande JSON (Build/Destroy)
                elif message.startswith("{"):
                    try:
                        cmd_dict = json.loads(message)
                        self.command_queue.put(cmd_dict)
                    except json.JSONDecodeError:
                        print(f"JSON invalide reçu: {message}")
                        
            except BlockingIOError:
                # Rien reçu, on attend un peu pour ne pas surchauffer le CPU
                time.sleep(0.01)
            except Exception as e:
                if self.running:
                    print(f"Erreur réseau: {e}")

    def broadcast(self, message_str):
        """
        [MÉTHODE MANQUANTE AJOUTÉE]
        Envoie un message au téléphone connecté.
        """
        if self.client_address:
            try:
                self.sock.sendto(message_str.encode('utf-8'), self.client_address)
            except Exception as e:
                print(f"Erreur envoi broadcast: {e}")
        # else:
            # Personne n'est connecté, on ignore silencieusement

    def send_popup(self, level, title, message):
        """
        [MÉTHODE MANQUANTE AJOUTÉE]
        Envoie une commande d'affichage de popup au mobile.
        Format: POPUP|LEVEL|TITLE|MESSAGE
        """
        # On nettoie les pipes '|' pour éviter de casser le protocole
        safe_title = title.replace("|", "-")
        safe_msg = message.replace("|", "-").replace("\n", " ")
        
        formatted_msg = f"POPUP|{level}|{safe_title}|{safe_msg}"
        self.broadcast(formatted_msg)

    def stop(self):
        """Arrête proprement le serveur."""
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        print("Serveur réseau arrêté.")