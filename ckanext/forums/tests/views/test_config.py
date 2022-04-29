import pytest

from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.forums.tests import factories as issue_factories
from ckanext.forums.tests.fixtures import issues_setup, owner


class TestEnabledForDatasets(object):
    @pytest.fixture
    def config(self, ckan_config):
        ckan_config['ckanext.forums.enabled_for_datasets'] = 'dataset-enabled'
        return ckan_config

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_dataset_enabled_by_config(self, app, config):
        dataset_enabled = factories.Dataset(name='dataset-enabled')
        response = app.get(toolkit.url_for('issues.dataset',
                                     dataset_id=dataset_enabled['id']))
        assert config["ckanext.forums.enabled_for_datasets"] == 'dataset-enabled'
        assert response._status_code == 200

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_other_datasets_disabled(self, app, config):
        dataset = factories.Dataset()
        response = app.get(toolkit.url_for('issues.dataset',
                                     dataset_id=dataset['id']))
        assert response._status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cant_enable_with_extra_with_this_config(self, app, config):
        '''test that issues are disabled even with the extra forum_enabled
        set'''
        dataset_misleading_extra = factories.Dataset(
                            extras=[{
                                'key': 'forum_enabled',
                                'value': True
                            }],
        )

        response = app.get(toolkit.url_for('issues.dataset',
                            dataset_id=dataset_misleading_extra['id']))
        assert response._status_code == 404


class TestEnabledForOrganizations(object):
    @pytest.fixture
    def config(self, ckan_config):
        ckan_config['ckanext.forums.enabled_for_organizations'] = 'enabled-org'
        ckan_config['ckanext.forums.enabled_for_datasets'] = 'random-dataset'
        return ckan_config

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_dataset_enabled_by_config(self, app, config):
        enabled_org = factories.Organization(name='enabled-org')
        dataset_enabled = factories.Dataset(name='dataset-enabled',
                                            owner_org=enabled_org['id'])
        response = app.get(toolkit.url_for('issues.dataset',
                                     dataset_id=dataset_enabled['id']))
        assert response._status_code == 200

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_other_datasets_disabled(self, app, config):
        dataset = factories.Dataset()
        response = app.get(toolkit.url_for('issues.dataset',
                                        dataset_id=dataset['id']))
        assert response._status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_org_enabled_by_config(self, app, config):
        enabled_org = factories.Organization(name='enabled-org')
        response = app.get(toolkit.url_for('issues.issues_for_organization',
                                            org_id=enabled_org['id']))
        assert response._status_code == 200

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_other_orgs_disabled(self, app, config):
        org = factories.Organization(name='org')
        response = app.get(toolkit.url_for('issues.issues_for_organization',
                                            org_id=org['id']))
        assert response._status_code == 404

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cant_enable_dataset_with_extra_with_this_config(self, app, config):
        '''test that issues are disabled even with the extra forum_enabled
        set'''
        dataset_misleading_extra = factories.Dataset(extras=[{
                                                    'key': 'forum_enabled',
                                                    'value': True
                                                    }])
        response = app.get(toolkit.url_for('issues.dataset',
                                    dataset_id=dataset_misleading_extra['id']))
        assert response._status_code == 404

class TestDatasetExtra(object):
    @pytest.fixture
    def org(self, owner):
        return factories.Organization(user=owner)

    @pytest.fixture
    def dataset(self, owner, org):
        return factories.Dataset(user=owner,
                                owner_org=org['name'],
                                name='test-dataset')

    @pytest.fixture
    def issue(self, owner, dataset):
        return issue_factories.Issue(user=owner,
                                    user_id=owner['id'],
                                    dataset_id=dataset['id'],
                                    visibility='hidden')

    @pytest.fixture
    def config(self, ckan_config):
        ckan_config['ckanext.forums.enabled_without_extra'] = 'false'
        return ckan_config                         

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issues_disabled_for_test_dataset(self, app, config, owner, dataset):
        '''test-dataset has no extra'''
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues_dataset',
                                    dataset_id=dataset['id']),
                                    extra_environ=env,
                                    expect_errors=True
        )
        assert 404 == response._status_code

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issues_enabled_for_test_dataset_1(self, app, config, owner, org):
        dataset_1 = factories.Dataset(
            user=owner,
            extras=[{
                'key': 'forum_enabled',
                'value': True
            }],
            owner_org=org['name'])
        env = {'REMOTE_USER': owner['name'].encode('ascii')}
        response = app.get(toolkit.url_for('issues.dataset',
                            dataset_id=dataset_1['id']),
                            extra_environ=env)
        assert 200 == response._status_code
