# rules_manager.py
import json
import os
import sys
# On n'a plus besoin d'importer settings ici car on ne lit plus les couleurs

class RulesLoader:
    @staticmethod
    def load(filename="Rules.json"):
        if not os.path.exists(filename):
            print(f"ERREUR CRITIQUE: '{filename}' introuvable !")
            sys.exit()

        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        adj_modifiers = data["common"]["adjacentModifiers"]
        buildings_rules = {}
        
        for key, b_data in data["buildings"].items():
            placement = b_data.get("placement", {})
            construction = b_data.get("construction", {})
            production = b_data.get("production", {})
            operation = b_data.get("operation", {})
            events = b_data.get("events", {})
            additional = b_data.get("additionalInstances", {})
            
            cost_dict = additional.get("cost", construction.get("cost", {"wood": 0, "stones": 0}))
            
            needs_adj = placement.get("operatesIfAdjacentTo") or None
            req_adj = placement.get("placementRequiresAdjacentTile") or None
            poll_spread_sec = operation.get("pollutionSpreadAfterSec") or 0
            poll_river_sec = operation.get("pollutesRiverAfterSec") or 0
            rate = production.get("ratePerSec", 0)
            loss_on_destroy = events.get("onPlayerDestroy", {}).get("loseVirtuosityAmount", construction.get("virtuosityGain", 0))
            flood_rules = events.get("onFlood", {})

            rule = {
                "name": b_data.get("displayName", key),
                "first_free": b_data.get("firstFree", False),
                "forbidden": placement.get("placementForbiddenTiles", []),
                "needs_adj_terrain": needs_adj,
                "requires_adj_terrain": req_adj,
                "cost": cost_dict,
                "production": {
                    "resource": production.get("resource"),
                    "amount": rate,
                    "tile_yield": production.get("adjacentTileYield", {})
                },
                "pollution_on_build": construction.get("pollutionOnBuild", 0),
                "virtuosity_on_build": construction.get("virtuosityGain", 0),
                "virtuosity_loss_on_destroy": loss_on_destroy,
                "emits_per_sec": operation.get("emitsPerSec", 0),
                "virtuosity_per_sec": operation.get("virtuosityPerSec", 0),
                "spreads_pollution": operation.get("affectsAdjacentTiles", False),
                "pollution_spread_after_sec": poll_spread_sec,
                "river_pollution_amount": operation.get("riverPollutionAmount", 0),
                "pollutes_river_after_sec": poll_river_sec,
                "on_flood": {
                    "destroyed": flood_rules.get("destroyed", False),
                    "floodScoreIncrease": flood_rules.get("floodScoreIncrease", 0)
                }
            }
            buildings_rules[key] = rule

        return buildings_rules, adj_modifiers

BUILDING_RULES, ADJACENT_MODIFIERS = RulesLoader.load()