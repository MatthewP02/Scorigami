from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta
from collegeupdate import Scoreboard
import numpy as np
import threading
import requests
import pytz
import time
import json

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
}

with open('/etc/config.json') as config_file:
    config = json.load(config_file)

#keeps going infinitely, will not loop back to start until all of the games for the current week are over. 
# (may have some logic error here, probably should wait until tuesday* morning to loop to check)

def fetch_games():
    #gets games going on
    s = requests.Session()
    x = s.get('https://www.espn.com/college-football/scoreboard/_/group/80?_xhr=pageContent',headers=headers)
    data = x.json()
    events = data["scoreboard"]["evts"]
    games = {}

    for i in range(0,len(events)):
        if events[i]['completed'] == True:
            pass
        else:
            gameid = events[i]['id']
            gametime = events[i]['date']
            games[gameid] = gametime

    #converts values in the dictionary to datetime objects
    games = {game_id: datetime.fromisoformat(game_time.replace('Z', '+00:00')).astimezone(pytz.utc) for game_id, game_time in games.items()}
    return games

def get_final(updater, number):
    while True:
        try:
            date, team1, team2, team1score, team2score = updater.finalscore(number)
            if team1score > team2score:
                winner = team1
                winner_score = team1score
                loser = team2
                loser_score = team2score
            else:
                winner = team2
                winner_score = team2score
                loser = team1
                loser_score = team1score
            date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M%z')
            print(f'{winner} {winner_score} - {loser} {loser_score}')
            #add logic to check for scorigami and post to twitter here
            #best logic to check for scorigami: load in numpy array, check if value == 0, if it is, then that score has never happened
            #ex: clemson beats utah 127-98, so i do x = Scorigami('Scorigami.json'), if x[98][127] == 0: scorigami!
            #adds game to the sqlite db



            response = requests.get(f"http://cfbscorigami.com/get_latest_game/3/20/")
            data = response.json()

            with open("games/temlates/Scorigami.json", 'r') as f:
                data = json.load(f)
        
            grid = np.array(data['grid'])
            hover_text = np.array(data['hover_text'], dtype=object)

            if grid[loser_score][winner_score] == 0:
                print("Scorigami!!!!!!!")
                payload = {"text": f'{winner} beats {loser} {winner_score} to {loser_score}\n SCORIGAMI! SCORE HAS NEVER HAPPENED!'}
                
            else:
                print('No scorigami, updating grid and DB.')
                payload = {"text": f'{winner} beats {loser} {winner_score} to {loser_score}, No scorigami, last occurrence:\n{data["date"]}: {data["winner"]} {data["loser"]}'}
            

            #tweet logic
            client_key = config['client']
            client_secret = config['client_secret']
            resource_key = config['resource_owner_key']
            resource_secret = config['resource_owner_secret']

            oauth = OAuth1Session(
                client_key,
                client_secret=client_secret,
                resource_owner_key=resource_key,
                resource_owner_secret=resource_secret,
            )

            # Making the request
            response = oauth.post(
                "https://api.twitter.com/2/tweets",
                json=payload,
            )

            if response.status_code != 201:
                raise Exception(
                    "Request returned an error: {} {}".format(response.status_code, response.text)
                )

            print("Response code: {}".format(response.status_code))
            print("Response: {}".format(response.json()))
            if grid[loser_score][winner_score] == 0.9999:
                pass
            else:
                grid[loser_score][winner_score] += 0.0001

            #adds to database, we dont need to create the plot anymore as thats all done frontend.
            updater.addToDatabase(date_obj, winner, winner_score, loser, loser_score)

            data = {
                'grid': grid.tolist(),
                'hover_text': hover_text.tolist()
            }

            with open('static/admin/Scorigami.json', 'w') as f:
                json.dump(data, f)

        except:
            print(f'game {number} not over, sleeping 20 minutes.')
            time.sleep(1200)
    
def loopgames(games):
    newgames = fetch_games()
    first_newgames = list(newgames.keys())[0]

    if first_newgames not in games:
        #new week loaded, as the first id of newgames is no longer in the dictionary.
        #so therefor, we overwrite games with the new dictionary.
        games = newgames
    else:
        #continue with games in dictionary
        print('No new week detected.')

    updater = Scoreboard(games)
    #am leaving games dictionary untouched, that way we can check to see if the week is over or not be seeing if new dict == games
    #iterates through started+2 hour games (id:time), and will not stop until all games have been seen


    for gameid, game_time in games.items():

        #make datetime.now() utc
        now_utc = datetime.now(pytz.utc)

        #adds 2 hours to gametime, so we do not start as soon as the game does, as it can not end right away.
        delta = (game_time+timedelta(hours=2)) - now_utc

        if delta.total_seconds() > 0:
            print(f"Waiting for {delta.total_seconds()} seconds until 2 hours after {gameid} starts.")
            time.sleep(delta.total_seconds())

        # Start a new thread to process the game
        game_thread = threading.Thread(target=get_final, args=(updater, gameid))
        game_thread.start()
    

games = {}

while True:
    loopgames(games)
    #waits 10 hours before running again if all the games are done.
    print("Sleeping 10 hours, games seem over for the time being.")
    time.sleep(36000)
