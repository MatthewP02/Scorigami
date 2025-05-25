import pandas as pd
import os
import django
import joblib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Scorigami.settings")
django.setup()
from games.models import FootballGame, FootballTeam

# Fetch all games from the database
def fetch_historical_scores():
    games = FootballGame.objects.order_by('date').all()  # Order by date to detect first occurrence
    score_set = set()
    scorigami_data = []

    for game in games:
        score_combination = (game.higher_score, game.lower_score)
        is_scorigami = 0  # Default to not a scorigami

        if score_combination not in score_set:
            is_scorigami = 1  # It's a scorigami if it hasn't occurred before
            score_set.add(score_combination)  # Add the score to the set of seen scores

        # Add the game data to a list for future processing
        scorigami_data.append({
            'game_id': game.game_id,
            'winner_score': game.higher_score,
            'loser_score': game.lower_score,
            'date': game.date,
            'is_scorigami': is_scorigami,
        })

    # Convert the list to a pandas DataFrame
    return pd.DataFrame(scorigami_data)

# Call this function to get historical scores labeled for scorigami
historical_scores_df = fetch_historical_scores()

# Feature engineering for the scorigami dataset
historical_scores_df['score_difference'] = historical_scores_df['winner_score'] - historical_scores_df['loser_score']
historical_scores_df['total_points'] = historical_scores_df['winner_score'] + historical_scores_df['loser_score']

# Features and labels
X = historical_scores_df[['winner_score', 'loser_score', 'score_difference', 'total_points']]
y = historical_scores_df['is_scorigami']

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
joblib.dump(clf, 'scorigami_model.pkl')