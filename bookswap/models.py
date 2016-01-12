from django.db import models
from django.core.validators import RegexValidator

from stdimage import StdImageField
from localflavor.us.models import USStateField # , USZipCodeField

from mig_main.pdf_field import ContentTypeRestrictedFileField, pdf_types
from mig_main.models import AcademicTerm

def default_term():
    """ Returns the current term.

    Fixes a serialization issue that results from circular references in
    migrations.
    """
    return AcademicTerm.get_current_term().id

def contract_file_name(instance, filename):
    """ Returns the filename for a contract.

    Fixes serialization loop issue.
    """
    return '/'.join([
            u'bookswap_contracts',
            (instance.get_type_display() + '_' +
             instance.term.get_abbreviation() + u'.pdf')
        ])


# Create your models here.
class BookSwapContract(models.Model):
    """ Contracts for buyers or sellers"""
    TYPE_CHOICES = (
        ('S', 'Seller'),
        ('B', 'Buyer'),
    )
    contract_file = ContentTypeRestrictedFileField(
        upload_to=contract_file_name,
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=True
    )
    term = models.ForeignKey('mig_main.AcademicTerm', default=default_term)
    type = models.CharField(
            max_length=1,
            choices=TYPE_CHOICES,
            default='S'
    )

    def __unicode__(self):
        return (self.term.get_abbreviation() + ' ' +
                self.get_type_display() + ' Contract')


class LocationImage(models.Model):
    """ One of the images used to advertise the location of Book Swap"""
    photo = StdImageField(
            upload_to='bookswap_photos',
            variations={'thumbnail': (1050, 790, True)}
    )
    super_caption = models.TextField(blank=True, null=True)
    sub_caption = models.TextField()
    display_order = models.PositiveSmallIntegerField()

    @classmethod
    def get_images(cls):
        return cls.objects.all().order_by('display_order', 'id')


class FAQItem(models.Model):
    """ One of the FAQ items"""
    title = models.TextField()
    text = models.TextField()
    display_order = models.PositiveSmallIntegerField()

    @classmethod
    def get_faqs(cls):
        return cls.objects.all().order_by('display_order', 'title')


class BookSwapPerson(models.Model):
    """ Extends user profile information to include data needed for Book Swap.
    """
    user_profile = models.OneToOneField('mig_main.UserProfile')
    UMID = models.CharField(
            max_length=8,
            validators=[RegexValidator(
                            regex=r'^[0-9]{8}$',
                            message="Your UMID must be 8 numbers."
                        )
                        ]
    )
    address1 = models.CharField(max_length=128, blank=True, null=True)
    address2 = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    state = USStateField(blank=True, null=True)
    # zip = USZipCodeField(blank=True, null=True)
    barcode = models.CharField(max_length=256, unique=True)


class BookType(models.Model):
    """The book in the 'class' sense. Contains book meta-data"""

    author = models.CharField(max_length=256, blank=True, null=True)
    edition = models.CharField(max_length=64, blank=True, null=True)
    isbn = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    course = models.CharField(max_length=128, blank=True, null=True)


class Book(models.Model):
    """An individual book to be bought or sold"""
    price = models.PositiveSmallIntegerField()
    buyer = models.ForeignKey(BookSwapPerson, null=True, blank=True, related_name='books_bought')
    seller = models.ForeignKey(BookSwapPerson, related_name='books_sold')
    book_type = models.ForeignKey(BookType)
    term = models.ForeignKey('mig_main.AcademicTerm', default=default_term)


class BookSwapStatus(models.Model):
    selling_enabled = models.BooleanField(default=False)
    receiving_enabled = models.BooleanField(default=False)
    display_prices = models.BooleanField(default=False)
    term = models.ForeignKey('mig_main.AcademicTerm', unique=True)
    
    @classmethod
    def can_sell(cls, term):
        stat = cls.objects.filter(term=term)
        if stat.exists():
            return stat[0].selling_enabled
        return False
    
    @classmethod
    def can_receive(cls, term):
        stat = cls.objects.filter(term=term)
        if stat.exists():
            return stat[0].receiving_enabled
        return False