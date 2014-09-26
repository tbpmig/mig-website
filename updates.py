print "processing python updates..."
from requirements.models import DistinctionType
DAs=DistinctionType.objects.filter(name__contains='DA')
for da in DAs:
    da.display_order=1
    da.save()

PAs = DistinctionType.objects.filter(name__contains='PA')
for pa in PAs:
    pa.display_order=2
    pa.save()

print "finished processing python updates."