from django.urls import path

from . import views
urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("create", views.createListing, name="create"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("watchlist/<int:listing_id>/toggle/", views.toggle_watchlist, name="toggle_watchlist"),
    path("listings/<int:listing_id>/", views.listingPage, name="listings"),
    path('won/', views.won_listings, name='won'),
    path('closed/', views.closed_listings, name='closed'),
    path('close/<int:listing_id>/', views.close, name='close'),
    path("register", views.register, name="register"),
    path('categories/', views.categories, name='categories'),
    path('category/<int:category_id>/', views.category_listings, name='category_listings'),
]
