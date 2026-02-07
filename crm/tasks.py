"""
Celery Tasks for CRM Application
Contains asynchronous tasks for report generation and other background jobs.
"""

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
import sys
import requests
# GraphQL client imports
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError


def get_graphql_client():
    """
    Create and return a GraphQL client for querying CRM data.
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
        fetch_schema_from_transport=False,
    )
    
    return client


@shared_task(name='crm.tasks.generate_crm_report')
def generate_crm_report():
    """
    Generate a weekly CRM report summarizing:
    - Total number of customers
    - Total number of orders
    - Total revenue
    
    Scheduled to run every Monday at 6:00 AM.
    Logs report to /tmp/crm_report_log.txt
    
    Returns:
        bool: True if successful, False otherwise
    """
    log_file = '/tmp/crm_report_log.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Define GraphQL query for CRM statistics
    query = gql("""
        query {
            totalCustomers
            totalOrders
            totalRevenue
        }
    """)
    
    try:
        # Execute GraphQL query
        client = get_graphql_client()
        result = client.execute(query)
        
        # Extract data
        total_customers = result.get('totalCustomers', 0)
        total_orders = result.get('totalOrders', 0)
        total_revenue = result.get('totalRevenue', 0.0)
        
        # Format report message
        report_message = (
            f"{timestamp} - Report: "
            f"{total_customers} customers, "
            f"{total_orders} orders, "
            f"${total_revenue:.2f} revenue."
        )
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write('=' * 80 + '\n')
            f.write(f'[{timestamp}] Weekly CRM Report\n')
            f.write('=' * 80 + '\n')
            f.write(f'Total Customers: {total_customers}\n')
            f.write(f'Total Orders: {total_orders}\n')
            f.write(f'Total Revenue: ${total_revenue:.2f}\n')
            f.write('=' * 80 + '\n\n')
        
        # Also write summary format as specified
        with open(log_file, 'a') as f:
            f.write(report_message + '\n')
        
        # Print to stdout (appears in Celery logs)
        print(f'[CRM REPORT] {report_message}')
        
        return True
    
    except TransportQueryError as e:
        error_message = f"{timestamp} - ERROR: GraphQL query failed - {str(e)}"
        
        with open(log_file, 'a') as f:
            f.write(f'[{error_message}]\n')
        
        print(f'[CRM REPORT ERROR] {error_message}', file=sys.stderr)
        return False
    
    except Exception as e:
        error_message = f"{timestamp} - ERROR: {str(e)}"
        
        with open(log_file, 'a') as f:
            f.write(f'[{error_message}]\n')
        
        print(f'[CRM REPORT ERROR] {error_message}', file=sys.stderr)
        return False


@shared_task(name='crm.tasks.test_celery')
def test_celery():
    """
    Simple test task to verify Celery is working.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"[{timestamp}] Celery test task executed successfully!"
    print(message)
    return message


@shared_task(name='crm.tasks.manual_report')
def manual_report():
    """
    Manual trigger for CRM report generation (for testing).
    """
    return generate_crm_report()
