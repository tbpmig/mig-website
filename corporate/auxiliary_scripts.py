import os
import zipfile
import shutil

from django.db.models import Q
from django.template.defaultfilters import slugify

from corporate.models import CorporateResourceGuide
from mig_main.models import Major, MemberProfile, Standing
from mig_main.utility import zipdir
from migweb.settings import PROJECT_PATH, MEDIA_ROOT

RESUMES_BY_MAJOR_LOCATION = os.path.sep.join([MEDIA_ROOT,'Resumes_by_major'])
RESUMES_BY_YEAR_LOCATION = os.path.sep.join([MEDIA_ROOT,'Resumes_by_year'])

def compile_resumes():
    shutil.rmtree(RESUMES_BY_MAJOR_LOCATION)
    os.makedirs(RESUMES_BY_MAJOR_LOCATION)
    resource_guides = CorporateResourceGuide.objects.filter(active=True)
    if resource_guides:
        shutil.copy(PROJECT_PATH+resource_guides[0].resource_guide.url,os.path.sep.join([RESUMES_BY_MAJOR_LOCATION,slugify(resource_guides[0].name)+'.pdf']))
    for resume_major in Major.objects.all():
        query=Q(major=resume_major)
        users_in_major = MemberProfile.get_members().filter(query)
        for user in users_in_major:
            if user.resume:
                major_dir = os.path.sep.join([RESUMES_BY_MAJOR_LOCATION,slugify(resume_major.name)])
                if not os.path.exists(major_dir):
                    os.makedirs(major_dir)
                resume_name=slugify(user.last_name+'_'+user.first_name+'_'+user.uniqname)+'.pdf'
                shutil.copy(PROJECT_PATH+user.resume.url,os.path.sep.join([major_dir,resume_name]))
    if os.path.exists(RESUMES_BY_YEAR_LOCATION):
        shutil.rmtree(RESUMES_BY_YEAR_LOCATION)
    os.makedirs(RESUMES_BY_YEAR_LOCATION)
    if resource_guides:
        shutil.copy(PROJECT_PATH+resource_guides[0].resource_guide.url,os.path.sep.join([RESUMES_BY_YEAR_LOCATION,slugify(resource_guides[0].name)+'.pdf']))
    not_alum = ~Q(name='Alumni')
    for standing in Standing.objects.all():
        members = MemberProfile.get_members().filter(standing=standing)
        if standing.name == 'Alumni':
            status_dir = os.path.sep.join([RESUMES_BY_YEAR_LOCATION,slugify(standing.name)])
        else:
            status_dir = os.path.sep.join([RESUMES_BY_YEAR_LOCATION, slugify(standing.name)+'-student'])
        if not os.path.exists(status_dir):
            os.makedirs(status_dir)
        for user in members:
            if user.resume:
                current_grad_year = user.expect_grad_date.year
                year_dir = os.path.sep.join([status_dir,'Graduating'+slugify(current_grad_year)])
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                resume_name=slugify(user.last_name+'_'+user.first_name+'_'+user.uniqname)+'.pdf'
                shutil.copy(PROJECT_PATH+user.resume.url,os.path.sep.join([year_dir,resume_name]))

def update_resume_zips():
    compile_resumes()
    current_path = os.getcwd()
    zip_file_name = os.sep.join([MEDIA_ROOT,'TBP_resumes_by_major.zip'])
    try:
        os.remove(zip_file_name)
    except OSError:
        pass
    zip_f = zipfile.ZipFile(zip_file_name,'w')
    os.chdir(RESUMES_BY_MAJOR_LOCATION)
    zipdir('.',zip_f)
    zip_f.close()
    zip_file_name_year = os.sep.join([MEDIA_ROOT,'TBP_resumes_by_year.zip'])
    try:
        os.remove(zip_file_name_year)
    except OSError:
        pass
    zip_f = zipfile.ZipFile(zip_file_name_year,'w')
    os.chdir(RESUMES_BY_YEAR_LOCATION)
    zipdir('.',zip_f)
    zip_f.close()
    os.chdir(current_path)