from member_resources.models import ActiveList, GradElecteeList, UndergradElecteeList
from mig_main.models import UserProfile, MemberProfile
from mig_main.utility import get_dropdowns
from migweb.settings import DEBUG
def profile_setup(request):
    profile = MemberProfile.objects.filter(uniqname=request.user.username)
    if profile.exists():
        if profile.filter(status__name='Active').exists():
            return {'is_active_member':True,
                'is_ugrad_electee':False,
                'is_grad_electee':False,
                'needs_profile':False}
        elif profile.filter(standing__name='Undergraduate').exists():
            return {'is_active_member':False,
                'is_ugrad_electee':True,
                'is_grad_electee':False,
                'needs_profile':False}
        else:
            return {'is_active_member':False,
                'is_ugrad_electee':False,
                'is_grad_electee':True,
                'needs_profile':False}

    is_active_member = ActiveList.objects.filter(uniqname=request.user.username).exists()
    is_ugrad_electee = UndergradElecteeList.objects.filter(uniqname=request.user.username).exists()
    is_grad_electee = GradElecteeList.objects.filter(uniqname=request.user.username).exists()

    needs_profile = not UserProfile.objects.filter(uniqname=request.user.username).exists()
    return {'is_active_member':is_active_member,
            'is_ugrad_electee':is_ugrad_electee,
            'is_grad_electee':is_grad_electee,
            'needs_profile':needs_profile}

def debug_features(request):
    return {'debug_features':DEBUG}

def dropdowns(request):
    return {'mig_dropdowns':get_dropdowns(request.user)}
