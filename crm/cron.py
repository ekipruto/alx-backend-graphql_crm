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
# ... existing imports and functions ...

def update_low_stock():
    """
    Execute GraphQL mutation to update low-stock products.
    Runs every 12 hours to restock products with stock < 10.
    
    Logs:
        - Product names and new stock levels
        - Timestamp
        - File: /tmp/low_stock_updates_log.txt
    """
    log_file = '/tmp/low_stock_updates_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    # Define GraphQL mutation
    mutation = gql("""
        mutation {
            updateLowStockProducts {
                success
                message
                updatedCount
                updatedProducts {
                    id
                    name
                    stock
                    price
                }
            }
        }
    """)
    
    try:
        # Execute mutation
        client = get_graphql_client()
        result = client.execute(mutation)
        
        # Extract result data
        data = result.get('updateLowStockProducts', {})
        success = data.get('success', False)
        message = data.get('message', 'No response')
        updated_count = data.get('updatedCount', 0)
        updated_products = data.get('updatedProducts', [])
        
        # Prepare log message
        with open(log_file, 'a') as f:
            # Log header
            f.write(f"\n{'='*70}\n")
            f.write(f"[{timestamp}] Low Stock Update Job Started\n")
            f.write(f"{'='*70}\n")
            
            if success:
                f.write(f"[{timestamp}] ✓ {message}\n")
                
                if updated_count > 0:
                    f.write(f"[{timestamp}] Updated {updated_count} product(s):\n\n")
                    
                    # Log each updated product
                    for idx, product in enumerate(updated_products, 1):
                        f.write(f"  {idx}. Product: {product['name']}\n")
                        f.write(f"     New Stock Level: {product['stock']} units\n")
                        f.write(f"     Price: ${product['price']}\n")
                        f.write(f"     Product ID: {product['id']}\n")
                        f.write(f"     ---\n")
                else:
                    f.write(f"[{timestamp}] No products needed restocking.\n")
            else:
                f.write(f"[{timestamp}] ✗ Error: {message}\n")
            
            # Log footer
            completion_time = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            f.write(f"\n[{completion_time}] Low stock update job completed.\n")
            f.write(f"{'='*70}\n")
        
        # Print to stdout (appears in cron logs)
        print(f"[LOW STOCK UPDATE] {timestamp} - {message}")
        
        return True
    
    except Exception as e:
        error_message = f"{timestamp} ERROR: {str(e)}"
        
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"[{error_message}]\n")
            f.write(f"{'='*70}\n")
        
        print(f"[LOW STOCK UPDATE ERROR] {error_message}", file=sys.stderr)
        return False


def test_low_stock_update():
    """
    Test function to manually verify low stock update works.
    Run with: python manage.py shell
    >>> from crm.cron import test_low_stock_update
    >>> test_low_stock_update()
    """
    print("Testing low stock update...")
    result = update_low_stock()
    
    if result:
        print("✓ Low stock update executed successfully")
        print("\nLog contents:")
        with open('/tmp/low_stock_updates_log.txt', 'r') as f:
            lines = f.readlines()
            # Show last 30 lines
            for line in lines[-30:]:
                print(line.rstrip())
    else:
        print("✗ Low stock update failed")
    
    return result


# Update __all__ to include new functions
__all__ = ['log_crm_heartbeat', 'test_heartbeat', 'update_low_stock', 'test_low_stock_update']
