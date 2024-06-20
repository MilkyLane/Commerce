from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    pass

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
class Listings(models.Model):


    title = models.CharField(max_length=255)
    description = models.TextField()
    sBid = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_listings')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='won_listings')
    image_url = models.URLField(blank=True)
    closed = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, related_name='listings')

    def has_winner(self, user):
        if self.closed:
            high_bid = self.bids.order_by('-amount').first()
            if high_bid:
                return high_bid.user == user
        return False


class bids(models.Model):
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listings, related_name='bids', on_delete=models.CASCADE)




class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'listing')


class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


