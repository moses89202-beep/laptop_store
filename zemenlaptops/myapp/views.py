from django.shortcuts import render
from .models import Laptop
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator


def home(request):
    laptops = Laptop.objects.all()
    return render(request, 'home.html', {'laptops': laptops})

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
    get_clean = lambda key: (request.GET.get(key, '').strip() or None) if (request.GET.get(key, '').strip() not in ['', 'None']) else None

    brand = get_clean('brand')
    ram = get_clean('ram')
    cpu = get_clean('cpu')
    gpu = get_clean('gpu')
    os_system = get_clean('os')
    storage = get_clean('storage')
    screen_size = get_clean('screen_size')
    max_price = get_clean('max_price')

    if brand: queryset = queryset.filter(brand__iexact=brand)
    if ram: queryset = queryset.filter(ram__icontains=ram)
    if cpu: queryset = queryset.filter(cpu__icontains=cpu)
    if gpu: queryset = queryset.filter(gpu__icontains=gpu)
    if os_system: queryset = queryset.filter(os__icontains=os_system)
    if storage: queryset = queryset.filter(storage__icontains=storage)
    if screen_size: queryset = queryset.filter(screen_size=screen_size)
    if max_price: queryset = queryset.filter(price__lte=max_price)

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
    distinct_gpus = Laptop.objects.values_list('gpu', flat=True).distinct().order_by('gpu')
    distinct_storage = Laptop.objects.values_list('storage', flat=True).distinct().order_by('storage')
    distinct_screens = Laptop.objects.values_list('screen_size', flat=True).distinct().order_by('screen_size')
    distinct_os = Laptop.objects.values_list('os', flat=True).distinct().order_by('os')

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
    }
    return render(request, 'catalog.html', context)


def cart_page(request):
    return render(request, 'cart.html')

def cart_items_api(request):
    id_string = request.GET.get('ids', '')
    if not id_string:
        return JsonResponse({'items': []})
        
    try:
        product_ids = [int(x.strip()) for x in id_string.split(',') if x.strip().isdigit()]
        laptops = Laptop.objects.filter(id__in=product_ids)
        items_data = []
        for laptop in laptops:
            items_data.append({
                'id': laptop.id,
                'name': laptop.name,
                'brand': laptop.brand,
                'price': float(laptop.price),
                'processor': getattr(laptop, 'processor', 'Core i7'),
                'ram': getattr(laptop, 'ram', '16GB RAM'),
                'storage': getattr(laptop, 'storage', '512GB SSD'),
                'image_url': laptop.image.url if laptop.image else ''
            })
            
        return JsonResponse({'items': items_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e), 'items': []}, status=400)