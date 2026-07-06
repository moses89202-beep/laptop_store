from .models import *
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import *
from django.db.models import Sum, Count, Q, IntegerField
from django.db.models.functions import Coalesce



def home(request):
    successful_order_items_filter = Q(
        orderitem__order__payment_status='completed',
        orderitem__order__delivery_status__in=['delivered', 'picked_up']
    )

    laptops = (
        Laptop.objects
        .annotate(
            total_ordered_quantity=Coalesce(
                Sum(
                    'orderitem__quantity',
                    filter=successful_order_items_filter
                ),
                0,
                output_field=IntegerField()
            ),
            order_item_appearances=Coalesce(
                Count(
                    'orderitem',
                    filter=successful_order_items_filter
                ),
                0,
                output_field=IntegerField()
            )
        )
        .filter(total_ordered_quantity__gt=0)
        .order_by(
            '-total_ordered_quantity',
            '-order_item_appearances',
            'id'
        )[:3]
    )

    return render(request, 'home.html', {
        'laptops': laptops
    })

def laptop_catalog(request):
    queryset = Laptop.objects.all().order_by('-created_at')

    search_query = request.GET.get('search', '').strip()

    if search_query and search_query != 'None':
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(cpu__icontains=search_query) |
            Q(gpu__icontains=search_query) |
            Q(ram__icontains=search_query) |
            Q(storage__icontains=search_query) |
            Q(os__icontains=search_query)
        )

    get_clean = lambda key: (
        request.GET.get(key, '').strip() or None
    ) if request.GET.get(key, '').strip() not in ['', 'None'] else None

    brand = get_clean('brand')
    ram = get_clean('ram')
    cpu = get_clean('cpu')
    gpu = get_clean('gpu')
    os_system = get_clean('os')
    storage = get_clean('storage')
    screen_size = get_clean('screen_size')
    max_price = get_clean('max_price')
    in_stock = request.GET.get('in_stock') == '1'

    if brand:
        queryset = queryset.filter(brand__iexact=brand)

    if ram:
        queryset = queryset.filter(ram__icontains=ram)

    if cpu:
        queryset = queryset.filter(cpu__icontains=cpu)

    if gpu:
        queryset = queryset.filter(gpu__icontains=gpu)

    if os_system:
        queryset = queryset.filter(os__icontains=os_system)

    if storage:
        queryset = queryset.filter(storage__icontains=storage)

    if screen_size:
        queryset = queryset.filter(screen_size=screen_size)

    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    if in_stock:
        queryset = queryset.filter(quantity__gt=0)

    sort_by = get_clean('sort')

    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'date_asc':
        queryset = queryset.order_by('created_at')
    elif sort_by == 'date_desc':
        queryset = queryset.order_by('-created_at')

    distinct_brands = Laptop.objects.values_list('brand', flat=True).distinct().order_by('brand')
    distinct_rams = Laptop.objects.values_list('ram', flat=True).distinct().order_by('ram')
    distinct_cpus = Laptop.objects.values_list('cpu', flat=True).distinct().order_by('cpu')
    distinct_gpus = Laptop.objects.exclude(gpu__isnull=True).exclude(gpu='').values_list('gpu', flat=True).distinct().order_by('gpu')
    distinct_storage = Laptop.objects.values_list('storage', flat=True).distinct().order_by('storage')
    distinct_screens = Laptop.objects.values_list('screen_size', flat=True).distinct().order_by('screen_size')
    distinct_os = Laptop.objects.exclude(os__isnull=True).exclude(os='').values_list('os', flat=True).distinct().order_by('os')

    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'brands': distinct_brands,
        'rams': distinct_rams,
        'cpus': distinct_cpus,
        'gpus': distinct_gpus,
        'storage_options': distinct_storage,
        'screen_sizes': distinct_screens,
        'os_options': distinct_os,
        'in_stock': in_stock,
    }

    return render(request, 'catalog.html', context)

def cart_page(request):
    return render(request, 'cart.html')

def cart_items_api(request):
    id_string = request.GET.get('ids', '')

    if not id_string:
        return JsonResponse({'items': []})

    try:
        product_ids = [
            int(x.strip())
            for x in id_string.split(',')
            if x.strip().isdigit()
        ]

        laptops = Laptop.objects.filter(id__in=product_ids)

        items_data = []

        for laptop in laptops:
            items_data.append({
                'id': laptop.id,
                'name': laptop.name,
                'brand': laptop.brand,
                'price': float(laptop.price),
                'processor': laptop.cpu,
                'ram': laptop.ram,
                'storage': laptop.storage,
                'available_quantity': laptop.quantity,
                'image_url': laptop.image.url if laptop.image else ''
            })

        return JsonResponse({'items': items_data})

    except Exception as e:
        return JsonResponse({'error': str(e), 'items': []}, status=400)

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account was created successfully.")
            return redirect('home')
    else:
        form = CustomerSignupForm()
    return render(request, 'account/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomerLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = CustomerLoginForm()
    return render(request, 'account/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    customer_profile = get_object_or_404(Customer, user=request.user)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer_profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=customer_profile, user=request.user)

    return render(request, 'account/profile.html', {
        'form': form,
        'customer': customer_profile
    })


@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')
        
    return redirect('profile')