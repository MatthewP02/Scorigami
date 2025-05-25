from django.db import models

class FootballTeam(models.Model):
    name = models.CharField(max_length=255)
    team_id = models.IntegerField(unique=True)

class FootballGame(models.Model):
    game_id = models.IntegerField(unique=True)
    lower_score = models.IntegerField()
    higher_score = models.IntegerField()
    date = models.DateField()
    loser = models.ForeignKey(FootballTeam, related_name='losing_games', on_delete=models.CASCADE)
    winner = models.ForeignKey(FootballTeam, related_name='winning_games', on_delete=models.CASCADE)