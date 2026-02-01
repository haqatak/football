import json
import os
import glob

TEAMS_DIR = os.path.join(os.path.dirname(__file__), 'teams')

PLAYER_STATS_NAMES = [
    "physical_balance", "physical_reaction", "physical_acceleration", "physical_velocity",
    "physical_stamina", "physical_agility", "physical_shotpower",
    "technical_standingtackle", "technical_slidingtackle", "technical_ballcontrol",
    "technical_dribble", "technical_shortpass", "technical_highpass",
    "technical_header", "technical_shot", "technical_volley",
    "mental_calmness", "mental_workrate", "mental_resilience",
    "mental_defensivepositioning", "mental_offensivepositioning", "mental_vision"
]

PLAYER_ROLES = [
    "GK", "CB", "LB", "RB", "DM", "CM", "LM", "RM", "AM", "CF"
]

DEFAULT_PLAYER = {
    "role": "CM",
    "x": 0.0,
    "y": 0.0,
    "kit_no": 1,
    "stats": [0.5] * 22
}

def ensure_teams_dir():
    if not os.path.exists(TEAMS_DIR):
        os.makedirs(TEAMS_DIR)

def list_teams():
    ensure_teams_dir()
    files = glob.glob(os.path.join(TEAMS_DIR, "*.json"))
    return [os.path.splitext(os.path.basename(f))[0] for f in files]

def load_team(name):
    path = os.path.join(TEAMS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def save_team(name, team_data):
    ensure_teams_dir()
    path = os.path.join(TEAMS_DIR, f"{name}.json")
    with open(path, 'w') as f:
        json.dump(team_data, f, indent=2)

def delete_team(name):
    path = os.path.join(TEAMS_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
