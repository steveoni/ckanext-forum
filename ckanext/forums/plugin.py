"""
CKAN Issue Extension
"""
from logging import getLogger
log = getLogger(__name__)

import ckan.plugins as p
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins import implements, toolkit
from ckan.lib.helpers import ckan_version

from ckanext.forums.views.issues import forums
from ckanext.forums.views.moderation import moderation



# Imports are done in methods to speed up paster.
# Please don't move back up to here.

class IssuesPlugin(p.SingletonPlugin, DefaultTranslation):
    """
    CKAN Issues Extension
    """
    implements(p.ITranslation)
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
        toolkit.add_resource('assets', 'forums')


    # IClick
    def get_commands(self):
        """CLI commands - Creates or Updated issues data tables"""       
        import click

        @click.command()
        def forumsdb():
            """Creates issues data tables"""
            from ckanext.forums.model import setup
            setup()

        @click.command()
        def issuesupdate():
            """Updates issues data tables"""
            from ckanext.forums.model import upgrade
            upgrade()
            print('Issues tables are up to date')

        return [forumsdb, issuesupdate]
    
    # ITemplateHelpers
    def get_helpers(self):
        from ckanext.forums.lib import util, helpers
        return {
            'forum_installed': lambda: True,
            'forum_count': util.forum_count,
            'forum_comment_count': util.forum_comment_count,
            'forum_enabled_for_organization':
                helpers.forum_enabled_for_organization,
            'replace_url_param': helpers.replace_url_param,
            'get_forum_filter_types': helpers.get_forum_filter_types,
            'get_forum_per_page': helpers.get_forum_per_page,
            'forum_enabled': helpers.forum_enabled,
            'forum_list': helpers.forum_list,
            'forum_user_has_reported_issue':
                helpers.forum_user_has_reported_issue,
            'forum_user_is_owner':
                helpers.forum_user_is_owner,
            'forum_users_who_reported_issue':
                helpers.forum_users_who_reported_issue,
        }

    
    # IBlueprint
    def get_blueprint(self):
        return [forums, moderation]


    # IActions
    def get_actions(self):
        import ckanext.forums.logic.action as action

        return dict((name, function) for name, function
                    in action.__dict__.items()
                    if callable(function))


    # IAuthFunctions
    def get_auth_functions(self):
        import ckanext.forums.auth as auth
        return {
            'forum_admin': auth.forum_admin,
            'forum_search': auth.forum_search,
            'forum_show': auth.forum_show,
            'forum_create': auth.forum_create,
            'forum_comment_create': auth.forum_comment_create,
            'forum_update': auth.forum_update,
            'forum_delete': auth.forum_delete,
            'forum_report': auth.forum_report,
            'forum_report_clear': auth.forum_report_clear,
            'forum_comment_search': auth.forum_comment_search,
        }
        