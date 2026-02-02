import socket
import threading
import queue

# Configuration
UDP_IP = "0.0.0.0" # Écoute tout le monde
UDP_PORT = 5005

class TerrapolisServer:
    def __init__(self, game_engine):
        self.game = game_engine
        # Création du socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Liaison au port
        try:
            self.sock.bind((UDP_IP, UDP_PORT))
            print(f"[RÉSEAU] Serveur UDP démarré sur le port {UDP_PORT}")
        except Exception as e:
            print(f"[RÉSEAU] Erreur de démarrage (Port occupé ?): {e}")

        self.running = True
        self.command_queue = queue.Queue() # File d'attente pour parler au Thread principal
        
        # Démarrer le thread d'écoute en arrière-plan
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True # Se ferme quand le jeu se ferme
        self.thread.start()
        

    def _listen_loop(self):
        while self.running:
            try:
                # Cette ligne attend un message (bloquante), d'où l'utilisation d'un Thread
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                
                # On ajoute le message dans la file pour que engine.py le traite
                self.command_queue.put((message, addr))
            except Exception as e:
                # Ignorer les erreurs de fermeture
                if self.running:
                    print(f"[RÉSEAU] Erreur écoute: {e}")

    def send_to(self, message, addr):
        try:
            self.sock.sendto(message.encode('utf-8'), addr)
        except Exception as e:
            print(f"[RÉSEAU] Erreur envoi: {e}")
            
    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass