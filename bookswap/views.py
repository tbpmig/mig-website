from django.shortcuts import redirect, get_object_or_404
from django.template import RequestContext, loader
from django.http import HttpResponse

from mig_main.utility import get_previous_page, Permissions, get_message_dict
from mig_main import messages
from mig_main.models import AcademicTerm
from bookswap.models import BookSwapPerson, BookSwapStatus, BookType, Book
from bookswap.forms import (
        StartTransactionForm,
        BookSwapPersonForm,
        BookSwapPersonFormNoProfile,
        BookSearchForm,
        BookTypeForm,
        ReceiveBookForm,
)
def get_permissions(user):
    return {
        'can_process':Permissions.can_process_bookswap(user),
    }


def get_common_context(request):
    context_dict = get_message_dict(request)
    context_dict.update({
        'main_nav': 'bookswap',
    })
    return context_dict


# Create your views here.
# These are for the admin site part
def admin_index(request):
    template = loader.get_template('bookswap/bookswap_admin_index.html')
    context_dict = {}
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def start_transaction(request):
    """ Just a simple form to receive the barcode, uniqname, or UMID
    Looks up the buyer or seller, redirects to form to confirm information
    """
    if not Permissions.can_process_bookswap(request.user): # TODO: create permission logic
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM 
        return get_previous_page(request, alternate='bookswap:admin_index')
    form = StartTransactionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            uniqname = ''
            if user:
                request.session['success_message'] = ('User found, please '
                                                      'confirm details.')
                request.session['had_profile'] = True
                uniqname = user.user_profile.uniqname
                request.session['uniqname'] = uniqname
            else:
                request.session['error_message'] = ('User not found, please '
                                                    'create now.')
                request.session['UMID'] = form.cleaned_data['user_UMID']
                request.session['uniqname'] = form.cleaned_data['user_uniqname']
                request.session['barcode'] = form.cleaned_data['user_barcode']
                request.session['had_profile'] = False
            return redirect('bookswap:update_person')
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
        'base': 'bookswap/base_bookswap.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    

def update_person(request):
    """ If person exists, pre-fill information
    If person has profile but not BS profile, pre-fill some of it, and on
    submit link together
    If person has nothing, will need to create and link everything on submit 
    """
    if not Permissions.can_process_bookswap(request.user):
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM
        return get_previous_page(request, alternate='bookswap:admin_index')
    had_profile = request.session.pop('had_profile', False)
    uniqname = request.session.pop('uniqname', '')
    if had_profile:
        bsp = BookSwapPerson.objects.get(user_profile__uniqname=uniqname)
        form = BookSwapPersonForm(request.POST or None, instance=bsp)
    else:
        initial = {
            'UMID': request.session.pop('UMID', ''),
            'uniqname': uniqname,
            'barcode': request.session.pop('barcode', ''),
        }
        form = BookSwapPersonFormNoProfile(request.POST or None, initial=initial)
        
    if request.method == 'POST':
        if form.is_valid():
            bsp = form.save()
            uniqname = bsp.user_profile.uniqname
            request.session['success_message'] = ('User created/updated.')
            if BookSwapStatus.can_receive(AcademicTerm.get_current_term()):
                return redirect('bookswap:receive_book_start', uniqname=uniqname)
            elif BookSwapStatus.can_sell(AcademicTerm.get_current_term()):
                return redirect('bookswap:sell_book_start', uniqname=uniqname)
            else:
                request.session['info_message'] = ('Book Swap not open for '
                                                   'receiving or selling')
                return redirect('bookswap:admin_index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
            request.session['had_profile'] = had_profile
            request.session['uniqname'] = uniqname
    else:
        request.session['had_profile'] = had_profile
        request.session['uniqname'] = uniqname
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Create/update user',
        'form_title': 'Create/update the user information',
        'help_text': ('Please confirm that the following is correct and '
                      'update as necessary. Note that for sellers an address '
                      'is required.'),
        'base': 'bookswap/base_bookswap.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))



def receive_book_start(request, uniqname):
    """ Just show a form for the barcode
    On submit looks up the book type, if present redirects to receive_book
    If not saves the uniqname into request.session and redirects to
    create_book_type
    """
    if not Permissions.can_process_bookswap(request.user):
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM
        return get_previous_page(request, alternate='bookswap:admin_index')
    if not BookSwapStatus.can_receive(AcademicTerm.get_current_term()):
        request.session['error_message'] = 'Book receiving not enabled'
        return get_previous_page(request, alternate='bookswap:admin_index')
    form = BookSearchForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            barcode = form.cleaned_data.get('book_barcode','')
            book_type = BookType.objects.filter(isbn=barcode)
            if book_type.exists():
                # TODO: If multiple give choice?
                book_type = book_type[0]
                request.session['success_message'] = ('Book found, please '
                                                      'enter sale details.')
                return redirect('bookswap:receive_book',
                                uniqname=uniqname,
                                book_type_id=book_type.id)

            else:
                request.session['warning_message'] = ('Book not found, please '
                                                      'enter details.')
                request.session['uniqname'] = uniqname
                request.session['isbn'] = barcode
                return redirect('bookswap:create_book_type')

        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Search for book by ISBN',
        'form_title': 'Search for a book in the system',
        'help_text': ('You can search for a book by its ISBN, which is the '
                      '13 digit code scanned by the barcode.'),
        'base': 'bookswap/base_bookswap.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def create_book_type(request):
    if not Permissions.can_process_bookswap(request.user):
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM
        return get_previous_page(request, alternate='bookswap:admin_index')
    if not BookSwapStatus.can_receive(AcademicTerm.get_current_term()):
        request.session['error_message'] = 'Book receiving not enabled'
        return get_previous_page(request, alternate='bookswap:admin_index')
    isbn = request.session.get('isbn', '')
    form = BookTypeForm(request.POST or None, initial = {'isbn': isbn})
    if request.method == 'POST':
        if form.is_valid():
            book_type = form.save()
            request.session['success_message'] = ('Book type created! '
                                                  'Please continue.')
            uniqname = request.session.pop('uniqname', '')
            request.session.pop('isbn', '')
            if uniqname:
                return redirect('bookswap:receive_book',
                                uniqname=uniqname,
                                book_type_id=book_type.id)
            else:
                return redirect('bookswap:create_book_type')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Create book type',
        'form_title': 'Create a book type',
        'help_text': ('This creates a type of book, not an individual '
                      'physical book to sell.'),
        'base': 'bookswap/base_bookswap.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def receive_book(request, uniqname, book_type_id):
    if not Permissions.can_process_bookswap(request.user):
        request.session['error_message'] = messages.BOOKSWAP_NO_PERM
        return get_previous_page(request, alternate='bookswap:admin_index')
    if not BookSwapStatus.can_receive(AcademicTerm.get_current_term()):
        request.session['error_message'] = 'Book receiving not enabled'
        return get_previous_page(request, alternate='bookswap:admin_index')
    book_type = get_object_or_404(BookType, id=book_type_id)
    seller = get_object_or_404(BookSwapPerson, user_profile__uniqname=uniqname)
    instance = Book(
                seller=seller,
                book_type=book_type,
                term=AcademicTerm.get_current_term()
    )
    form = ReceiveBookForm(request.POST or None, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            book = form.save()
            request.session['success_message'] = ('Book added created! '
                                                  'Please continue.')
            return redirect('bookswap:receive_book_start',
                            uniqname=uniqname)
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Receive book',
        'form_title': 'Recieve a copy of: %s for %s' % (book_type.title, uniqname),
        'help_text': ('This receives a specific saleable book.'),
        'base': 'bookswap/base_bookswap.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
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
