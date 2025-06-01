from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Min
from .models import MenuItem, PizzaTopping, Order, OrderItem, MenuItemSize
import json
from django.utils.safestring import mark_safe

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

        all_selected_toppings = list(map(int, request.POST.getlist('default_toppings') + request.POST.getlist('extra_toppings')))

        default_toppings = list(PizzaTopping.objects.filter(pizza=item).values_list('topping__id', flat=True))
        extra_toppings = [tid for tid in all_selected_toppings if tid not in default_toppings]
        removed_toppings = [tid for tid in default_toppings if tid not in all_selected_toppings]

        toppings_price = 0
        for tid in extra_toppings:
            topping = get_object_or_404(MenuItem, id=tid)
            topping_size = MenuItemSize.objects.filter(item=topping, size=selected_size).first()
            if topping_size:
                toppings_price += float(topping_size.price)

        total_price = float(item_variant.price) + toppings_price

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
        return redirect('index')

    return redirect('index')