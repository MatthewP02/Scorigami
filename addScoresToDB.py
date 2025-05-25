from image_creator import create_score_image
from datetime import datetime
import numpy as np
import tweepy
import django
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Scorigami.settings")
django.setup()
from games.models import FootballGame, FootballTeam

# Initialize Twitter API v2 Client
client = tweepy.Client(
    consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
    consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
)

class addScores:
    def dumpScores(self):
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

    def addScore(self, game_id, winner_name, winner_id, loser_name, loser_id, winner_score, loser_score, date):
        
        # Fetch or create winner and loser teams from the database
        winner_team, _ = FootballTeam.objects.get_or_create(team_id=winner_id, defaults={'name': winner_name})
        loser_team, _ = FootballTeam.objects.get_or_create(team_id=loser_id, defaults={'name': loser_name})

        date_str = date.strftime("%Y-%m-%d")

        # Print details for verification
        print(f"Date: {date_str}")
        print(f"Winner: {winner_team.name} (ID: {winner_team.team_id})")
        print(f"Winner Score: {winner_score}")
        print(f"Loser: {loser_team.name} (ID: {loser_team.team_id})")
        print(f"Loser Score: {loser_score}")

        # Create and save the FootballGame record
        FootballGame.objects.create(
            game_id=game_id,
            lower_score=loser_score,
            higher_score=winner_score, 
            date=date_str, 
            loser=loser_team, 
            winner=winner_team
        )
    
    def addNewScore(self, game_id, winner_name, winner_id, loser_name, loser_id, higher_score, lower_score, date, potential_scorigami):
        # Fetch or create winner and loser teams from the database
        winner_team, _ = FootballTeam.objects.get_or_create(team_id=winner_id, defaults={'name': winner_name})
        loser_team, _ = FootballTeam.objects.get_or_create(team_id=loser_id, defaults={'name': loser_name})

        # Add the new game to the database
        FootballGame.objects.create(
            game_id=game_id,
            higher_score=higher_score,
            lower_score=lower_score,
            date=date,
            winner=winner_team,
            loser=loser_team
        )

        print(f"Game added to the database: {winner_name} {higher_score} - {loser_name} {lower_score}")
        # self.send_discord_notification(f"Game added to the database: {winner_name} {higher_score} - {loser_name} {lower_score}")
        # Check if a game with the same higher and lower score already exists
        existing_game = FootballGame.objects.filter(higher_score=higher_score, lower_score=lower_score).first()

        if existing_game:
            print(f"Game with score {higher_score}-{lower_score} already exists. Updating the database.")
            if potential_scorigami:
                # Post to Twitter here (since potential scorigami)
                self.noScorigami(winner_id, loser_id, winner_name, loser_name, higher_score, lower_score, "4th", "0:00")
        else:
            # Post to Twitter here (since no existing game with this score)
            games = FootballGame.objects.all()
            unique_scores = set()

            for game in games:
                score_combination = (game.higher_score, game.lower_score)
                unique_scores.add(score_combination)

            total_unique_scores = len(unique_scores)

            self.tweetScorigami(winner_id, loser_id, winner_name, loser_name, higher_score, lower_score, "4th", "0:00", total_unique_scores)
            

    def tweetScorigami(self, winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left, total_unique_scores):
        try:  
            # Format the tweet
            suffix = "th" if 10 <= total_unique_scores % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(total_unique_scores % 10, "th")
            tweet_text = f"SCORIGAMI! The {total_unique_scores}{suffix} unique score in college football history! {winner} {winner_score}, {loser} {loser_score} #Scorigami #CollegeFootball #CFBScorigami"
            
            # Create the image and post tweet with image
            create_score_image(winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left, 1)
            
            # Upload media and post tweet using v2 API
            media = client.media_upload('cropped_score_image.png')
            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            
        except tweepy.TweepyException as e:
            print(f"Error posting Scorigami tweet: {e}")
            time.sleep(5)
            self.tweetScorigami(winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left, total_unique_scores)

    def tweetPotentialScorigami(self, away_team_id, home_team_id, away_team_name, home_team_name, away_score, home_score, period, time_left):
        try:
            period = "1st" if period == "1" else "2nd" if period == "2" else "3rd" if period == "3" else "4th"
            winner = home_team_name if home_score > away_score else away_team_name
            loser = away_team_name if home_score > away_score else home_team_name
            winner_score = home_score if home_score > away_score else away_score
            loser_score = away_score if home_score > away_score else home_score
            
            # Format the tweet
            tweet_text = f"Potential Scorigami Alert: {winner} leads {loser} {winner_score} to {loser_score} ({period}, {time_left} remaining) #Scorigami #CollegeFootball #CFBScorigami"
            
            # Create the image and post tweet with image
            create_score_image(home_team_id, away_team_id, home_team_name, away_team_name, home_score, away_score, period, time_left, 2)
            
            # Upload media and post tweet using v2 API
            media = client.media_upload('cropped_score_image.png')
            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            
        except tweepy.TweepyException as e:
            print(f"Error posting Potential Scorigami tweet: {e}")
            time.sleep(5)
            self.tweetPotentialScorigami(away_team_id, home_team_id, away_team_name, home_team_name, away_score, home_score, period, time_left)

    def noScorigami(self, winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left):
        try:
            # Format the tweet
            tweet_text = f"No Scorigami. {winner} beats {loser} {winner_score} to {loser_score} #Scorigami #CollegeFootball #CFBScorigami"
            
            # Create the image and post tweet with image
            create_score_image(winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left, 0)
            
            # Upload media and post tweet using v2 API
            media = client.media_upload('cropped_score_image.png')
            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            
        except tweepy.TweepyException as e:
            print(f"Error posting No Scorigami tweet: {e}")
            time.sleep(5)
            self.noScorigami(winner_id, loser_id, winner, loser, winner_score, loser_score, period, time_left)