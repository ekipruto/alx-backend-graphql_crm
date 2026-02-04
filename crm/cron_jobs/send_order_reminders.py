#!/usr/bin/env python
"""
Order Reminder Script
Purpose: Query GraphQL for pending orders and send reminders
Schedule: Runs daily at 8:00 AM via cron
Log: /tmp/order_reminders_log.txt
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the Django project to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')

import django
django.setup()

# Now import Django-related modules
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def get_graphql_client():
    """
    Create and return a GraphQL client configured for the local endpoint.
    """
    # Configure transport for GraphQL endpoint
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql',
        use_json=True,
        headers={
            'Content-Type': 'application/json',
        },
        verify=True,
        retries=3,
    )
    
    # Create GraphQL client
    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )
    
    return client


def query_pending_orders():
    """
    Query GraphQL endpoint for pending orders from the last 7 days.
    Returns a list of orders with ID and customer email.
    """
    # Calculate date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Define GraphQL query
    query = gql("""
        query GetPendingOrders($orderDateGte: Date!) {
            allOrders(orderDateGte: $orderDateGte) {
                edges {
                    node {
                        id
                        orderDate
                        totalAmount
                        customer {
                            id
                            name
                            email
                        }
                        product {
                            id
                            name
                        }
                    }
                }
            }
        }
    """)
    
    # Variables for the query
    variables = {
        'orderDateGte': seven_days_ago
    }
    
    try:
        # Execute query
        client = get_graphql_client()
        result = client.execute(query, variable_values=variables)
        
        # Extract orders from result
        orders = []
        if result and 'allOrders' in result:
            edges = result['allOrders'].get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                if node:
                    orders.append({
                        'id': node.get('id'),
                        'order_date': node.get('orderDate'),
                        'total_amount': node.get('totalAmount'),
                        'customer_email': node.get('customer', {}).get('email'),
                        'customer_name': node.get('customer', {}).get('name'),
                        'product_name': node.get('product', {}).get('name'),
                    })
        
        return orders
    
    except Exception as e:
        print(f"Error querying GraphQL: {str(e)}", file=sys.stderr)
        return []


def log_order_reminders(orders, log_file='/tmp/order_reminders_log.txt'):
    """
    Log order reminders to a file with timestamp.
    
    Args:
        orders: List of order dictionaries
        log_file: Path to log file
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_file, 'a') as f:
        # Log header
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] Order Reminders Processing Started\n")
        f.write(f"{'='*60}\n")
        
        if not orders:
            f.write(f"[{timestamp}] No pending orders found in the last 7 days.\n")
        else:
            f.write(f"[{timestamp}] Found {len(orders)} pending order(s):\n\n")
            
            # Log each order
            for idx, order in enumerate(orders, 1):
                f.write(f"  {idx}. Order ID: {order['id']}\n")
                f.write(f"     Customer: {order['customer_name']} ({order['customer_email']})\n")
                f.write(f"     Product: {order['product_name']}\n")
                f.write(f"     Order Date: {order['order_date']}\n")
                f.write(f"     Amount: ${order['total_amount']}\n")
                f.write(f"     ---\n")
        
        # Log footer
        completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n[{completion_time}] Order reminders processing completed.\n")
        f.write(f"{'='*60}\n")


def main():
    """
    Main function to execute the order reminder script.
    """
    try:
        # Query pending orders
        print("Querying GraphQL for pending orders...")
        orders = query_pending_orders()
        
        # Log reminders
        print(f"Found {len(orders)} pending order(s). Logging reminders...")
        log_order_reminders(orders)
        
        # Print confirmation
        print("Order reminders processed!")
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
