from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from .forms import LaptopForm, UserForm, CustomerProfileForm, OrderForm
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q, Sum
from myapp.models import Laptop, Review
from app2.models import Order
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model

User = get_user_model()

@staff_member_required
def dashboard_home_view(request):
    # Base Stats
    total_laptops = Laptop.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_reviews = Review.objects.count()
    
    # Financial Analytics
    total_revenue = Order.objects.filter(payment_status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_revenue = Order.objects.filter(payment_status='pending').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Line Chart Data: Monthly Completed Orders & Revenue Trends
    monthly_data = (
        Order.objects.filter(payment_status='completed')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'), total=Sum('total_amount'))
        .order_by('month')
    )
    
    sales_labels = [d['month'].strftime('%b %Y') for d in monthly_data]
    sales_totals = [float(d['total']) for d in monthly_data]
    order_counts = [d['count'] for d in monthly_data]

    # Doughnut Chart Data: Distribution of Available Stock items by Brand
    brand_data = (
        Laptop.objects.values('brand')
        .annotate(stock=Sum('quantity'))
        .filter(stock__gt=0)
        .order_by('-stock')
    )
    
    brand_labels = [b['brand'] for b in brand_data]
    brand_stock = [b['stock'] for b in brand_data]

    context = {
        'total_laptops': total_laptops,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_reviews': total_reviews,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'sales_labels': sales_labels,
        'sales_totals': sales_totals,
        'order_counts': order_counts,
        'brand_labels': brand_labels,
        'brand_stock': brand_stock,
        'low_stock_laptops': Laptop.objects.filter(quantity__lte=3),
        'recent_orders': Order.objects.select_related('customer').order_by('-created_at')[:5]
    }
    return render(request, 'base_dashboard.html', context)


@staff_member_required
def laptop_manage_view(request, pk=None):
    instance = get_object_or_404(Laptop, pk=pk) if pk else None
    if request.method == 'POST' and 'delete_laptop' in request.POST and instance:
        instance.delete()
        return redirect('laptop_manage')

    form = LaptopForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and 'save_laptop' in request.POST and form.is_valid():
        saved_laptop = form.save()
        if instance:
            return redirect('laptop_edit', pk=saved_laptop.pk)
        return redirect('laptop_manage')

    if request.method == 'POST' and 'delete_review' in request.POST:
        review_id = request.POST.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        laptop_pk = review.laptop.pk
        review.delete()
        return redirect('laptop_edit', pk=laptop_pk)

    brands = Laptop.objects.values_list('brand', flat=True).distinct().order_by('brand')
    oses = Laptop.objects.values_list('os', flat=True).distinct().order_by('os')
    storages = Laptop.objects.values_list('storage', flat=True).distinct().order_by('storage')
    rams = Laptop.objects.values_list('ram', flat=True).distinct().order_by('ram')
    laptops_qs = Laptop.objects.all()
    low_stock_laptops = Laptop.objects.filter(quantity__lt=20).order_by('quantity')
    brand_filter = request.GET.get('brand', '')
    os_filter = request.GET.get('os', '')
    storage_filter = request.GET.get('storage', '')
    ram_filter = request.GET.get('ram', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'name')
    if brand_filter:
        laptops_qs = laptops_qs.filter(brand=brand_filter)
    if os_filter:
        laptops_qs = laptops_qs.filter(os=os_filter)
    if storage_filter:
        laptops_qs = laptops_qs.filter(storage=storage_filter)
    if ram_filter:
        laptops_qs = laptops_qs.filter(ram=ram_filter)
    if search_query:
        laptops_qs = laptops_qs.filter(
            Q(name__icontains=search_query) | 
            Q(brand__icontains=search_query) |
            Q(cpu__icontains=search_query)
        )
    laptops_qs = laptops_qs.annotate(num_orders=Count('orderitem'))
    laptops_qs = laptops_qs.annotate(avg_rating=Avg('reviews__rating'))
    if sort_by == 'name':
        laptops_qs = laptops_qs.order_by('brand', 'name')
    elif sort_by == '-name':
        laptops_qs = laptops_qs.order_by('-brand', '-name')
    elif sort_by == 'stock_asc':
        laptops_qs = laptops_qs.order_by('quantity')
    elif sort_by == 'stock_desc':
        laptops_qs = laptops_qs.order_by('-quantity')
    elif sort_by == 'rating_desc':
        laptops_qs = laptops_qs.order_by('-avg_rating')
    elif sort_by == 'rating_asc':
        laptops_qs = laptops_qs.order_by('avg_rating')
    elif sort_by == 'orders_desc':
        laptops_qs = laptops_qs.order_by('-num_orders')
    elif sort_by == 'orders_asc':
        laptops_qs = laptops_qs.order_by('num_orders')
    paginator = Paginator(laptops_qs, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    selected_reviews = []
    if instance:
        selected_reviews = instance.reviews.select_related('customer').all()

    return render(request, 'laptop_manage.html', {
        'page_obj': page_obj,
        'form': form,
        'selected_laptop': instance,
        'selected_reviews': selected_reviews,
        'low_stock_laptops': low_stock_laptops,
        'brands': brands,
        'oses': oses,
        'storages': storages,
        'rams': rams,
        'current_brand': brand_filter,
        'current_os': os_filter,
        'current_storage': storage_filter,
        'current_ram': ram_filter,
        'current_sort_by': sort_by,
        'current_q': search_query,
    })



@staff_member_required
def user_manage_view(request, pk=None):
    users_queryset = User.objects.select_related('customer_profile').all()
    if not request.user.is_superuser:
        users_queryset = users_queryset.filter(is_superuser=False)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        users_queryset = users_queryset.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(customer_profile__full_name__icontains=search_query) |
            Q(customer_profile__phone_number__icontains=search_query)
        )
    account_type_filter = request.GET.get('account_type', 'all')
    if account_type_filter == 'superuser' and request.user.is_superuser:
        users_queryset = users_queryset.filter(is_superuser=True)
    elif account_type_filter == 'staff':
        users_queryset = users_queryset.filter(is_staff=True, is_superuser=False)
    elif account_type_filter == 'customer':
        users_queryset = users_queryset.filter(is_staff=False, is_superuser=False)
    sort_by = request.GET.get('sort', 'username_asc')
    if sort_by == 'username_asc':
        users_queryset = users_queryset.order_by('username')
    elif sort_by == 'username_desc':
        users_queryset = users_queryset.order_by('-username')
    elif sort_by == 'date_desc':
        users_queryset = users_queryset.order_by('-date_joined')
    elif sort_by == 'date_asc':
        users_queryset = users_queryset.order_by('date_joined')
    else:
        users_queryset = users_queryset.order_by('-date_joined')
    paginator = Paginator(users_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if pk:
        if not request.user.is_superuser:
            user_instance = get_object_or_404(User.objects.filter(is_superuser=False), pk=pk)
        else:
            user_instance = get_object_or_404(User, pk=pk)
    else:
        user_instance = None

    customer_instance = getattr(user_instance, 'customer_profile', None) if user_instance else None
    if request.method == 'POST' and 'delete_user' in request.POST and user_instance:
        user_instance.delete()
        return redirect('user_manage')

    user_form = UserForm(request.POST or None, instance=user_instance)
    customer_form = CustomerProfileForm(request.POST or None, instance=customer_instance)
    if request.method == 'POST' and 'save_user' in request.POST:
        if user_form.is_valid() and customer_form.is_valid():
            user = user_form.save(commit=False)
            customer = customer_form.save(commit=False)
            if not user_instance:
                user.set_password(user_form.cleaned_data['password'])
            user.email = customer.email
            acc_type = request.POST.get('account_type')
            if acc_type == 'superuser' and request.user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
            elif acc_type == 'staff':
                user.is_superuser = False
                user.is_staff = True
            else:
                user.is_superuser = False
                user.is_staff = False
            
            user.save()
            
            customer.user = user
            customer.save()
            return redirect('user_manage')

    selected_account_type = 'customer'
    if user_instance:
        if user_instance.is_superuser:
            selected_account_type = 'superuser'
        elif user_instance.is_staff:
            selected_account_type = 'staff'

    return render(request, 'user_manage.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'user_form': user_form,
        'customer_form': customer_form,
        'selected_user': user_instance,
        'selected_account_type': selected_account_type,
        'search_query': search_query,
        'current_filter': account_type_filter,
        'current_sort': sort_by,
    })


@staff_member_required
def order_manage_view(request, pk=None):
    order_instance = get_object_or_404(Order, pk=pk) if pk else None
    q = request.GET.get('q', '')
    orders = Order.objects.select_related('customer__user').prefetch_related('items__laptop').all().order_by('-created_at')
    
    if q:
        orders = orders.filter(
            Q(tx_ref__icontains=q) |
            Q(customer__full_name__icontains=q) |
            Q(customer__user__username__icontains=q) |
            Q(customer__email__icontains=q) |
            Q(customer__user__email__icontains=q) |
            Q(customer__phone_number__icontains=q) |
            Q(items__laptop__name__icontains=q) |
            Q(items__laptop__brand__icontains=q)
        ).distinct()

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    if request.method == 'POST':
        if 'delete_order' in request.POST and order_instance:
            order_instance.delete()
            return redirect('order_manage')
        if 'save_order' in request.POST and order_instance:
            order_form = OrderForm(request.POST, instance=order_instance)
            if order_form.is_valid():
                order_form.save()
                return redirect('order_manage')
        else:
            order_form = OrderForm(instance=order_instance)
    else:
        order_form = OrderForm(instance=order_instance)

    return render(request, 'order_manage.html', {
        'orders': orders_page,
        'order_form': order_form,
        'selected_order': order_instance,
        'q': q,
    })