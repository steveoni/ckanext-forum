"""
CKAN Issue Extension
"""
from logging import getLogger
log = getLogger(__name__)

import ckan.plugins as p
from ckan.plugins import implements, toolkit

from ckanext.issues.views.issues import issues
from ckanext.issues.views.moderation import moderation



# Imports are done in methods to speed up paster.
# Please don't move back up to here.

class IssuesPlugin(p.SingletonPlugin):
    """
    CKAN Issues Extension
    """
    implements(p.IConfigurer, inherit=True)
    implements(p.ITemplateHelpers, inherit=True)
    implements(p.IActions)
    implements(p.IAuthFunctions)
    implements(p.IClick)
    implements(p.IBlueprint)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'issues')


    # IClick
    def get_commands(self):
        """CLI commands - Creates or Updated issues data tables"""       
        import click

        @click.command()
        def issuesdb():
            """Creates issues data tables"""
            from ckanext.issues.model import setup
            setup()

        @click.command()
        def issuesupdate():
            """Updates issues data tables"""
            from ckanext.issues.model import upgrade
            upgrade()
            print('Issues tables are up to date')

        return [issuesdb, issuesupdate]
    
    # ITemplateHelpers
    def get_helpers(self):
        from ckanext.issues.lib import util, helpers
        return {
            'issues_installed': lambda: True,
            'issue_count': util.issue_count,
            'issue_comment_count': util.issue_comment_count,
            'issues_enabled_for_organization':
                helpers.issues_enabled_for_organization,
            'replace_url_param': helpers.replace_url_param,
            'get_issue_filter_types': helpers.get_issue_filter_types,
            'get_issues_per_page': helpers.get_issues_per_page,
            'issues_enabled': helpers.issues_enabled,
            'issues_list': helpers.issues_list,
            'issues_user_has_reported_issue':
                helpers.issues_user_has_reported_issue,
            'issues_user_is_owner':
                helpers.issues_user_is_owner,
            'issues_users_who_reported_issue':
                helpers.issues_users_who_reported_issue,
        }

    
    # IBlueprint
    def get_blueprint(self):
        return [issues, moderation]


    # IActions
    def get_actions(self):
        import ckanext.issues.logic.action as action

        return dict((name, function) for name, function
                    in action.__dict__.items()
                    if callable(function))


    # IAuthFunctions
    def get_auth_functions(self):
        import ckanext.issues.auth as auth
        return {
            'issue_admin': auth.issue_admin,
            'issue_search': auth.issue_search,
            'issue_show': auth.issue_show,
            'issue_create': auth.issue_create,
            'issue_comment_create': auth.issue_comment_create,
            'issue_update': auth.issue_update,
            'issue_delete': auth.issue_delete,
            'issue_report': auth.issue_report,
            'issue_report_clear': auth.issue_report_clear,
            'issue_comment_search': auth.issue_comment_search,
        }
        