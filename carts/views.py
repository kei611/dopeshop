import datetime
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cart, CartItem, Order, Payment
from store.models import Product, Variation
from django.core.exceptions import ObjectDoesNotExist

from django.conf import settings

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    # get the product
    product = Product.objects.get(id=product_id)
    product_variation = []
    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass
    try:
        # get the cart using the cart_id present in the session
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    cart.save()
    
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        # existing variation -> database
        # current variation -> product_variation
        # item_id -> database
        ex_var_list = []
        id = []
        for item in cart_item:
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))
            id.append(item.id)
            
        if product_variation in ex_var_list:
            # increase the cart item quantity
            index = ex_var_list.index(product_variation)
            item_id = id[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)
            item.save()
    else:
        cart_item = CartItem.objects.create(
            product = product, 
            quantity = 1, 
            cart = cart, 
        )
        if len(product_variation) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        cart_item.save()
    return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass 

    context = {
        'total': total, 
        'quantity': quantity, 
        'cart_items': cart_items, 
        'tax': tax, 
        'grand_total': grand_total, 
    }
    return render(request, 'store/cart.html', context)


import stripe
def checkout(request, total=0, quantity=0, cart_items=None):
    stripe.api_key = settings.STRIPE_API_KEY
    
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        line_items = []

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

            line_item = create_line_item(
                cart_item.product.price, cart_item.product.product_name, cart_item.quantity, cart_item.product.stripe_price_id)
            line_items.append(line_item)

    except ObjectDoesNotExist:
        pass 

    try:
        checkout_session = stripe.checkout.Session.create(
            shipping_address_collection={"allowed_countries": settings.ALLOWED_COUNTRIES},
            payment_method_types=['card'],
            line_items=line_items,
            shipping_options=create_shipping(),
            mode='payment',
            success_url=f'{settings.MY_URL}/cart/success/', 
            cancel_url=f'{settings.MY_URL}/cart/cancel/', 
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(status=400)
        
def create_shipping():
    shipping_items = []
    shipping_items.append({"shipping_rate": "shr_1MSkBDBpT7ryj6PXh6G8JE1p"})
    # shipping_items.append({"shipping_rate": "shr_1MSkqcBpT7ryj6PX8uB7jnjM"})
    return shipping_items


def create_line_item(unit_amount, name, quantity, stripe_price_id):
    return {
        'price': stripe_price_id, 
        'quantity': quantity,
    }
    
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
@csrf_exempt
def my_webhook_view(request):
    stripe.api_key = settings.STRIPE_API_KEY
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        create_order(session)
        create_payments(session)

    return HttpResponse(status=200)
    
def create_order(session):
    order = Order()
    order.full_name = session['customer_details']['name']
    order.phone = session['customer_details']['phone']
    order.email = session['customer_details']['email']
    order.address_line_1 = session['customer_details']['address']['line1']
    order.address_line_2 = session['customer_details']['address']['line2']
    order.country = session['customer_details']['address']['country']
    order.state = session['customer_details']['address']['state']
    order.city = session['customer_details']['address']['city']
    order.order_total = session['amount_total']
    order.save()
    
    # Generate order number
    yr = int(datetime.date.today().strftime('%Y'))
    dt = int(datetime.date.today().strftime('%d'))
    mt = int(datetime.date.today().strftime('%m'))
    d = datetime.date(yr, mt, dt)
    current_date = d.strftime("%Y%m%d") #20221228
    order_number = current_date + str(order.id)
    order.order_number = order_number
    order.save()
    
    print("Creating order")
        
def create_payments(session):
    # Store transaction details inside Payment model
    payment = Payment()
    payment.payment_id = session['id']
    payment.payment_method = session['payment_method_types']
    payment.amount_paid = session['amount_total']
    payment.status = session['payment_status'] 
    
    payment.save()

def create_orderProduct_clear_cart(request):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    for item in cart_items:
        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    
    # Clear cart
    CartItem.objects.filter(cart=cart, is_active=True).delete()         
    
def success(request):
    create_orderProduct_clear_cart(request)
    return render(request, 'orders/success.html')

def cancel(request):
    return render(request, 'orders/cancel.html')