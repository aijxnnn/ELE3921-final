from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Min
from .models import MenuItem, PizzaTopping, Order, OrderItem, MenuItemSize
import json
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

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
        'items': item_sizes,
        'item_name': item.name,
        'item_category': item.category,
        'all_toppings': all_toppings,
        'default_toppings': default_toppings,
        'topping_prices_json': topping_prices_json
    })

def add_to_cart(request):
    if request.method == "POST":
        selected_size = request.POST.get('size')
        item = get_object_or_404(MenuItem, name=request.POST.get('item_name'))
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
    print(total)
    return render(request, 'pizzeria/cart.html', 
        {
        'cart_items': cart_items,
        'total': total }
        )


#TODO combine clear cart and remove_item? 
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

def place_order(request):

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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'pizzeria/register.html', {'form': form})