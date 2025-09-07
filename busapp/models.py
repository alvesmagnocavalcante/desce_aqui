from django.db import models

class BusStop(models.Model):
    busstop_id = models.CharField(max_length=50)
    lat = models.FloatField()
    lng = models.FloatField()

    def __str__(self):
        return self.busstop_id
