from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import inlineformset_factory
from myapp.models import Laptop, Customer, Review
from app2.models import Order, OrderItem
from .forms import LaptopForm, UserForm, CustomerProfileForm, OrderForm

# ==========================================
# DASHBOARD HOME VIEW (Staff Required)
# ==========================================
@staff_member_required
def dashboard_home_view(request):
    context = {
        'total_laptops': Laptop.objects.count(),
        'total_users': User.objects.count(),
        'total_orders': Order.objects.count(),
        'total_reviews': Review.objects.count(),
        'recent_orders': Order.objects.select_related('customer').order_by('-created_at')[:5]
    }
    return render(request, 'base_dashboard.html', context)


# ==========================================
# LAPTOP CRUD + REVIEWS (Staff Required)
# ==========================================
@staff_member_required
def laptop_manage_view(request, pk=None):
    laptops = Laptop.objects.all()
    instance = get_object_or_404(Laptop, pk=pk) if pk else None
    
    if request.method == 'POST' and 'delete_laptop' in request.POST and instance:
        instance.delete()
        return redirect('laptop_manage')

    form = LaptopForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and 'save_laptop' in request.POST and form.is_valid():
        form.save()
        return redirect('laptop_manage')

    if request.method == 'POST' and 'delete_review' in request.POST:
        review_id = request.POST.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        review.delete()
        return redirect('laptop_manage')

    all_reviews = Review.objects.select_related('laptop', 'customer').all()

    return render(request, 'laptop_manage.html', {
        'laptops': laptops,
        'form': form,
        'selected_laptop': instance,
        'reviews': all_reviews
    })


# ==========================================
# USER/CUSTOMER CRUD (Staff Required)
# ==========================================
@staff_member_required
def user_manage_view(request, pk=None):
    users = User.objects.select_related('customer_profile').all()
    user_instance = get_object_or_404(User, pk=pk) if pk else None
    customer_instance = getattr(user_instance, 'customer_profile', None) if user_instance else None

    if request.method == 'POST' and 'delete_user' in request.POST and user_instance:
        user_instance.delete()
        return redirect('user_manage')

    user_form = UserForm(request.POST or None, instance=user_instance)
    customer_form = CustomerProfileForm(request.POST or None, instance=customer_instance)

    if request.method == 'POST' and 'save_user' in request.POST:
        if user_form.is_valid() and customer_form.is_valid():
            user = user_form.save(commit=False)
            if not user_instance:
                user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            customer = customer_form.save(commit=False)
            customer.user = user
            customer.save()
            return redirect('user_manage')

    return render(request, 'user_manage.html', {
        'users': users,
        'user_form': user_form,
        'customer_form': customer_form,
        'selected_user': user_instance
    })


# ==========================================
# ORDER CRUD (Staff Required)
# ==========================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from app2.models import Order
from .forms import OrderForm

@staff_member_required
def order_manage_view(request, pk=None):
    orders = Order.objects.select_related('customer').all()
    order_instance = get_object_or_404(Order, pk=pk) if pk else None

    # Handle deletion
    if request.method == 'POST' and 'delete_order' in request.POST and order_instance:
        order_instance.delete()
        return redirect('order_manage')

    # Status update logic
    order_form = OrderForm(request.POST or None, instance=order_instance) if order_instance else None

    if request.method == 'POST' and 'save_order' in request.POST and order_instance:
        if order_form.is_valid():
            order_form.save()
            return redirect('order_manage')

    return render(request, 'order_manage.html', {
        'orders': orders,
        'order_form': order_form,
        'selected_order': order_instance
    })