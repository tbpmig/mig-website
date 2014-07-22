import imp
import os
from subprocess import call
MODULE_EXTENSIONS = ('.py', '.pyc', '.pyo')

def package_contents(package_name):
    file, pathname, description = imp.find_module(package_name)
    if file:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0]
        for module in os.listdir(pathname)
        if  module.endswith(MODULE_EXTENSIONS)])


def generate_pydoc(package_name):
    call(['pydoc','-w',package_name])
    call(['mv',package_name+'.html','/home/mikehand/migweb_wiki/pydoc_files/'])
    for subpackage in package_contents(package_name):
        call(['pydoc','-w',package_name+'.'+subpackage])
        call(['mv',package_name+'.'+subpackage+'.html','/home/mikehand/migweb_wiki/pydoc_files/'])

