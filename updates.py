print "processing python updates..."
from electees.models import ElecteeResource,ElecteeResourceType
from mig_main.models import Standing

grad_standing = Standing.objects.get(name='Graduate')
grad_packets = ElecteeResource.objects.filter(resource_type__name='Grad Packet')
for gp in grad_packets:
    gp.standing = grad_standing
    gp.save()

new_type =ElecteeResourceType(name='Packet',is_packet=True)
new_type.save()

packets = ElecteeResource.objects.filter(resource_type__is_packet=True)
for packet in packets:
    packet.resource_type=new_type
    packet.save()
packet_types = ElecteeResourceType.objects.filter(is_packet=True).exclude(name='Packet')   
packet_types.delete() 
print "finished processing python updates."