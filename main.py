# main.py
import sys
import engine

if __name__ == "__main__":
    try:
        game_instance = engine.Game()
        game_instance.run()
    except KeyboardInterrupt:
        sys.exit()