import factory

from requirements.models import SemesterType


class SemesterTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = SemesterType
    name = factory.Iterator(['Winter', 'Summer', 'Fall'])
