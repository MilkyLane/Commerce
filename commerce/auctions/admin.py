
from django.contrib import admin
from .models import Listings, bids, Comments, Category

admin.site.register(Category)
admin.site.register(Listings)
admin.site.register(bids)
admin.site.register(Comments)