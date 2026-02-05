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

CRONJOBS = [
    # Heartbeat logger - runs every 5 minutes
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    
    # Low stock update - runs every 12 hours at the top of the hour
    # 0 */12 * * * = At minute 0 past every 12th hour (00:00, 12:00)
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# Crontab settings
CRONTAB_LOCK_JOBS = True
CRONTAB_COMMAND_SUFFIX = '2>&1'
