import json
import requests
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Laptop, Order, OrderItem, Customer


def generate_receipt_pdf(order):
    from io import BytesIO
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    SLATE_900 = colors.HexColor("#0f172a")
    SLATE_600 = colors.HexColor("#475569")
    SLATE_400 = colors.HexColor("#94a3b8")
    BG_LIGHT = colors.HexColor("#f8fafc")
    CARD_BG = colors.HexColor("#f1f5f9")
    AMBER = colors.HexColor("#f59e0b")
    WHITE = colors.white


    logo_style = ParagraphStyle(
        'LogoStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=SLATE_900,
        spaceAfter=4,
    )

    invoice_style = ParagraphStyle(
        'InvoiceStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=SLATE_600,
        alignment=2  # Right
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SLATE_400,
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=SLATE_600,
        leading=14
    )

    total_style = ParagraphStyle(
        'TotalStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=SLATE_900,
    )

    story = []

    logo_block = Paragraph(
        f"""
        <font color="#f59e0b"><b>■</b></font>
        <b>ZEMEN LAPTOPS</b><br/>
        <font size="9" color="#94a3b8">
        Premium laptop store in Addis Ababa
        </font>
        """,
        logo_style
    )

    invoice_block = Paragraph(
        f"<b>INVOICE</b><br/><font size='9'>Ref: {order.tx_ref[:8].upper()}</font>",
        invoice_style
    )

    header = Table([[logo_block, invoice_block]], colWidths=[3.5 * inch, 2.5 * inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(header)
    story.append(Spacer(1, 20))

    cust_name = order.customer.full_name or order.customer.user.username

    logistics = f"""
    <b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}<br/>
    <b>Delivery:</b> {order.get_delivery_method_display()}<br/>
    <b>Status:</b> {order.get_delivery_status_display()}
    """

    customer_info = [
        [
            Paragraph(
                f"<b>BILLED TO</b><br/>{cust_name}<br/>{order.customer.email or order.customer.user.email}",
                normal_style
            ),
            Paragraph(logistics, normal_style)
        ]
    ]

    customer_table = Table(customer_info, colWidths=[3 * inch, 3 * inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(customer_table)
    story.append(Spacer(1, 25))

    table_data = [[
        Paragraph("<b>Item</b>", normal_style),
        Paragraph("<b>Qty</b>", normal_style),
        Paragraph("<b>Price</b>", normal_style),
        Paragraph("<b>Total</b>", normal_style),
    ]]

    for item in order.items.all():
        table_data.append([
            Paragraph(item.laptop.name, normal_style),
            str(item.quantity),
            f"{item.price} ETB",
            f"{item.price * item.quantity} ETB",
        ])

    table_data.append([
        "",
        "",
        Paragraph("<b>Grand Total</b>", total_style),
        Paragraph(f"<b>{order.total_amount} ETB</b>", total_style)
    ])

    item_table = Table(table_data, colWidths=[3 * inch, 0.7 * inch, 1.1 * inch, 1.2 * inch])

    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SLATE_900),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, AMBER),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(item_table)
    story.append(Spacer(1, 40))

    footer = Paragraph(
        """
        <font color="#94a3b8">
        Thank you for shopping with <b>Zemen Laptops</b>.<br/>
        Megenagna, Tamegas Building | Addis Ababa<br/>
        zemenlaptops@gmail.com | +251 91 123 4567
        </font>
        """,
        ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1
        )
    )

    story.append(footer)

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


@login_required
def initialize_payment(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        cart_items = data.get('cart_items', [])
        delivery_method = data.get('delivery_method', 'delivery')
        if delivery_method not in ['delivery', 'pickup']:
            return JsonResponse({"error": "Invalid delivery method specified."}, status=400)
        if not cart_items:
            return JsonResponse({"error": "Your cart is empty."}, status=400)

        quantity_map = {}
        for item in cart_items:
            laptop_id = item.get('id')
            quantity = item.get('quantity', 1)

            try:
                laptop_id = int(laptop_id)
                quantity = int(quantity)
            except (TypeError, ValueError):
                return JsonResponse({"error": "Invalid cart item format."}, status=400)

            if quantity <= 0:
                return JsonResponse({"error": "Invalid product quantity."}, status=400)

            quantity_map[laptop_id] = quantity_map.get(laptop_id, 0) + quantity

        if not quantity_map:
            return JsonResponse({"error": "Your cart is empty."}, status=400)

        customer = get_object_or_404(Customer, user=request.user)

        with transaction.atomic():
            laptops_queryset = Laptop.objects.select_for_update().filter(id__in=quantity_map.keys())
            laptops = {laptop.id: laptop for laptop in laptops_queryset}

            if len(laptops) != len(quantity_map):
                return JsonResponse({"error": "Some products in your cart no longer exist."}, status=404)

            for laptop_id, requested_quantity in quantity_map.items():
                laptop = laptops[laptop_id]
                if laptop.quantity <= 0:
                    return JsonResponse({"error": f"{laptop.name} is currently out of stock."}, status=409)
                if requested_quantity > laptop.quantity:
                    return JsonResponse({"error": f"You requested {requested_quantity} of {laptop.name}, but only {laptop.quantity} is available."}, status=409)

            total_price = Decimal("0.00")
            for laptop_id, requested_quantity in quantity_map.items():
                laptop = laptops[laptop_id]
                total_price += laptop.price * requested_quantity

            initial_delivery_status = 'pending' if delivery_method == 'delivery' else 'ready_for_pickup'

            order = Order.objects.create(
                customer=customer,
                total_amount=total_price,
                payment_status='pending',
                delivery_method=delivery_method,
                delivery_status=initial_delivery_status
            )

            for laptop_id, requested_quantity in quantity_map.items():
                laptop = laptops[laptop_id]
                OrderItem.objects.create(
                    order=order,
                    laptop=laptop,
                    quantity=requested_quantity,
                    price=laptop.price
                )

        name_parts = (customer.full_name or "Customer Name").split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "User"

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "amount": str(order.total_amount),
            "currency": "ETB",
            "email": customer.email or request.user.email or "customer@example.com",
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": str(order.tx_ref),
            "callback_url": f"https://yourdomain.com/payment/verify/{order.tx_ref}/",
            "return_url": f"http://127.0.0.1:8000/payment/success/{order.tx_ref}/",
            "customization": {
                "title": "Zemen Laptops",
                "description": f"Payment for Order {order.id}"
            }
        }

        response = requests.post(settings.CHAPA_API_URL, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        if response_data.get("status") == "success":
            return JsonResponse({"checkout_url": response_data["data"]["checkout_url"]})

        order.delete()
        return JsonResponse({"error": response_data.get("message", "Chapa initialization failed.")}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request format."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


@login_required
def verify_payment(request, tx_ref):
    order = get_object_or_404(Order, tx_ref=tx_ref)
    
    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
    verify_url = f"{settings.CHAPA_VERIFY_URL}{tx_ref}"
    
    response = requests.get(verify_url, headers=headers)
    response_data = response.json()
    
    if response_data.get("status") == "success" and response_data["data"]["status"] == "success":
        if order.payment_status != 'completed':
            order.payment_status = 'completed'
            
            if order.delivery_method == 'pickup':
                order.delivery_status = 'ready_for_pickup' 
            
            order.save()
            
            for item in order.items.all():
                if item.laptop.quantity >= item.quantity:
                    item.laptop.quantity -= item.quantity
                    item.laptop.save()

            if not order.receipt:
                pdf_binary = generate_receipt_pdf(order)
                filename = f"receipt_{order.tx_ref[:8]}.pdf"
                order.receipt.save(filename, ContentFile(pdf_binary))
                    
        return render(request, 'payment_success.html', {'order': order})
    else:
        order.payment_status = 'failed'
        order.save()
        return render(request, 'payment_failed.html', {'order': order})