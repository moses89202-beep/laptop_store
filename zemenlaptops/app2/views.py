import json
import requests
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Laptop, Order, OrderItem, Customer

def generate_receipt_pdf(order):
    from io import BytesIO
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'StoreTitle', 
        parent=styles['Heading1'], 
        textColor=colors.HexColor('#1A365D'), 
        fontSize=24, 
        spaceAfter=6
    )
    invoice_title_style = ParagraphStyle(
        'InvoiceTitle', 
        parent=styles['Normal'], 
        alignment=2, # Right aligned
        fontSize=18, 
        textColor=colors.HexColor('#4A5568')
    )
    meta_style = ParagraphStyle(
        'MetaStyle', 
        parent=styles['Normal'], 
        fontSize=10, 
        textColor=colors.HexColor('#4A5568'), 
        leading=14
    )
    
    story = []
    
    header_data = [
        [
            Paragraph("<b>Zemen Laptops</b>", title_style), 
            Paragraph(f"<b>INVOICE</b><br/>Ref: {order.tx_ref[:8].upper()}", invoice_title_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    cust_name = order.customer.full_name or order.customer.user.username
    logistics_info = f"<b>Delivery Method:</b> {order.get_delivery_method_display()}<br/>"
    if order.delivery_method == 'delivery':
        logistics_info += f"<b>Delivery Status:</b> {order.get_delivery_status_display()}"
    else:
        logistics_info += f"<b>Pickup Status:</b> {order.get_delivery_status_display()}"

    meta_data = [
        [
            Paragraph(f"<b>Billed To:</b><br/>{cust_name}<br/>{order.customer.email or order.customer.user.email}", meta_style),
            Paragraph(f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}<br/>{logistics_info}", meta_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    table_data = [[
        Paragraph("<b>Item Description</b>", styles['Normal']), 
        Paragraph("<b>Qty</b>", styles['Normal']), 
        Paragraph("<b>Unit Price</b>", styles['Normal']), 
        Paragraph("<b>Total</b>", styles['Normal'])
    ]]
    
    for item in order.items.all():
        table_data.append([
            Paragraph(item.laptop.name, styles['Normal']),
            Paragraph(str(item.quantity), styles['Normal']),
            Paragraph(f"{item.price} ETB", styles['Normal']),
            Paragraph(f"{item.price * item.quantity} ETB", styles['Normal'])
        ])
    table_data.append([
        Paragraph("<b>Grand Total</b>", styles['Normal']), 
        "", "", 
        Paragraph(f"<b>{order.total_amount} ETB</b>", styles['Normal'])
    ])
    
    item_table = Table(table_data, colWidths=[260, 50, 100, 130])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F7FAFC')]),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E2E8F0')),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#1A365D')),
        ('TOPPADDING', (0,-1), (-1,-1), 10),
    ]))
    for i in range(4):
        item_table.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
        
    story.append(item_table)
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.HexColor('#A0AEC0'))
    story.append(Paragraph("Thank you for shopping with Zemen Laptops! Come back again.", footer_style))
    
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