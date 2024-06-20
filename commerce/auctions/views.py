from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Listings, User, bids, Comments, Watchlist, Category
from django.db.models import Max

def index(request):
     aListings = Listings.objects.filter(closed=False)

     if request.user.is_authenticated:

         watchlist = Watchlist.objects.filter(user=request.user)
         watchlist_listings = [item.listing for item in watchlist]
     else:
         watchlist_listings = []
     return render(request, 'auctions/index.html', {'listings': aListings, 'watchlist_listings': watchlist_listings})


def watchlist(request):
    if request.user.is_authenticated:
        watchlist_items = Watchlist.objects.filter(user=request.user)
        context = {'watchlist_items': watchlist_items}
        return render(request, 'auctions/watchlist.html', context)
    else:
        return HttpResponseRedirect('index')

def toggle_watchlist(request, listing_id):
    if request.user.is_authenticated:
        listing = Listings.objects.get(pk=listing_id)
        user = request.user

        on_watchlist = Watchlist.objects.filter(user=user, listing=listing).exists()
        if on_watchlist:

            Watchlist.objects.filter(user=user, listing=listing).delete()
            message = "Listing removed from watchlist."
        else:

            Watchlist.objects.create(user=user, listing=listing)
            message = "Listing added to watchlist."
        return redirect('index')
    else:
        return HttpResponseRedirect(reverse('login'))

def category_listings(request, category_id):
    category = Category.objects.get(pk=category_id)
    listings = category.listings.filter(closed=False)
    return render(request, 'auctions/category_listings.html', {'category': category, 'listings': listings})
def categories(request):
    categories = Category.objects.all()
    return render(request, 'auctions/categories.html', {'categories': categories})
def close(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    if request.user == listing.user:
        listing.closed = True
        high_bid = bids.objects.filter(listing=listing).aggregate(Max('amount'))
        if high_bid:
            high_bid_amount = high_bid['amount__max']
            winning_bid = bids.objects.filter(listing=listing, amount=high_bid_amount).first()
            if winning_bid:

                listing.winner = winning_bid.user
        listing.save()
    return redirect('listings', listing_id=listing_id)
def createListing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        try:
            sBid = float(request.POST.get("sBid"))
            if sBid < 0:
                raise ValueError("Starting bid must be non-negative")
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid input data")
        image_url = request.POST.get('image_url', '')
        listing = Listings.objects.create(title=title, description=description, sBid=sBid,
                                          image_url=image_url, user=request.user, )
        categories_ids = request.POST.getlist('categories')
        categories = Category.objects.filter(pk__in=categories_ids)


        for category_id in categories_ids:
            category = Category.objects.get(pk=category_id)
            listing.categories.add(category)

        return redirect('index')
    else:
        categories = Category.objects.all()  # Fetch all categories
        context = {'categories': categories}  # Add categories to context
        return render(request, 'auctions/create.html', context)


def listingPage(request, listing_id):

    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')

    try:
        listing = Listings.objects.get(pk=listing_id)
    except Listings.DoesNotExist:
        return render(request, '404.html')

    can_close_auction = listing.user == request.user and not listing.closed

    if request.method == "POST":
        if request.POST.get("close_auction"):
            if can_close_auction:
                try:
                    listing.closed = True
                    if bids.objects.filter(listing=listing).exists():
                        high_bid = bids.objects.filter(listing=listing).order_by('-amount').first()
                        if high_bid:
                            listing.winner = high_bid.user
                    listing.save()
                    if bids.objects.filter(listing=listing).exists():
                        high_bid = bids.objects.filter(listing=listing).order_by('-amount').first()


                    return redirect('listings', listing_id)
                except Exception as e:
                    return HttpResponseBadRequest("There was an error closing the auction.")
            else:
                return HttpResponseBadRequest("You are not authorized to close this auction.")


        bid_amount = request.POST.get("bid")
        comment = request.POST.get("comment")
        if bid_amount:
            try:
                bid_amount = float(bid_amount)

                if bid_amount <= listing.sBid:
                    return HttpResponseBadRequest("Bid must be higher than the starting bid.")

                if bids.objects.filter(listing=listing, amount__gte=bid_amount).exists():
                    return HttpResponseBadRequest("Bid must be higher than the current highest bid.")

                bid = bids.objects.create(
                    user=request.user,
                    listing=listing,
                    amount=bid_amount
                )
                if comment:
                    Comments.objects.create(
                        user=request.user,
                        listing=listing,
                        content=comment
                    )

                return redirect('listings', listing_id)
            except ValueError:
                return HttpResponseBadRequest("Invalid bid amount. Please enter a valid number.")
        else:
            return HttpResponseBadRequest("Missing bid amount. Please enter a bid.")

    else:  # GET request
        high_bid = bids.objects.filter(listing=listing).order_by('-amount').first()
        comments = Comments.objects.filter(listing=listing).order_by('-timestamp')
        won_auction = (listing.closed and high_bid and high_bid.user == request.user)
        winner = listing.has_winner if listing.closed else None

        context = {
            'listing': listing,
            'high_bid': high_bid,
            'comments': comments,
            'user_has_won': listing.has_winner(request.user),
            'user_is_creator': listing.user == request.user,
            'won_auction': won_auction,
            'can_close_auction': can_close_auction
        }
        return render(request, 'auctions/listings.html', context)


def closed_listing(request, listing_id):
    listing = get_object_or_404(Listings, pk=listing_id)
    if listing.has_winner(request.user) or listing.user == request.user:
        return render(request, 'auctions/closed.html', {'listing': listing})
    else:
        return render(request, 'auctions/won.html')

def won_listings(request):
    won_listings = Listings.objects.filter(winner=request.user, closed=True)
    return render(request, 'auctions/won.html', {'listings': won_listings})

def closed_listings(request):
    closed_listings = Listings.objects.filter(user=request.user, closed=True)
    return render(request, 'auctions/closed.html', {'listings': closed_listings})

def login_view(request):
    if request.method == "POST":


        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)


        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]


        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })


        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
