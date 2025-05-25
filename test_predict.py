import joblib
import warnings
import numpy as np
import matplotlib.pyplot as plt
import mplcursors

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
            
clf = joblib.load('scorigami_model.pkl')
print(predict_scorigami_likelihood(65,33, clf))