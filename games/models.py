from django.db import models

# Create your models here.
class FootballGame(models.Model):
    lower_score = models.IntegerField()
    higher_score = models.IntegerField()
    date = models.DateField()
    loser = models.CharField(max_length=100)
    winner = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.date}: {self.winner} ({self.higher_score}) vs {self.loser} ({self.lower_score})"