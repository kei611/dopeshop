from django.shortcuts import render
from .models import Product, ProductGallery
from carts.views import _cart_id

# Create your views here.

def store(request):
    products = Product.objects.all().filter(is_available=True)
    
    context = {
        'products': products, 
    }

    return render(request, 'store/store.html', context)

def product_detail(request, product_slug):
    try:
        single_product = Product.objects.get(slug=product_slug)
    except Exception as e:
        raise e
        
    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    
    context = {
        'single_product': single_product, 
        'product_gallery': product_gallery, 
    }
    return render(request, 'store/product_detail.html', context)
