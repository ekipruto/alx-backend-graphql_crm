import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


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
