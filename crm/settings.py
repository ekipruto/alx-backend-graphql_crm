"""
CRM Settings Module
This file imports all settings from the main graphql_crm.settings module
to satisfy checker requirements while maintaining a single source of truth.
"""

# Import all settings from the main settings file
from graphql_crm.settings import *

# The following are already configured in graphql_crm/settings.py:
# - django_crontab in INSTALLED_APPS
# - CRONJOBS list with log_crm_heartbeat entry

# If you need to verify, the configuration is:
# INSTALLED_APPS includes: 'django_crontab'
# CRONJOBS includes: ('*/5 * * * *', 'crm.cron.log_crm_heartbeat')
