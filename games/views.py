from django.shortcuts import render
from .models import FootballGame
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
import numpy as np
import json
import os

def view_scores(request, higher_score, lower_score):
    team_name = request.GET.get('team', None)
    if team_name:
        games = FootballGame.objects.filter(
            Q(higher_score=higher_score, lower_score=lower_score),
            Q(winner__icontains=team_name) | Q(loser__icontains=team_name)
        ).order_by('-date')
    else:
        games = FootballGame.objects.filter(higher_score=higher_score, lower_score=lower_score).order_by('-date')
    return render(request, 'view_scores.html', {'games': games, 'higher_score':higher_score, 'lower_score':lower_score})

def research_scores(request):
    return render(request, 'score_lookup.html')

def home(request):
    games = FootballGame.objects.all()
    total_games = len(games)

    unique_scores = set()

    for game in games:
        score_combination = (game.higher_score, game.lower_score)
        unique_scores.add(score_combination)

    total_unique_scores = len(unique_scores)

    context = {
        'total_unique_scores': total_unique_scores,
        'total_games': total_games
    }

    return render(request, 'home.html', context)

def grid(request):
    file_path = os.path.join(settings.BASE_DIR,'staticfiles','Scorigami.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    return JsonResponse(data)