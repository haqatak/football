import streamlit as st
import numpy as np
from gfootball.ui import team_repository
from gfootball.env import custom_team
from gfootball.env import scenario_builder
import gfootball.env as football_env
import time

st.set_page_config(page_title="GFootball Team Editor", layout="wide")

st.title("Google Research Football - Team Designer")

# Sidebar for Navigation
page = st.sidebar.selectbox("Navigate", ["Team Editor", "Match Simulation"])

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)]

def rgb_to_hex(rgb_color):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]*255), int(rgb_color[1]*255), int(rgb_color[2]*255))

if page == "Team Editor":
    st.header("Create / Edit Team")

    # Load existing teams
    teams = team_repository.list_teams()
    selected_team_name = st.selectbox("Select Team to Edit", ["Create New"] + teams)

    team_data = {
        "name": "New Team",
        "kit_color": [0.9, 0.1, 0.1],
        "shorts_color": [0.1, 0.1, 0.9],
        "players": []
    }

    if selected_team_name != "Create New":
        loaded = team_repository.load_team(selected_team_name)
        if loaded:
            team_data = loaded

    # Team Details
    col1, col2, col3 = st.columns(3)
    with col1:
        team_name = st.text_input("Team Name", team_data["name"])
    with col2:
        kit_color_hex = st.color_picker("Jersey Color", rgb_to_hex(team_data["kit_color"]))
    with col3:
        shorts_color_hex = st.color_picker("Shorts Color", rgb_to_hex(team_data.get("shorts_color", [0.1, 0.1, 0.9])))

    # Player Editor
    st.subheader("Players")

    players = team_data.get("players", [])

    if st.button("Add Player"):
        players.append(team_repository.DEFAULT_PLAYER.copy())

    players_to_remove = []

    for i, player in enumerate(players):
        with st.expander(f"Player {i+1}: {player.get('role', 'Unknown')} (Kit #{player.get('kit_no', 0)})"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                role = st.selectbox(f"Role ({i})", team_repository.PLAYER_ROLES, index=team_repository.PLAYER_ROLES.index(player.get('role', 'CM')))
                player['role'] = role
            with c2:
                kit_no = st.number_input(f"Kit Number ({i})", min_value=0, max_value=99, value=player.get('kit_no', 0))
                player['kit_no'] = kit_no
            with c3:
                px = st.number_input(f"Position X ({i})", -1.0, 1.0, player.get('x', 0.0))
                player['x'] = px
            with c4:
                py = st.number_input(f"Position Y ({i})", -0.42, 0.42, player.get('y', 0.0))
                player['y'] = py

            st.markdown("#### Abilities")
            stats = player.get('stats', [0.5] * 22)
            if len(stats) != 22:
                stats = [0.5] * 22

            # Group stats
            groups = {
                "Physical": team_repository.PLAYER_STATS_NAMES[:7],
                "Technical": team_repository.PLAYER_STATS_NAMES[7:16],
                "Mental": team_repository.PLAYER_STATS_NAMES[16:]
            }

            tabs = st.tabs(groups.keys())
            for tab_name, tab in zip(groups.keys(), tabs):
                with tab:
                    for stat_name in groups[tab_name]:
                        idx = team_repository.PLAYER_STATS_NAMES.index(stat_name)
                        stats[idx] = st.slider(f"{stat_name.replace('_', ' ').title()}", 0.0, 1.0, float(stats[idx]), key=f"stat_{i}_{idx}")
            player['stats'] = stats

            if st.button(f"Remove Player {i+1}", key=f"rem_{i}"):
                players_to_remove.append(i)

    for i in sorted(players_to_remove, reverse=True):
        del players[i]

    # Save
    if st.button("Save Team"):
        team_data["name"] = team_name
        team_data["kit_color"] = hex_to_rgb(kit_color_hex)
        team_data["shorts_color"] = hex_to_rgb(shorts_color_hex)
        team_data["players"] = players
        team_repository.save_team(team_name, team_data)
        st.success(f"Team '{team_name}' saved successfully!")

elif page == "Match Simulation":
    st.header("Simulate Match")

    teams = team_repository.list_teams()

    c1, c2 = st.columns(2)
    with c1:
        left_team_name = st.selectbox("Left Team", teams, index=0 if teams else None)
    with c2:
        right_team_name = st.selectbox("Right Team", teams, index=1 if len(teams) > 1 else 0)

    if st.button("Start Simulation"):
        if not left_team_name or not right_team_name:
            st.error("Please select two teams.")
        else:
            left_data = team_repository.load_team(left_team_name)
            right_data = team_repository.load_team(right_team_name)

            # Construct configuration
            config_update = {}

            # Left Team
            config_update['left_team_name'] = left_data['name']
            config_update['left_team_color'] = left_data['kit_color']
            config_update['left_team_color2'] = left_data.get('shorts_color')

            left_players = []
            for p in left_data['players']:
                role_enum = getattr(scenario_builder.Role, f"e_PlayerRole_{p['role']}")
                left_players.append({
                    'x': p['x'], 'y': p['y'],
                    'role': role_enum,
                    'kit_no': p.get('kit_no', 0),
                    'player_stats': p.get('stats')
                })
            config_update['left_team_players'] = left_players

            # Right Team
            config_update['right_team_name'] = right_data['name']
            config_update['right_team_color'] = right_data['kit_color']
            config_update['right_team_color2'] = right_data.get('shorts_color')

            right_players = []
            for p in right_data['players']:
                role_enum = getattr(scenario_builder.Role, f"e_PlayerRole_{p['role']}")
                right_players.append({
                    'x': p['x'], 'y': p['y'],
                    'role': role_enum,
                    'kit_no': p.get('kit_no', 0),
                    'player_stats': p.get('stats')
                })
            config_update['right_team_players'] = right_players

            status_text = st.empty()
            status_text.text("Initializing Environment...")

            try:
                env = football_env.create_environment(
                    env_name='custom',
                    other_config_options=config_update,
                    render=False # Cannot render directly in streamlit easily
                )

                env.reset()
                status_text.text("Running simulation steps...")

                # Run a short simulation
                progress_bar = st.progress(0)
                for step in range(100):
                    action = env.action_space.sample()
                    obs, reward, term, trunc, info = env.step(action)
                    progress_bar.progress(step + 1)
                    if term or trunc:
                        break

                env.close()
                status_text.text("Simulation complete!")
                st.success("Simulation finished successfully.")

            except Exception as e:
                st.error(f"Simulation failed: {e}")
