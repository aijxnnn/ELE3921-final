from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Min, Case, When, IntegerField, Value
from .models import MenuItem, PizzaTopping, Order, OrderItem, MenuItemSize
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, QueryDict
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login
from .forms import CreateUserForm, EditAccountForm
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

def index(request):
    all_items = MenuItem.objects.filter(category__in=['pizza', 'drink'])

    pizzas = {}
    drinks = {}

    for item in all_items:
        item.min_price = item.item_variant.aggregate(Min('price'))['price__min']
        if item.category == 'pizza':
            pizzas[item.name] = item
        elif item.category == 'drink':
            drinks[item.name] = item

    context = {
        'pizzas': pizzas.values(),
        'drinks': drinks.values(),
    }
    return render(request, "pizzeria/index.html", context)

def product_view(request, name):
    item = get_object_or_404(MenuItem, name=name, category__in=['pizza', 'drink'])
    item_sizes = MenuItemSize.objects.filter(item=item).order_by('price')
    all_toppings = list(MenuItem.objects.filter(category='topping'))

    if item.category == 'pizza':
        default_toppings = MenuItem.objects.filter(id__in=PizzaTopping.objects.filter(pizza=item).values_list('topping__id', flat=True))
        for topping in all_toppings:
            topping.size_prices = {
            s.size: float(s.price) for s in MenuItemSize.objects.filter(item=topping)
            }
        #create json for js dynamic pricing of toppings in the html 
        topping_prices_json = mark_safe(json.dumps({
            topping.id: topping.size_prices for topping in all_toppings}))
        
    else:
        default_toppings = []
        topping_prices_json = []
    
    return render(request, "pizzeria/product_view.html", {
        'item': item,
        'items': item_sizes,
        'item_name': item.name,
        'item_category': item.category,
        'all_toppings': all_toppings,
        'default_toppings': default_toppings,
        'topping_prices_json': topping_prices_json
    })

def add_to_cart(request):

    if not request.user.is_authenticated:
        if request.method == "POST":
            request.session['pending_cart'] = request.POST.dict()
            messages.info(request, "You must be logged in to add items to your cart.")
            return redirect(f"{reverse('login')}?next={reverse('add_to_cart')}")
        return redirect('index')

    # if returning from login, and a user tries creating a cart
    if request.method == "GET" and 'pending_cart' in request.session:
        # convert stored data back into POST format
        post_data = QueryDict('', mutable=True)
        post_data.update(request.session.pop('pending_cart'))
        request.POST = post_data
        request.method = "POST" 

    if request.method == "POST":
        selected_size = request.POST.get('size')
        category = request.POST.get('item_category')
        item = get_object_or_404(MenuItem, name=request.POST.get('item_name'), category=category)
        item_variant = MenuItemSize.objects.filter(item=item, size=selected_size).first()

        selected_extra_toppings = list(map(int, request.POST.getlist('extra_toppings')))
        selected_default_toppings = list(map(int, request.POST.getlist('default_toppings')))
        default_toppings = list(PizzaTopping.objects.filter(pizza=item).values_list('topping__id', flat=True))
        
        extra_toppings = [tid for tid in selected_extra_toppings]

        #if user removes a topping that is already there - it doesn't change anything w the price that's why it's different
        removed_toppings = [tid for tid in default_toppings if tid not in selected_default_toppings]
        #TODO: toping prices in view cart 
        extra_toppings_list =[]
        toppings_price = 0
        for tid in extra_toppings:
            topping = get_object_or_404(MenuItem, id=tid)
            topping_size = MenuItemSize.objects.filter(item=topping, size=selected_size).first()
            if topping_size:
                toppings_price += float(topping_size.price)

        total_price = float(item_variant.price) + toppings_price
        print(total_price)
        print(extra_toppings_list)

        cart_item = {
            'item_name': item.name,
            'item_size': selected_size,
            'item_price': float(item_variant.price),
            'extra_toppings': extra_toppings,
            'removed_toppings': removed_toppings,
            'total_price': total_price,
            'image_filename': item.image_filename,
        }

        cart = request.session.get('cart', [])
        cart.append(cart_item)
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f"{item.name} ({selected_size}) added to your cart!")
        print("POST data:", request.POST)   
        print(messages) 
        return redirect('index')

    return redirect('index')

def view_cart(request):
    cart = request.session.get('cart', [])
    cart_items = []
    total = 0

    for item in cart:

        extra_toppings = MenuItem.objects.filter(id__in=item.get('extra_toppings', []))
        for topping in extra_toppings:
            topping.price = MenuItemSize.objects.filter(item=topping, size=item.get('item_size')).first().price

        removed_toppings = MenuItem.objects.filter(id__in=item.get('removed_toppings', []))

        cart_items.append({
            'name': item.get('item_name'),
            'size': item.get('item_size'),
            'base_price': item.get('item_price'),
            'extra_toppings': extra_toppings,
            'removed_toppings': removed_toppings,
            'total_price': item.get('total_price'),
            'image_filename': item.get('image_filename'),
        })
               
        total = total + item.get('total_price', 0)
        request.session['cart_total'] = total
        request.session.modified = True
    print(total)
    return render(request, 'pizzeria/cart.html', 
        {
        'cart_items': cart_items,
        'total': total }
        )

def clear_cart(request):
    request.session['cart'] = []
    request.session.modified = True
    return redirect('cart')

def remove_item(request):
    if request.method == "POST":

        index = int(request.POST.get("item_index"))

        cart = request.session.get('cart', [])
  
        removed_item = cart.pop(index)
        request.session['cart'] = cart
        request.session.modified = True

        messages.success(request, f"Removed {removed_item['item_name']} ({removed_item['item_size']}) from your cart.")

    return redirect('cart')

def order(request):

    cart = request.session.get('cart', [])
    
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')
    
    order_total = request.session.get('cart_total', 0)

    order = Order.objects.create(
        user=request.user,
        total_price=order_total
    )

    for item in cart:
        extra_ids   = item.get('extra_toppings', [])
        removed_ids = item.get('removed_toppings', [])

        extra_names   = list(MenuItem.objects.filter(id__in=extra_ids).values_list('name', flat=True))
        removed_names = list(MenuItem.objects.filter(id__in=removed_ids).values_list('name', flat=True))

        OrderItem.objects.create(
            order            = order,
            item_name        = item['item_name'],
            item_size        = item['item_size'],
            extra_toppings   = ', '.join(extra_names),
            removed_toppings = ', '.join(removed_names),
            total_item_price = item['total_price']
        )

    request.session['cart'] = []
    request.session.modified = True

    messages.success(request, f"Order #{order.id} placed!")
    return redirect('index')

def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if 'pending_cart' in request.session:
                return redirect('add_to_cart')
            return redirect('index')
    else:
        form = CreateUserForm()
    
    return render(request, 'pizzeria/register.html', {'form': form})
   
def edit_account_view(request):
    if request.method == 'POST':
        form = EditAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account')
    else:
        form = EditAccountForm(instance=request.user)

    return render(request, 'pizzeria/edit_account.html', {'form': form})

def account_view(request):
    return render(request, "pizzeria/account.html", {"user": request.user})

def my_orders(request):
    cutoff = timezone.now() - timedelta(days=1)

    orders = Order.objects.filter(user=request.user).annotate(
        status_order=Case(
            When(status='Pending', then=Value(0)),
            When(status='Preparing', then=Value(1)),
            When(status='Ready', then=Value(2)),
            default=Value(99),
            output_field=IntegerField()
        )
    ).order_by('status_order', '-created_at').prefetch_related('items')

    recent_orders = orders.filter(created_at__gte=cutoff)
    old_orders = orders.filter(created_at__lt=cutoff)

    return render(request, 'pizzeria/my_orders.html', {
        'recent_orders': recent_orders,
        'old_orders': old_orders
    })

def manage_orders(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")
        order = get_object_or_404(Order, id=order_id)
        if new_status in dict(Order.ORDER_STATUS):
            order.status = new_status
            order.save()

    orders = (
        Order.objects
            .all()
            .order_by('status', '-created_at')
            .prefetch_related('items')
    )
        
    pending_orders = orders.filter(status='pending').order_by('-created_at')
    preparing_orders = orders.filter(status='preparing').order_by('-created_at')
    complete_orders = orders.filter(status='complete').order_by('-created_at')

    order_groups = [
        ("Pending Orders", pending_orders),
        ("Preparing Orders", preparing_orders),
        ("Completed Orders", complete_orders),
    ]
    return render(request, 'pizzeria/manage_orders.html', {
        'pending_orders': pending_orders,
        'order_groups': order_groups,
        'preparing_orders': preparing_orders,
        'complete_orders': complete_orders,
        'status_choices': Order.ORDER_STATUS,
    })