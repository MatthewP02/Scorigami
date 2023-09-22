from datetime import timedelta
from datetime import datetime
import requests
import django
import pytz
import time
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Scorigami.settings")
django.setup()
from games.models import FootballGame

class Scoreboard():
    def __init__(self, games):
        self.s = requests.Session()
        self.games = games
        self.startedGames = {}

    def finalscore(self, id):
        x = self.s.get(f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={id}')
        data = x.json()

        finished = data['header']['competitions'][0]['status']['type']['completed']

        if finished:
            date = data['header']['competitions'][0]['date']
            team1 = data['header']['competitions'][0]['competitors'][0]['team']['nickname']
            team2 = data['header']['competitions'][0]['competitors'][1]['team']['nickname']
            team1score = data['header']['competitions'][0]['competitors'][0]['score']
            team2score = data['header']['competitions'][0]['competitors'][1]['score']
            return date, team1, team2, team1score, team2score
        else:
            return False
            #Game not over

    def check_games(self, games):
        self.games = games
        now = datetime.now(pytz.UTC)
        
        for game_id, game_time in self.games.items():
            if (now - game_time) >= timedelta(hours=2):
                self.startedGames[game_id] = game_time
        
        return self.startedGames

    def tweet(self, gamenumber):
        #twitter post logic 
        print('tweeted')
    
    def addToDatabase(self, date_obj, winner, winner_score, loser, loser_score):
        # Convert to desired string format
        date = date_obj.strftime("%Y-%m-%d")

        game = FootballGame.objects.create(
            lower_score=loser_score,
            higher_score=winner_score, 
            date=date, 
            loser=loser, 
            winner=winner
        )

        print('added to db')