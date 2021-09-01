import pytest

from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, user


@pytest.fixture
def dataset():
    return factories.Dataset()

@pytest.fixture
def issue(user, dataset):
    return issue_factories.Issue(user=user,
                                 user_id=user['id'],
                                 dataset_id=dataset['id'])

@pytest.fixture
def comment(issue, user):
    comment = issue_factories.IssueComment(
                    user_id=user['id'],
                    issue_number=issue['number'],
                    dataset_id=issue['dataset_id'],)
    return comment

class TestIssueApi(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_search_api(self, app, user, dataset, issue, comment):
        response = app.get("/api/3/action/issue_search", extra_environ={})
        assert 200 == response._status_code