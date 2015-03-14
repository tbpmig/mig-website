import factory

from mig_main.models import AcademicTerm
from mig_main.tests.factories import OfficerPositionFactory, MemberProfileFactory
from history.models import Officer, GoverningDocument, GoverningDocumentType

class OfficerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Officer
    user            = factory.SubFactory(MemberProfileFactory)   
    position        = factory.SubFactory(OfficerPositionFactory)
    website_bio     = 'I have a bio'
    website_photo   = factory.django.ImageField(from_path='migweb/test_photos/about_flower.jpg')
    
    @factory.post_generation
    def term(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for term in extracted:
                self.term.add(term)
        else:
            self.term.add(AcademicTerm.get_current_term())


class DocumentTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocumentType
    name = factory.Iterator(['Constitution','Bylaws'])


class OldDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocument
    id = factory.Sequence(lambda n:n)
    document_type = factory.LazyAttribute(lambda o:GoverningDocumentType.objects.get(name='Constitution') if o.id %2 else GoverningDocumentType.objects.get(name='Bylaws'))
    active = False
    pdf_file = factory.django.FileField(from_path='migweb/test_docs/test.pdf')


class CurrentDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocument
    id = factory.Sequence(lambda n:n)
    document_type = factory.LazyAttribute(lambda o:GoverningDocumentType.objects.get(name='Constitution') if o.id %2 else GoverningDocumentType.objects.get(name='Bylaws'))
    active = True
    pdf_file = factory.django.FileField(from_path='migweb/test_docs/test.pdf')