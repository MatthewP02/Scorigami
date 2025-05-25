from datetime import datetime, timezone, timedelta
import time
import joblib
import requests
import threading
from discord_webhook import DiscordWebhook
from addScoresToDB import addScores  # Import your class that handles adding scores
import json
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('COLLEGE_FOOTBALL_DATA_API_KEY')
webhook_url = os.getenv('DISCORD_WEBHOOK')

headers = {
    'Authorization': f'Bearer {token}'
}

def predict_scorigami_likelihood(winner_score, loser_score, clf):
    if (winner_score <= 36 or 
        loser_score == 1 or 
        winner_score == loser_score or 
        (winner_score < 45 and loser_score != 4)):
        return 0.0
    score_diff = winner_score - loser_score
    total_points = winner_score + loser_score
    input_data = [[winner_score, loser_score, score_diff, total_points]]
    
    # Predict the probability of scorigami
    scorigami_prob = clf.predict_proba(input_data)[0][1]  # Probability of scorigami (class 1)
    return round(scorigami_prob*100,2)

# Instantiate the addScores class
score_adder = addScores()

# Function to fetch games based on classification
def fetch_games(classification):
    url = f'https://apinext.collegefootballdata.com/scoreboard?classification={classification}'
    response = requests.get(url, headers=headers)
    return response.json()

# Function to parse the start date
def parse_date(date_str):
    date_str = date_str.replace('Z', '').split('.')[0]
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')

def send_discord_notification(message):
    webhook = DiscordWebhook(url=webhook_url, content=message)
    response = webhook.execute()

# Function to monitor the games
def monitor_games(classification):
    clf = joblib.load('scorigami_model.pkl')

    while True:
        games = fetch_games(classification)

        if not games:
            print(f"({classification}) No games found. Checking again in an hour...")
            time.sleep(3600)  # Sleep for 1 hour if no games are found
            continue

        ongoing_games = {}
        tweeted_games = {}

        # Start monitoring the games
        while True:
            all_games_completed = True 
            
            for game in games:
                #print(game)
                #exit()
                status = game['status']
                game_id = game['id']
                home_team = game['homeTeam']
                away_team = game['awayTeam']
                
                # Parse the start time of the game
                start_time = parse_date(game['startDate'])
                current_time = datetime.now(timezone.utc)

                # Check if the game is ongoing or in progress
                if current_time >= start_time.replace(tzinfo=timezone.utc) and status in ['in_progress']:#, 'scheduled']:
                    all_games_completed = False  # At least one game is ongoing
                    
                    if game_id not in ongoing_games:
                        print(f"({classification}) Game {away_team['name']} vs {home_team['name']} has started! Monitoring...")
                        send_discord_notification(f"({classification}) Game {away_team['name']} vs {home_team['name']} has started! Monitoring...")
                        scorigami_prob = predict_scorigami_likelihood(home_team['points'], away_team['points'], clf)

                        if scorigami_prob > 35 and game_id not in tweeted_games:
                            print(f"({classification}) Scorigami likely in game {away_team['name']} vs {home_team['name']}! Probability: {scorigami_prob}")
                            send_discord_notification(f"({classification}) Scorigami likely in game {away_team['name']} vs {home_team['name']}! Probability: {scorigami_prob}")

                            addScores.tweetPotentialScorigami(away_team['id'], home_team['id'], away_team['name'], home_team['name'], away_team['points'], home_team['points'], game['period'], game['clock'])
                            tweeted_games[game_id] = True
                            ongoing_games[game_id] = {'game': game, 'potential_scorigami': True}
                        else:
                            ongoing_games[game_id] = {'game': game, 'potential_scorigami': False}

                # If the game is completed, send data to addNewScore() from the addScores class
                if status == 'completed' and game_id in ongoing_games:
                    winner = home_team if home_team['points'] > away_team['points'] else away_team
                    loser = away_team if home_team['points'] > away_team['points'] else home_team
                    potential_scorigami = ongoing_games[game_id]['potential_scorigami']

                    # handle tweet and image creation inside of addNewScore
                    # Call the addNewScore function from your addScores class
                    score_adder.addNewScore(
                        game_id=game_id,
                        winner_name=winner['name'],
                        winner_id=winner['id'],
                        loser_name=loser['name'],
                        loser_id=loser['id'],
                        winner_score=winner['points'],
                        loser_score=loser['points'],
                        date=parse_date(game['startDate']),
                        potential_scorigami=potential_scorigami
                    )

            # Remove completed games from the ongoing games list
            ongoing_games = {gid: g for gid, g in ongoing_games.items() if g['game']['status'] != 'completed'}

            # If all games are completed, break out of the monitoring loop
            if all_games_completed:
                print(f"({classification}) All current games have been completed.")
                send_discord_notification(f"({classification}) All current games have been completed.")
                break

            # Fetch updates for ongoing games
            if ongoing_games:
                print(f"({classification}) Fetching updates for {len(ongoing_games)} ongoing games...")
                games = fetch_games(classification)

            # Sleep for 5 minutes before fetching again
            time.sleep(300)

        # Fetch new games once the current games are completed
        print(f"({classification}) Waiting one hour...")
        time.sleep(3600)  # Wait 1 hour before checking for new games

# Function to start threads for each classification
def start_monitoring_in_threads():
    classifications = ['fbs', 'fcs', 'ii', 'iii']
    threads = []

    # Create and start a thread for each classification
    for classification in classifications:
        thread = threading.Thread(target=monitor_games, args=(classification,))
        thread.start()
        threads.append(thread)

    # Join threads to wait for all of them to finish
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_monitoring_in_threads()