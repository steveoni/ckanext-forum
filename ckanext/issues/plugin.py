"""
CKAN Issue Extension
"""
from logging import getLogger
log = getLogger(__name__)

import ckan.plugins as p
from ckan.plugins import implements, toolkit

from ckanext.issues.lib import util, helpers
from ckanext.issues.model import setup as model_setup
import ckanext.issues.logic.action as action
import ckanext.issues.auth as auth


class IssuesPlugin(p.SingletonPlugin):
    """
    CKAN Issues Extension
    """
    implements(p.IConfigurable)
    implements(p.IConfigurer, inherit=True)
    implements(p.IRoutes, inherit=True)
    implements(p.ITemplateHelpers, inherit=True)
    implements(p.IActions)
    implements(p.IAuthFunctions)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def get_helpers(self):
        return {
            'issues_installed': lambda: True,
            'issue_count': util.issue_count,
            'issue_comment_count': util.issue_comment_count,
            'time_ago': util.time_ago,
            'replace_url_param': helpers.replace_url_param,
            'get_issue_filter_types': helpers.get_issue_filter_types,
            'get_issues_per_page': helpers.get_issues_per_page,
        }

    def configure(self, config):
        model_setup()

    def before_map(self, map):
        from ckan.config.routing import SubMapper

        with SubMapper(map, controller='ckanext.issues.controller:IssueController') as m:
            m.connect('issues_home', '/dataset/:package_id/issues', action='home')
            m.connect('issues_new', '/dataset/:package_id/issues/new',
                    action='new')
            m.connect('issues_edit', '/dataset/:package_id/issues/:id/edit',
                    action='edit')
            m.connect('issues_delete', '/dataset/:dataset_id/issues/:issue_id/delete',
                    action='delete')
            m.connect('issues_comments', '/dataset/:package_id/issues/:id/comments',
                    action='comments')
            m.connect('add_issue_with_resource', '/dataset/:package_id/issues/new/:resource_id', action='add')
            m.connect('issues_show', '/dataset/:package_id/issues/:id',
                    action='show')
            m.connect('all_issues_page', '/dataset/issues/all', action='all_issues_page')
            m.connect('publisher_issue_page', '/publisher/issues/:publisher_id', action='publisher_issue_page')

        return map

    def get_actions(self):
        return dict((name, function) for name, function
            in action.__dict__.items()
            if callable(function))

    def get_auth_functions(self):
        return {
            'issue_show': auth.issue_show,
            'issue_count': auth.issue_show,
            'issue_create': auth.issue_create,
            'issue_comment_create': auth.issue_comment_create,
            'issue_update': auth.issue_update,
            'issue_delete': auth.issue_delete,
        }
