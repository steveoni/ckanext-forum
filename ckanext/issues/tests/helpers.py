from ckan.lib.search import clear_all
from ckan.tests import helpers



class ClearOnSetupClassMixin(object):
    @classmethod
    def setupClass(self):
        helpers.reset_db()
        clear_all()


class ClearOnTearDownMixin(object):
    def teardown(self):
        helpers.reset_db()
        clear_all()
