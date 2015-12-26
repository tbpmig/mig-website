from django.shortcuts import redirect
from django.http import HttpResponse

from mig_main.utility import get_previous_page, Permissions, get_message_dict

def get_permissions(user):
    return {}


def get_common_context(request):
    context_dict = get_message_dict(request)
    context_dict.update({
        'main_nav': 'bookswap',
    })
    return context_dict


# Create your views here.
# These are for the admin site part
def admin_index(request):
    pass


def start_transaction(request):
    """ Just a simple form to receive the barcode, uniqname, or UMID
    Looks up the buyer or seller, redirects to form to confirm information
    """
    if not Permissions.can_process_bookswap(event, request.user): # TODO: create permission logic
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM # TODO: Add message
        return get_previous_page(request, alternate='bookswap:admin_index')
    form = StartTransactionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            uniqname = ''
            if user:
                request.session['success_message'] = ('User found, please '
                                                      'confirm details.')
                uniqname = user.user_profile.uniqname
            else:
                request.session['error_message'] = ('User not found, please '
                                                    'create now.')
                request.session['UMID'] = form.cleaned_data['user_UMID']
                request.session['uniqname'] = form.cleaned_data['user_uniqname']
                request.session['barcode'] = form.cleaned_data['user_barcode']
                
            return redirect('bookswap:update_person', uniqname=uniqname)
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Search for user',
        'form_title': 'Search for a user in the system',
        'help_text': ('You can search for a user by UMID, uniqname, or the '
                      'barcode on their MCard.'),
        'base': 'bookswap/base_bookswap.html', # TODO: make this
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    



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


# These are for the public front end
def view_faq(request):
    pass


def view_inventory(request):
    pass


def view_location(request):
    pass


def view_resources(request):
    pass
