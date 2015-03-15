import tempfile
import shutil

from django.test.runner import DiscoverRunner

from django.conf import settings

class MigTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super(MigTestRunner,self).setup_test_environment(**kwargs)
        print 'setup whole thing.'
        self.OLD_MEDIA = settings.MEDIA_ROOT
        self.temp_dir = tempfile.mkdtemp(suffix='foo').replace('\\','/')
        settings.MEDIA_ROOT = self.temp_dir + '/media/'
        
        
    def teardown_test_environment(self, **kwargs):
        super(MigTestRunner,self).teardown_test_environment(**kwargs)
        shutil.rmtree(self.temp_dir,ignore_errors=True)
        settings.MEDIA_ROOT = self.OLD_MEDIA