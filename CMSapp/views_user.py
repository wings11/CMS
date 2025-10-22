from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article
from .serializers import PartnershipSerializer, CustomershipSerializer, ProductSerializer, RequestFormSerializer, ProjectReferenceSerializer, NewsSerializer, ArticleSerializer
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import escape
import logging

logger = logging.getLogger(__name__)

class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

class PartnershipViewSet(ReadOnlyViewSet):
    queryset = Partnership.objects.all()
    serializer_class = PartnershipSerializer
    
class CustomershipViewSet(ReadOnlyViewSet):
    queryset = Customership.objects.all()
    serializer_class = CustomershipSerializer

class ProductViewSet(ReadOnlyViewSet):
    queryset = Product.objects.all().order_by('position')
    serializer_class = ProductSerializer

class RequestFormViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = RequestForm.objects.all().order_by('-request_time')  
    serializer_class = RequestFormSerializer
    permission_classes = [AllowAny]
    def perform_create(self, serializer):
        instance = serializer.save()
        # Send auto-reply email
        html_body = f"""
          <p>Hi <strong>{escape(instance.full_name)}</strong>,</p>
          <p>Thank you for submitting your request to Civil Master Solution (CMS). We’ve received your inquiry for: {escape(instance.product_name)}.</p>
          <p>Our team will review it and get back to you within 2-3 business days. If you have questions, contact us at cms@civilmastersolution.com.</p>
          <p>Best regards,<br/>Civil Master Solution Team<br/>www.civilmastersolution.com</p>
        """
        email = EmailMessage(
            subject="Thank You for Your Request - Civil Master Solution",
            body=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email_address],
            headers={"Reply-To": "cms@civilmastersolution.com"},
        )
        email.content_subtype = "html"
        
        try:
            email.send()
            instance.auto_reply_sent = True
            instance.save(update_fields=["auto_reply_sent"])
        except Exception as e:
            logger.error(f"Email failed for {instance.email_address}: {e}")
            
class ProjectReferenceViewSet(ReadOnlyViewSet):
    queryset = ProjectReference.objects.all().order_by('position')
    serializer_class = ProjectReferenceSerializer
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get all favorite project references from home page display."""
        favorites = ProjectReference.objects.filter(is_favorite=True).order_by('position')
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

class NewsViewSet(ReadOnlyViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

class ArticleViewSet(ReadOnlyViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer