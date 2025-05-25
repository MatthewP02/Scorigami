from discord_webhook import DiscordWebhook
from addScoresToDB import addScores
from datetime import datetime
import numpy as np
import requests
import django
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

#years = [i for i in range(1869, 2024) if i != 1871]
years = [2024]

token = os.getenv('COLLEGE_FOOTBALL_DATA_API_KEY')
webhook_url = os.getenv('DISCORD_WEBHOOK')

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {token}"
}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Scorigami.settings")
django.setup()
from games.models import FootballGame, FootballTeam

def send_discord_notification(message):
    webhook = DiscordWebhook(url=webhook_url, content=message)
    response = webhook.execute()

def dumpScores(self):
    try:
        # Initialize grid and hover text
        grid = np.zeros((73, 223))
        hover_text = np.empty(grid.shape, dtype=object)
        hover_text.fill('')

        # Mark impossible scores
        impossible_scores = [(7, 1)]
        for x, y in impossible_scores:
            grid[y, x] = 1
            hover_text[y][x] = "This score is impossible."

        for i in range(223):
            for j in range(i + 1, 73):
                grid[j, i] = 1  # Mark as impossible (losing team can't score more than the winner)
                hover_text[j][i] = "The losing team cannot have more points than the winner."

        # Query all games from the database and populate the grid
        games = FootballGame.objects.all()

        for game in games:
            lower_score = game.lower_score
            higher_score = game.higher_score

            if grid[lower_score][higher_score] < 1:
                grid[lower_score][higher_score] += 0.0001  # Increment score occurrence

            if hover_text[lower_score][higher_score] == "":
                hover_text[lower_score][higher_score] = f"1 game: {game.date}: {game.winner.name} {higher_score} - {game.loser.name} {lower_score}<br>"
            else:
                game_count = int(grid[lower_score][higher_score] * 10000)
                hover_text[lower_score][higher_score] = f"{game_count} games: {game.date}: {game.winner.name} {higher_score} - {game.loser.name} {lower_score}<br>"

        # Convert grid and hover_text to lists
        data = {
            'grid': grid.tolist(),
            'hover_text': hover_text.tolist()
        }

        # Save to JSON file
        file_path = f"static/Scorigami.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        print(f"Scorigami data saved to {file_path}")
    except Exception as e:
        print(f"Error querying games from the database: {e}")
        send_discord_notification(f"Error querying games from the database: {e}")
        return

# Initialize addScores class
score_adder = addScores()

with requests.Session() as s:
    for year in years:
        while True:
            try:
                url = f'https://api.collegefootballdata.com/games?year={year}'
                x = s.get(url, headers=headers)

                games = json.loads(x.content)
                print(year)

                for game in games:
                    try:
                        game_id = game["id"]
                        date = game["startDate"]
                        home_team = game["homeTeam"]
                        home_score = game["homePoints"]
                        home_id = game["homeId"]
                        away_team = game["awayTeam"]
                        away_score = game["awayPoints"]
                        away_id = game["awayId"]
                        print(f"[{date}] {home_team} {home_score} - {away_score} {away_team}")
                        
                        # Convert date to a usable format
                        date_str = date.replace('Z', '').split('.')[0]
                        date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                        if date_obj > datetime.now():
                            print('End of schedule. Breaking...')
                            break

                        # Handle cases where score is not recorded
                        if home_score is None or away_score is None:
                            print(f"No score recorded: {home_score}, {away_score}. Skipping game.")
                            continue

                        # Determine the winner and loser, and add the score to the database
                        if home_score < away_score:
                            # Away team won
                            score_adder.addScore(
                                game_id = game_id,
                                winner_name=away_team, 
                                winner_id=away_id, 
                                loser_name=home_team, 
                                loser_id=home_id, 
                                winner_score=away_score, 
                                loser_score=home_score, 
                                date=date_obj
                            )
                        else:
                            # Home team won
                            score_adder.addScore(
                                game_id = game_id,
                                winner_name=home_team, 
                                winner_id=home_id, 
                                loser_name=away_team, 
                                loser_id=away_id, 
                                winner_score=home_score, 
                                loser_score=away_score, 
                                date=date_obj
                            )
                    except Exception as e:
                        print(f'Error: {e}')
                        if "UNIQUE constraint failed" in str(e):
                            continue
                        else:
                            break

            except Exception as e:
                print(f'Error: {e}')
                time.sleep(3)  # Pause before retrying
                continue
            break

    # Dump the scores to the database
    dumpScores(score_adder)