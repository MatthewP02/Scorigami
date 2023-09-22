from django.shortcuts import render
from .models import FootballGame
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
import json
import os

def view_scores(request, higher_score, lower_score):
    team_name = request.GET.get('team', None)
    if team_name:
        games = FootballGame.objects.filter(
            Q(higher_score=higher_score, lower_score=lower_score),
            Q(winner__icontains=team_name) | Q(loser__icontains=team_name)
        )
    else:
        games = FootballGame.objects.filter(higher_score=higher_score, lower_score=lower_score)
    return render(request, 'view_scores.html', {'games': games, 'higher_score':higher_score, 'lower_score':lower_score})

def research_scores(request):
    return render(request, 'score_lookup.html')

def home(request):
    game_count = FootballGame.objects.all().count()
    context = {
        'game_count': game_count
    }
    return render(request, 'home.html', context)

def grid(request):
    file_path = os.path.join(settings.BASE_DIR,'static','admin','Scorigami.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    return JsonResponse(data)

def get_latest_game(request, winner_score, loser_score):
    if winner_score < loser_score:
        winner_score, loser_score = loser_score, winner_score
    
    games = FootballGame.objects.filter(higher_score=winner_score, lower_score=loser_score).order_by('-date')
    
    latest_game = games.first()
    
    if not latest_game:
        return JsonResponse({'error': 'No game found with the given scores'}, status=404)
    
    return JsonResponse({
        'date': latest_game.date,
        'winner': latest_game.winner,
        'loser': latest_game.loser,
        'winner_score': latest_game.higher_score,
        'loser_score': latest_game.lower_score,
    })