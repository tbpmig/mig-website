from django.shortcuts import render

# Create your views here.

def start_transaction(request):
    # Check permissions to process
    
    # Just a simple form to receive the barcode, uniqname, or UMID
    # Looks up the buyer or seller, redirects to form to confirm information
    pass


def update_person(request, uniqname):
    # Check permissions to process

    # If person exists, pre-fill information
    # If person has profile but not BS profile, pre-fill some of it, and on
    # submit link together
    # If person has nothing, will need to create and link everything on submit

    # Depending on if selling/receiving is enabled, redirect to receive or sell book page
    pass


def receive_book_start(request, uniqname):
    # Check permissions to receive

    # Just show a form for the barcode
    # On submit looks up the book type, if present redirects to receive_book
    # If not saves the uniqname into request.session and redirects to
    # create_book_type
    pass

def create_book_type(request):
    # Needs to redirect to receive that book
    pass

def receive_book(request, uniqname, book_type_id):
    # Check permissions to receive

    # Just show a form for the barcode
    # On submit looks up the book type, redirects with a page to choose which one
    pass


def sell_book_start(request, uniqname):
    # Check permissions to sell

    # Just show a form for the barcode
    # On submit looks up the book type, redirects with a page to choose which one
    pass


def sell_book(request, uniqname, book_type_id):
    pass


# Should probably be ajax
def sell_individual_book(request,uniqname,book_id):
    pass
    

def manage_bookswap_settings(request):
    # Check appropriate permissions
    pass

    
    

