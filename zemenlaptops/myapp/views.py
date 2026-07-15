from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import *
from django.db.models import FloatField, Sum, Count, Q, IntegerField, Avg
from django.db.models.functions import Coalesce
from .models import *
from app2.models import OrderItem
from decimal import Decimal
from django.db.models.functions import Cast



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


from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Count
from .models import Laptop  # Adjust this import to match your app structure

def laptop_catalog(request):
    # 1. Base Queryset with Annotations for Ratings
    queryset = Laptop.objects.annotate(
        avg_rating=Avg('reviews__rating'),  # Adjust 'reviews__rating' based on your Review model relation
        review_count=Count('reviews')
    )

    # 2. Extract Query Parameters
    search_query = request.GET.get('search', '').strip()
    brand_filter = request.GET.get('brand', '').strip()
    ram_filter = request.GET.get('ram', '').strip()
    storage_filter = request.GET.get('storage', '').strip()
    gpu_filter = request.GET.get('gpu', '').strip()
    os_filter = request.GET.get('os', '').strip()
    in_stock_filter = request.GET.get('in_stock', '').strip()
    sort_by = request.GET.get('sort', 'date_desc').strip()

    # 3. Apply Filters
    if search_query:
        queryset = queryset.filter(name__icontains=search_query) | queryset.filter(brand__icontains=search_query)
    if brand_filter:
        queryset = queryset.filter(brand=brand_filter)
    if ram_filter:
        queryset = queryset.filter(ram=ram_filter)
    if storage_filter:
        queryset = queryset.filter(storage=storage_filter)
    if gpu_filter:
        queryset = queryset.filter(gpu=gpu_filter)
    if os_filter:
        queryset = queryset.filter(os=os_filter)
    if in_stock_filter == '1':
        queryset = queryset.filter(quantity__gt=0)

    # 4. Apply Sorting
    if sort_by == 'date_asc':
        queryset = queryset.order_by('created_at')  # Adjust field names to match your model
    elif sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'rating_desc':
        queryset = queryset.order_by('-avg_rating')
    else:
        queryset = queryset.order_by('-created_at')  # Default: Newest Arrivals

    # 5. Dynamically Fetch Distinct Options for Sidebar Dropdowns
    brands = Laptop.objects.exclude(brand__isnull=True).exclude(brand="").values_list('brand', flat=True).distinct().order_by('brand')
    rams = Laptop.objects.exclude(ram__isnull=True).exclude(ram="").values_list('ram', flat=True).distinct().order_by('ram')
    storage_options = Laptop.objects.exclude(storage__isnull=True).exclude(storage="").values_list('storage', flat=True).distinct().order_by('storage')
    gpus = Laptop.objects.exclude(gpu__isnull=True).exclude(gpu="").values_list('gpu', flat=True).distinct().order_by('gpu')
    os_options = Laptop.objects.exclude(os__isnull=True).exclude(os="").values_list('os', flat=True).distinct().order_by('os')

    # 6. Pagination (e.g., 9 laptops per page)
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # 7. Context Construct
    context = {
        'page_obj': page_obj,
        
        # Dropdown Option Lists
        'brands': brands,
        'rams': rams,
        'storage_options': storage_options,
        'gpus': gpus,
        'os_options': os_options,
        
        # State Preservation
        'selected_brand': brand_filter,
        'selected_ram': ram_filter,
        'selected_storage': storage_filter,
        'selected_gpu': gpu_filter,
        'selected_os': os_filter,
        'in_stock': in_stock_filter == '1',
        'selected_sort': sort_by,
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

    user_reviews = Review.objects.filter(customer=customer_profile).select_related('laptop')

    return render(request, 'account/profile.html', {
        'form': form,
        'customer': customer_profile,
        'reviews': user_reviews,
    })


@login_required
def update_review(request, review_id):
    customer_profile = get_object_or_404(Customer, user=request.user)
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



def laptop_detail(request, pk):
    laptop = get_object_or_404(Laptop, pk=pk)
    reviews = laptop.reviews.select_related('customer__user')
    rating_data = reviews.aggregate(average=Avg('rating'), count=Count('id'))
    average_rating = round(rating_data['average'] or 0, 1)
    review_count = rating_data['count']

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

    can_review = False
    
    if request.user.is_authenticated:
        customer = getattr(request.user, 'customer_profile', None)
        
        if customer:
            valid_orders = OrderItem.objects.filter(
                laptop=laptop,
                order__customer=customer,
                order__delivery_status__in=['delivered', 'picked_up']
            )
            already_reviewed = Review.objects.filter(
                customer=customer, 
                laptop=laptop
            ).exists()

            if valid_orders.exists() and not already_reviewed:
                can_review = True
        else:
            print(f"DEBUG: User {request.user.username} has no Customer Profile attached.")


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