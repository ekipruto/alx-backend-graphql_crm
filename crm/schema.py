import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.db.models import F
from crm.models import Product
from django.db.models import Sum, Count
# ==========================================
# GraphQL Types (represent database models)
# ==========================================

class CustomerNode(DjangoObjectType):
    """GraphQL type for Customer model with relay support"""
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (relay.Node,)
        fields = ('id', 'name', 'email', 'phone', 'created_at', 'orders')


class ProductNode(DjangoObjectType):
    """GraphQL type for Product model with relay support"""
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (relay.Node,)
        fields = ('id', 'name', 'price', 'stock', 'created_at')


class OrderNode(DjangoObjectType):
    """GraphQL type for Order model with relay support"""
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (relay.Node,)
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at')


# Also keep the original types for mutations
class CustomerType(DjangoObjectType):
    """GraphQL type for Customer model"""
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at', 'orders')


class ProductType(DjangoObjectType):
    """GraphQL type for Product model"""
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'created_at')


class OrderType(DjangoObjectType):
    """GraphQL type for Order model"""
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at')


# ==========================================
# Input Types (for mutations)
# ==========================================

class CustomerInput(graphene.InputObjectType):
    """Input type for creating a customer"""
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    """Input type for creating a product"""
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)


class OrderInput(graphene.InputObjectType):
    """Input type for creating an order"""
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# ==========================================
# Mutations (same as before)
# ==========================================

class CreateCustomer(graphene.Mutation):
    """Mutation to create a single customer"""
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        try:
            if Customer.objects.filter(email=input.email).exists():
                raise ValidationError("Email already exists")
            
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.get('phone')
            )
            
            customer.full_clean()
            customer.save()
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


class BulkCreateCustomers(graphene.Mutation):
    """Mutation to create multiple customers at once"""
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    
    @staticmethod
    def mutate(root, info, input):
        customers_created = []
        errors = []
        
        for idx, customer_data in enumerate(input):
            try:
                if Customer.objects.filter(email=customer_data.email).exists():
                    errors.append(f"Row {idx + 1}: Email {customer_data.email} already exists")
                    continue
                
                customer = Customer(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.get('phone')
                )
                
                customer.full_clean()
                customer.save()
                
                customers_created.append(customer)
            
            except ValidationError as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=customers_created,
            errors=errors if errors else None
        )


class CreateProduct(graphene.Mutation):
    """Mutation to create a product"""
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        try:
            if input.price <= 0:
                raise ValidationError("Price must be positive")
            
            stock = input.get('stock', 0)
            if stock < 0:
                raise ValidationError("Stock cannot be negative")
            
            product = Product(
                name=input.name,
                price=input.price,
                stock=stock
            )
            
            product.full_clean()
            product.save()
            
            return CreateProduct(
                product=product,
                message="Product created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


class CreateOrder(graphene.Mutation):
    """Mutation to create an order with products"""
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    message = graphene.String()
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                raise ValidationError(f"Customer with ID {input.customer_id} does not exist")
            
            if not input.product_ids or len(input.product_ids) == 0:
                raise ValidationError("At least one product must be selected")
            
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    raise ValidationError(f"Product with ID {product_id} does not exist")
            
            order = Order(
                customer=customer,
                order_date=input.get('order_date')
            )
            order.save()
            
            order.products.set(products)
            order.calculate_total()
            
            return CreateOrder(
                order=order,
                message="Order created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


# ==========================================
# Queries with Filtering
# ==========================================

class Query(graphene.ObjectType):
    """
    CRM queries with filtering support
    """
    
    # Filtered queries using DjangoFilterConnectionField
    all_customers = DjangoFilterConnectionField(CustomerNode)
    all_products = DjangoFilterConnectionField(ProductNode)
    all_orders = DjangoFilterConnectionField(OrderNode)
    
    # Single item queries
    customer = relay.Node.Field(CustomerNode)
    product = relay.Node.Field(ProductNode)
    order = relay.Node.Field(OrderNode)


# ==========================================
# Mutations
# ==========================================

class Mutation(graphene.ObjectType):
    """All CRM mutations"""
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
class Query(graphene.ObjectType):
    """Main Query class with all resolvers"""
    
    # Add this hello field for health checks
    hello = graphene.String(
        name=graphene.String(default_value="World"),
        description="Simple health check endpoint"
    )
    
    # Your existing fields...
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        # ... rest of your fields
    )
    
    # ... rest of your Query class
    
    def resolve_hello(self, info, name):
        """Resolver for hello field - health check"""
        return f"Hello {name}! CRM GraphQL API is responsive."


# Your schema export
schema = graphene.Schema(query=Query)
class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update low-stock products (stock < 10).
    Increments stock by 10 to simulate restocking.
    """
    
    class Arguments:
        # No arguments needed - automatically finds low stock products
        pass
    
    # Return fields
    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)
    updated_count = graphene.Int()
    
    def mutate(self, info):
        """
        Execute the mutation to restock low-stock products.
        """
        try:
            # Find products with stock less than 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            # Count products before update
            count = low_stock_products.count()
            
            if count == 0:
                return UpdateLowStockProducts(
                    success=True,
                    message="No low-stock products found. All products have sufficient stock.",
                    updated_products=[],
                    updated_count=0
                )
            
            # Get list of products before updating (for return)
            products_list = list(low_stock_products)
            
            # Update stock by incrementing by 10
            # Using F() expression for atomic update
            low_stock_products.update(stock=F('stock') + 10)
            
            # Refresh products from database to get updated values
            updated_products = Product.objects.filter(
                id__in=[p.id for p in products_list]
            )
            
            return UpdateLowStockProducts(
                success=True,
                message=f"Successfully restocked {count} low-stock product(s). Stock increased by 10 units each.",
                updated_products=list(updated_products),
                updated_count=count
            )
        
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error restocking products: {str(e)}",
                updated_products=[],
                updated_count=0
            )


class Mutation(graphene.ObjectType):
    """
    Main Mutation class containing all mutations.
    """
    update_low_stock_products = UpdateLowStockProducts.Field()
    
    # Add other mutations here as needed
    # create_customer = CreateCustomer.Field()
    # create_order = CreateOrder.Field()


# Update schema to include Mutation
schema = graphene.Schema(query=Query, mutation=Mutation)

class Query(graphene.ObjectType):
    """Main Query class with all resolvers"""
    
    # ... your existing fields ...
    
    # Aggregation queries for reports
    total_customers = graphene.Int(description="Total number of customers")
    total_orders = graphene.Int(description="Total number of orders")
    total_revenue = graphene.Float(description="Total revenue from all orders")
    
    # CRM statistics (combined query)
    crm_stats = graphene.Field(
        'CRMStatsType',
        description="Combined CRM statistics"
    )
    
    # ... rest of your existing queries ...
    
    def resolve_total_customers(self, info):
        """Return total number of customers"""
        return Customer.objects.count()
    
    def resolve_total_orders(self, info):
        """Return total number of orders"""
        return Order.objects.count()
    
    def resolve_total_revenue(self, info):
        """Return total revenue from all orders"""
        result = Order.objects.aggregate(total=Sum('total_amount'))
        return float(result['total'] or 0)
    
    def resolve_crm_stats(self, info):
        """Return combined CRM statistics"""
        total_customers = Customer.objects.count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        
        return {
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue)
        }


# Add a new type for CRM statistics (before Query class)
class CRMStatsType(graphene.ObjectType):
    """Type for CRM statistics"""
    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()
