import pytest

from ckan import model
from ckan.lib import search
from ckan.tests import factories

from ckanext.forums.tests import factories as issue_factories
from ckanext.forums.logic import validators
from ckanext.forums.tests.fixtures import issues_setup

@pytest.fixture
def dataset():
    return factories.Dataset()


class TestAsPackageId(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_given_name_returns_id(self, dataset):
        package_id = validators.as_package_id(dataset['name'],
                                              context={
                                                  'model': model,
                                                  'session': model.Session})
        assert dataset['id'] == package_id

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_given_id_returns_id(self, dataset):
        package_id = validators.as_package_id(dataset['id'],
                                              context={
                                                  'model': model,
                                                  'session': model.Session})
        assert dataset['id'] == package_id
