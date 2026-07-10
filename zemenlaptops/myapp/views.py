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

from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from .models import Laptop

from django.shortcuts import render
from django.db.models import Avg, Count, Max, Q
from django.core.paginator import Paginator
from .models import Laptop  # Adjust this import based on your app structure
from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator
from .models import Laptop  # Adjust this import based on your app structure

from django.shortcuts import render
from django.db.models import Avg, Count, Q, FloatField
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from .models import Laptop # Adjust this import depending on your app structure

def laptop_catalog(request):
    queryset = Laptop.objects.all()

    # ✅ Force avg_rating to be a FloatField to prevent Decimal-to-float comparison failures in Django templates
    queryset = queryset.annotate(
        avg_rating=Cast(Avg('reviews__rating'), output_field=FloatField()),
        review_count=Count('reviews')
    ).order_by('-created_at')

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

    # ✅ Sorting
    sort_by = get_clean('sort')

    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'date_asc':
        queryset = queryset.order_by('created_at')
    elif sort_by == 'date_desc':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'rating_desc':
        queryset = queryset.order_by('-avg_rating', '-review_count')

    # ✅ Distinct filters
    distinct_brands = Laptop.objects.values_list('brand', flat=True).distinct().order_by('brand')
    distinct_rams = Laptop.objects.values_list('ram', flat=True).distinct().order_by('ram')
    distinct_cpus = Laptop.objects.values_list('cpu', flat=True).distinct().order_by('cpu')
    distinct_gpus = Laptop.objects.exclude(gpu__isnull=True).exclude(gpu='').values_list('gpu', flat=True).distinct().order_by('gpu')
    distinct_storage = Laptop.objects.values_list('storage', flat=True).distinct().order_by('storage')
    distinct_screens = Laptop.objects.values_list('screen_size', flat=True).distinct().order_by('screen_size')
    distinct_os = Laptop.objects.exclude(os__isnull=True).exclude(os='').values_list('os', flat=True).distinct().order_by('os')

    # ✅ Pagination
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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer, Review
from .forms import ReviewForm, CustomerProfileForm  # Assuming CustomerProfileForm is imported here

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

    # Fetch user's reviews along with laptop data to avoid N+1 queries
    user_reviews = Review.objects.filter(customer=customer_profile).select_related('laptop')

    return render(request, 'account/profile.html', {
        'form': form,
        'customer': customer_profile,
        'reviews': user_reviews,
    })

@login_required
def update_review(request, review_id):
    customer_profile = get_object_or_404(Customer, user=request.user)
    # Ensure users can only update their own reviews
    review = get_object_or_404(Review, id=review_id, customer=customer_profile)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated successfully!")
        else:
            messages.error(request, "There was an error updating your review.")
    return redirect('profile')

@login_required
def delete_review(request, review_id):
    customer_profile = get_object_or_404(Customer, user=request.user)
    # Ensure users can only delete their own reviews
    review = get_object_or_404(Review, id=review_id, customer=customer_profile)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Your review has been removed.")
    return redirect('profile')


@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')
        
    return redirect('profile')


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count, Q
from .models import Laptop, Review
from app2.models import Order, OrderItem
from .forms import ReviewForm

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count, Q
from decimal import Decimal  # ✅ Required to fix the multiplication error
from .models import Laptop, Review
from django.contrib import messages # Import messages for debugging

def laptop_detail(request, pk):
    laptop = get_object_or_404(Laptop, pk=pk)
    reviews = laptop.reviews.select_related('customer__user')

    # Rating statistics
    rating_data = reviews.aggregate(average=Avg('rating'), count=Count('id'))
    average_rating = round(rating_data['average'] or 0, 1)
    review_count = rating_data['count']

    # Recommended Logic
    has_gpu = laptop.gpu is not None and laptop.gpu != ""
    price_range_min = laptop.price * Decimal('0.8')
    price_range_max = laptop.price * Decimal('1.2')
    recommended = Laptop.objects.filter(
        price__gte=price_range_min, price__lte=price_range_max
    ).exclude(id=laptop.id)
    
    if has_gpu:
        recommended = recommended.exclude(gpu__isnull=True).exclude(gpu__exact='')
    else:
        recommended = recommended.filter(Q(gpu__isnull=True) | Q(gpu__exact=''))
    recommended = recommended[:4]

    # ✅ IMPROVED REVIEW PERMISSION LOGIC
    can_review = False
    
    if request.user.is_authenticated:
        # 1. Safely get the customer profile
        customer = getattr(request.user, 'customer_profile', None)
        
        if customer:
            # 2. Check for delivered items
            # We look for ANY order that contains this laptop and is marked delivered/picked_up
            valid_orders = OrderItem.objects.filter(
                laptop=laptop,
                order__customer=customer,
                order__delivery_status__in=['delivered', 'picked_up']
            )

            # 3. Check if already reviewed
            already_reviewed = Review.objects.filter(
                customer=customer, 
                laptop=laptop
            ).exists()

            if valid_orders.exists() and not already_reviewed:
                can_review = True
            
            # --- DEBUGGING (Remove this after fixing) ---
            # if not valid_orders.exists():
            #    print(f"DEBUG: No delivered orders found for {request.user.username}")
            # if already_reviewed:
            #    print(f"DEBUG: {request.user.username} already reviewed this.")
        else:
            print(f"DEBUG: User {request.user.username} has no Customer Profile attached.")

    # Handle Review Submit
    if request.method == "POST" and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.customer = request.user.customer_profile
            review.laptop = laptop
            review.save()
            return redirect('laptop_detail', pk=laptop.pk)
    else:
        form = ReviewForm()

    context = {
        'laptop': laptop,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_count': review_count,
        'recommended': recommended,
        'can_review': can_review,
        'form': form,
    }
    return render(request, 'laptop_detail.html', context)