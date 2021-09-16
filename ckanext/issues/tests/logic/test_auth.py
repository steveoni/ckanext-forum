import pytest

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.tests.fixtures import issues_setup, user, owner

class TestIssueUpdate(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_org_editor_can_update_an_issue(self, user):
        org = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'editor'}]
        )
        dataset = factories.Dataset(owner_org=org['name'], private=True)
        user = helpers.call_action('get_site_user')
        issue = issue_factories.Issue(user=user, dataset_id=dataset['id'])

        context = {
            'user': user['name'],
            'model': model,
        }
        assert helpers.call_auth('issue_update',
                                context,
                                issue_number=issue['number'],
                                dataset_id=dataset['id'],
                                status='open')
        
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_owner_can_update_issue(self, owner):
        issue_owner = owner
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=issue_owner,
                                      user_id=issue_owner['id'],
                                      dataset_id=dataset['id'])

        context = {
            'user': issue_owner['name'],
            'model': model,
        }
        assert helpers.call_auth('issue_update',
                                context,
                                issue_number=issue['number'],
                                dataset_id=dataset['id'],
                                status='open')

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_organization_member_cannot_update_issue(self, user, owner):
        issue_owner = owner
        org = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'member'}]
        )
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=issue_owner,
                                      user_id=issue_owner['id'],
                                      dataset_id=dataset['id'])

        other_user = factories.User()
        context = {
            'user': other_user['name'],
            'model': model,
        }
        pytest.raises(
            toolkit.NotAuthorized,
            helpers.call_auth,
            'issue_update',
            context,
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            status='open'
        )

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_normal_user_cannot_update_issue(self, user, owner):
        issue_owner = owner
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=issue_owner,
                                      user_id=issue_owner['id'],
                                      dataset_id=dataset['id'])

        other_user = factories.User()
        context = {
            'user': other_user['name'],
            'model': model,
        }
        pytest.raises(
            toolkit.NotAuthorized,
            helpers.call_auth,
            'issue_update',
            context,
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            status='open'
        )

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_anonymous_user_cannot_update_issue(self, user, owner):
        issue_owner = owner
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=issue_owner,
                                      user_id=issue_owner['id'],
                                      dataset_id=dataset['id'])

        other_user = factories.User()
        context = {
            'user': other_user['name'],
            'model': model,
        }
        pytest.raises(
            toolkit.NotAuthorized,
            helpers.call_auth,
            'issue_update',
            context,
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            status='open'
        )


class TestIssueDelete(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_dataset_owner_can_delete_issue(self, owner):
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=owner,
                                      user_id=owner['id'],
                                      dataset_id=dataset['id'])

        context = {
            'user': owner['name'],
            'auth_user_obj': owner,
            'model': model,
            'session': model.Session,
        }
        assert helpers.call_auth('issue_delete', context, issue_id=issue['id'],
                          dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_owner_cannot_delete_on_a_dataset_they_do_not_own(self, user):
        # they aren't part of the org
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user=user,
                                      user_id=user['id'],
                                      dataset_id=dataset['id'])

        context = {
            'user': user['name'],
            'auth_user_obj': user,
            'model': model,
            'session': model.Session,
        }
        pytest.raises(toolkit.NotAuthorized, helpers.call_auth, 'issue_delete',
                      context, issue_id=issue['id'], dataset_id=dataset['id'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_user_cannot_delete_issue_they_do_not_own(self, user, owner):
        org = factories.Organization(user=owner)
        dataset = factories.Dataset(owner_org=org['name'])
        issue = issue_factories.Issue(user_id=owner['id'],
                                      dataset_id=dataset['id'])

        context = {
            'user': user['name'],
            'auth_user_obj': user,
            'model': model,
            'session': model.Session,
        }
        pytest.raises(toolkit.NotAuthorized, helpers.call_auth, 'issue_delete',
                      context, issue_id=issue['id'], dataset_id=dataset['id'])


class TestReport(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_any_user_can_report_an_issue(self, user):
        context = {
            'user': user['name'],
            'model': model,
        }
        assert helpers.call_auth('issue_report', context=context)

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_anon_users_cannot_report_issues(self):
        context = {
            'user': None,
            'model': model,
        }
        pytest.raises(toolkit.NotAuthorized, helpers.call_auth,
            'issue_report', context=context)
