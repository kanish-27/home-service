"""
Invoice views for handling invoice generation, display, and download
"""
import os
import pymongo
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.template.loader import render_to_string
from bson import ObjectId
from decimal import Decimal
from datetime import datetime
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from .models import Booking, Invoice


class InvoiceDetailView(LoginRequiredMixin, TemplateView):
    """View invoice details for a booking"""
    template_name = 'services/invoice_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('booking_id')

        # Always pass booking_id to context
        context['booking_id'] = booking_id

        try:
            # Try to get invoice from MongoDB first
            invoice_data = self.get_mongodb_invoice(booking_id)
            if invoice_data:
                context.update(invoice_data)
                return context

            # Fallback to Django ORM
            try:
                booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)

                # Check if booking is approved and paid
                if booking.status != 'confirmed' or not booking.is_paid:
                    messages.error(self.request, 'Invoice is only available for approved and paid bookings.')
                    context['booking'] = booking
                    return context

                # Get or create invoice
                invoice, created = Invoice.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'subtotal': booking.total_amount,
                        'tax_amount': booking.total_amount * Decimal('0.18'),
                        'total_amount': booking.total_amount * Decimal('1.18'),
                    }
                )

                if created:
                    # Generate QR code for service access
                    self.generate_qr_code(invoice)

                context['booking'] = booking
                context['invoice'] = invoice
                context['is_mongodb'] = False

                # Calculate amounts for template if no invoice exists
                if not invoice:
                    subtotal = booking.total_amount
                    tax_amount = subtotal * Decimal('0.18')
                    total_amount = subtotal + tax_amount

                    context['booking_subtotal'] = f"{subtotal:.2f}"
                    context['booking_tax_amount'] = f"{tax_amount:.2f}"
                    context['booking_total_amount'] = f"{total_amount:.2f}"

            except (Booking.DoesNotExist, ValueError):
                # If Django ORM booking not found, show error
                messages.error(self.request, 'Booking not found or you do not have permission to view this invoice.')

        except Exception as e:
            messages.error(self.request, f'Error loading invoice: {str(e)}')

        return context
    
    def get_mongodb_invoice(self, booking_id):
        """Get invoice data from MongoDB"""
        try:
            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Get booking from MongoDB
            booking_doc = db['services_booking'].find_one({'_id': ObjectId(booking_id)})
            if not booking_doc:
                print(f"No MongoDB booking found for ID: {booking_id}")
                return None

            # Check if user owns this booking
            if booking_doc.get('customer_id') != self.request.user.id:
                print(f"User {self.request.user.id} does not own booking {booking_id}")
                return None

            # For invoice display, we'll show it for confirmed bookings regardless of payment status
            if booking_doc.get('status') != 'confirmed':
                print(f"Booking {booking_id} is not confirmed (status: {booking_doc.get('status')})")
                return None

            # Get or create invoice from MongoDB
            invoice_doc = db['services_invoice'].find_one({'booking_id': ObjectId(booking_id)})
            if not invoice_doc:
                # Create a basic invoice document for display
                from datetime import datetime
                invoice_doc = {
                    'booking_id': ObjectId(booking_id),
                    'invoice_number': f'INV-{booking_id[:8].upper()}',
                    'generated_at': datetime.now(),
                    'subtotal': 0,
                    'tax_amount': 0,
                    'total_amount': 0
                }
                print(f"Created temporary invoice doc for booking {booking_id}")

            # Get service and provider info
            service_doc = db['services_service'].find_one({'_id': booking_doc.get('service_id')})
            provider_doc = db['auth_user'].find_one({'_id': booking_doc.get('provider_id')})

            # If service or provider not found in database, extract from notes
            service_name = "Unknown Service"
            provider_name = "Unknown Provider"

            if service_doc:
                service_name = service_doc.get('name', 'Unknown Service')
            elif booking_doc.get('notes'):
                # Extract service name from notes
                notes = booking_doc.get('notes', '')
                if 'Booking for' in notes:
                    parts = notes.split(' - ')
                    if len(parts) >= 1:
                        service_name = parts[0].replace('Booking for ', '').strip()

            if provider_doc:
                provider_name = f"{provider_doc.get('first_name', '')} {provider_doc.get('last_name', '')}".strip()
                if not provider_name:
                    provider_name = provider_doc.get('email', 'Unknown Provider')
            elif booking_doc.get('notes'):
                # Extract provider name from notes
                notes = booking_doc.get('notes', '')
                if 'Provider:' in notes:
                    parts = notes.split(' - ')
                    if len(parts) >= 2:
                        provider_name = parts[1].replace('Provider: ', '').strip()

            # Create service and provider data objects for template compatibility
            if not service_doc:
                service_doc = {'name': service_name}

            if not provider_doc:
                provider_doc = {
                    'first_name': provider_name.split()[0] if provider_name.split() else provider_name,
                    'last_name': ' '.join(provider_name.split()[1:]) if len(provider_name.split()) > 1 else '',
                    'email': 'Not available'
                }

            # Calculate amounts
            subtotal = float(booking_doc.get('total_amount', 0))
            tax_amount = subtotal * 0.18
            total_amount = subtotal + tax_amount

            # Update invoice_doc with calculated amounts
            invoice_doc['subtotal'] = subtotal
            invoice_doc['tax_amount'] = tax_amount
            invoice_doc['total_amount'] = total_amount

            print(f"MongoDB invoice data prepared for booking {booking_id}")
            print(f"  Service: {service_name}")
            print(f"  Provider: {provider_name}")
            print(f"  Subtotal: ₹{subtotal}")
            print(f"  Tax: ₹{tax_amount}")
            print(f"  Total: ₹{total_amount}")

            return {
                'booking_data': booking_doc,
                'invoice_data': invoice_doc,
                'service_data': service_doc,
                'provider_data': provider_doc,
                'booking_id': str(booking_doc['_id']),
                'is_mongodb': True
            }

        except Exception as e:
            print(f"Error getting MongoDB invoice: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
    def generate_qr_code(self, invoice):
        """Generate QR code for invoice"""
        try:
            # Create QR code data
            qr_data = f"HomeService Invoice: {invoice.invoice_number}\nBooking ID: {invoice.booking.id}\nAmount: ₹{invoice.total_amount}\nCustomer: {invoice.booking.customer.email}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Save QR code to invoice
            qr_filename = f"qr_code_{invoice.invoice_number}.png"
            invoice.qr_code.save(qr_filename, ContentFile(qr_buffer.read()), save=True)
            
        except Exception as e:
            print(f"Error generating QR code: {e}")


class InvoiceDownloadView(LoginRequiredMixin, View):
    """Download invoice PDF"""
    
    def get(self, request, booking_id):
        try:
            # Try MongoDB first
            pdf_content = self.generate_mongodb_invoice_pdf(booking_id)
            if pdf_content:
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="invoice_{booking_id}.pdf"'
                return response
            
            # Fallback to Django ORM
            booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
            
            # Check if booking is approved and paid
            if booking.status != 'confirmed' or not booking.is_paid:
                messages.error(request, 'Invoice download is only available for approved and paid bookings.')
                return redirect('services:booking_detail', pk=booking_id)
            
            # Get invoice
            invoice = get_object_or_404(Invoice, booking=booking)
            
            # Generate PDF
            pdf_content = self.generate_pdf(invoice)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            return response
            
        except Exception as e:
            messages.error(request, f'Error downloading invoice: {str(e)}')
            return redirect('services:booking_list')
    
    def generate_mongodb_invoice_pdf(self, booking_id):
        """Generate PDF for MongoDB invoice"""
        try:
            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Get booking and invoice
            booking_doc = db['services_booking'].find_one({'_id': ObjectId(booking_id)})
            if not booking_doc or booking_doc.get('customer_id') != self.request.user.id:
                return None

            invoice_doc = db['services_invoice'].find_one({'booking_id': ObjectId(booking_id)})
            if not invoice_doc:
                # Create temporary invoice for PDF
                from datetime import datetime
                invoice_doc = {
                    'booking_id': ObjectId(booking_id),
                    'invoice_number': f'INV-{booking_id[:8].upper()}',
                    'generated_at': datetime.now(),
                    'subtotal': float(booking_doc.get('total_amount', 0)),
                    'tax_amount': float(booking_doc.get('total_amount', 0)) * 0.18,
                    'total_amount': float(booking_doc.get('total_amount', 0)) * 1.18
                }

            # Get additional data with fallback to notes
            service_doc = db['services_service'].find_one({'_id': booking_doc.get('service_id')})
            provider_doc = db['auth_user'].find_one({'_id': booking_doc.get('provider_id')})
            customer_doc = db['auth_user'].find_one({'_id': booking_doc.get('customer_id')})

            # If customer not found in MongoDB, use the current user
            if not customer_doc:
                customer_doc = {
                    'first_name': self.request.user.first_name,
                    'last_name': self.request.user.last_name,
                    'email': self.request.user.email
                }

            # Extract service and provider names from notes if not found in database
            service_name = "Unknown Service"
            provider_name = "Unknown Provider"

            if service_doc:
                service_name = service_doc.get('name', 'Unknown Service')
            elif booking_doc.get('notes'):
                notes = booking_doc.get('notes', '')
                if 'Booking for' in notes:
                    parts = notes.split(' - ')
                    if len(parts) >= 1:
                        service_name = parts[0].replace('Booking for ', '').strip()

            if provider_doc:
                provider_name = f"{provider_doc.get('first_name', '')} {provider_doc.get('last_name', '')}".strip()
                if not provider_name:
                    provider_name = provider_doc.get('email', 'Unknown Provider')
            elif booking_doc.get('notes'):
                notes = booking_doc.get('notes', '')
                if 'Provider:' in notes:
                    parts = notes.split(' - ')
                    if len(parts) >= 2:
                        provider_name = parts[1].replace('Provider: ', '').strip()

            # Create service and provider objects for PDF
            if not service_doc:
                service_doc = {'name': service_name}

            if not provider_doc:
                provider_doc = {
                    'first_name': provider_name.split()[0] if provider_name.split() else provider_name,
                    'last_name': ' '.join(provider_name.split()[1:]) if len(provider_name.split()) > 1 else '',
                    'email': 'Not available'
                }

            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []

            # Add content to PDF
            self.add_pdf_content(story, {
                'booking': booking_doc,
                'invoice': invoice_doc,
                'service': service_doc,
                'provider': provider_doc,
                'customer': customer_doc,
                'is_mongodb': True
            })

            doc.build(story)
            buffer.seek(0)
            return buffer.read()

        except Exception as e:
            print(f"Error generating MongoDB PDF: {e}")
            return None
    
    def generate_pdf(self, invoice):
        """Generate PDF for Django ORM invoice"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Add content to PDF
        self.add_pdf_content(story, {
            'booking': invoice.booking,
            'invoice': invoice,
            'service': invoice.booking.service,
            'provider': invoice.booking.provider,
            'customer': invoice.booking.customer,
            'is_mongodb': False
        })
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    def add_pdf_content(self, story, data):
        """Add content to PDF"""
        styles = getSampleStyleSheet()
        
        # Header
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#20c997'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("HomeService Invoice", header_style))
        story.append(Spacer(1, 20))
        
        # Invoice details
        if data['is_mongodb']:
            invoice_number = data['invoice']['invoice_number']
            generated_date = data['invoice']['generated_at'].strftime('%B %d, %Y')
            customer_name = f"{data['customer'].get('first_name', '')} {data['customer'].get('last_name', '')}".strip()
            customer_email = data['customer']['email']
            service_name = data['service']['name']
            provider_name = f"{data['provider'].get('first_name', '')} {data['provider'].get('last_name', '')}".strip()

            # Ensure provider name is not empty
            if not provider_name or provider_name.strip() == '':
                provider_name = data['provider'].get('email', 'Service Provider')

            subtotal = data['invoice']['subtotal']
            tax_amount = data['invoice']['tax_amount']
            total_amount = data['invoice']['total_amount']
        else:
            invoice_number = data['invoice'].invoice_number
            generated_date = data['invoice'].generated_at.strftime('%B %d, %Y')
            customer_name = data['customer'].get_full_name()
            customer_email = data['customer'].email
            service_name = data['service'].name
            provider_name = data['provider'].get_full_name()
            subtotal = float(data['invoice'].subtotal)
            tax_amount = float(data['invoice'].tax_amount)
            total_amount = float(data['invoice'].total_amount)
        
        # Invoice info table
        invoice_data = [
            ['Invoice Number:', invoice_number],
            ['Date:', generated_date],
            ['Customer:', f"{customer_name} ({customer_email})"],
            ['Service:', service_name],
            ['Provider:', provider_name],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Amount breakdown - Use Rs. for better PDF compatibility
        amount_data = [
            ['Description', 'Amount'],
            ['Service Charge', f'Rs. {subtotal:.2f}'],
            ['GST (18%)', f'Rs. {tax_amount:.2f}'],
            ['Total Amount', f'Rs. {total_amount:.2f}'],
        ]
        
        amount_table = Table(amount_data, colWidths=[4*inch, 2*inch])
        amount_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#20c997')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(amount_table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = "Thank you for choosing HomeService! Present this invoice and QR code to the service provider."
        story.append(Paragraph(footer_text, styles['Normal']))


@login_required
def check_invoice_status(request, booking_id):
    """Check if invoice is available for a booking"""
    try:
        # Check MongoDB first
        client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        db = client[settings.DATABASES['default']['NAME']]
        
        booking_doc = db['services_booking'].find_one({'_id': ObjectId(booking_id)})
        if booking_doc and booking_doc.get('customer_id') == request.user.id:
            invoice_doc = db['services_invoice'].find_one({'booking_id': ObjectId(booking_id)})
            if invoice_doc and booking_doc.get('status') == 'confirmed' and booking_doc.get('is_paid'):
                return JsonResponse({
                    'has_invoice': True,
                    'invoice_number': invoice_doc['invoice_number'],
                    'download_url': f'/services/invoice/{booking_id}/download/',
                    'view_url': f'/services/invoice/{booking_id}/'
                })
        
        # Check Django ORM
        try:
            booking = Booking.objects.get(id=booking_id, customer=request.user)
            if booking.status == 'confirmed' and booking.is_paid:
                try:
                    invoice = Invoice.objects.get(booking=booking)
                    return JsonResponse({
                        'has_invoice': True,
                        'invoice_number': invoice.invoice_number,
                        'download_url': f'/services/invoice/{booking_id}/download/',
                        'view_url': f'/services/invoice/{booking_id}/'
                    })
                except Invoice.DoesNotExist:
                    pass
        except Booking.DoesNotExist:
            pass
        
        return JsonResponse({'has_invoice': False})
        
    except Exception as e:
        return JsonResponse({'has_invoice': False, 'error': str(e)})
