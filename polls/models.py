from django.db import models

# Create your models here.

class Listdata(models.Model):
    item1 = models.CharField(max_length=50, blank=True)
    item2 = models.CharField(max_length=50, blank=True)
    rank = models.IntegerField(default=1)

    def __unicode__(self):
        return(self.item1 + ":"+ str(self.rank))
