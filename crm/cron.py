"""
CRM Cron Jobs Module
Contains scheduled tasks for the CRM application.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure Django is set up
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()

# Import after Django setup
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError


def get_graphql_client():
    """
    Create and return a GraphQL client for health checks.
    """
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql',
        use_json=True,
        headers={'Content-Type': 'application/json'},
        verify=True,
        retries=3,
        timeout=10,
    )
    
    client = Client(
        transport=transport,
        fetch_schema_from_transport=False,  # Don't fetch schema for performance
    )
    
    return client


def query_graphql_hello():
    """
    Query the GraphQL hello field to verify endpoint is responsive.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    query = gql("""
        query {
            hello(name: "Heartbeat")
        }
    """)
    
    try:
        client = get_graphql_client()
        result = client.execute(query)
        
        if result and 'hello' in result:
            return True, result['hello']
        else:
            return False, "No response from GraphQL hello field"
    
    except TransportQueryError as e:
        return False, f"GraphQL query error: {str(e)}"
    
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health.
    
    Format: DD/MM/YYYY-HH:MM:SS CRM is alive
    File: /tmp/crm_heartbeat_log.txt
    
    Also queries GraphQL hello field to verify endpoint responsiveness.
    """
    # Log file path
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    # Get current timestamp in required format: DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    # Base heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"
    
    # Query GraphQL endpoint for health check
    graphql_success, graphql_message = query_graphql_hello()
    
    # Prepare full log message
    if graphql_success:
        status = "✓ GraphQL endpoint responsive"
        full_message = f"{heartbeat_message} - {status}"
    else:
        status = f"✗ GraphQL endpoint issue: {graphql_message}"
        full_message = f"{heartbeat_message} - {status}"
    
    # Append to log file
    try:
        with open(log_file, 'a') as f:
            f.write(full_message + '\n')
        
        # Print to stdout (will appear in cron logs)
        print(f"[HEARTBEAT] {full_message}")
        
        return True
    
    except Exception as e:
        error_message = f"{timestamp} ERROR: Failed to write heartbeat log - {str(e)}"
        print(f"[HEARTBEAT ERROR] {error_message}", file=sys.stderr)
        return False


def test_heartbeat():
    """
    Test function to manually verify heartbeat logging works.
    Run with: python manage.py shell
    >>> from crm.cron import test_heartbeat
    >>> test_heartbeat()
    """
    print("Testing heartbeat logging...")
    result = log_crm_heartbeat()
    
    if result:
        print("✓ Heartbeat logged successfully")
        print("\nLog contents:")
        with open('/tmp/crm_heartbeat_log.txt', 'r') as f:
            print(f.read())
    else:
        print("✗ Heartbeat logging failed")
    
    return result


# Make functions available for django-crontab
__all__ = ['log_crm_heartbeat', 'test_heartbeat']
