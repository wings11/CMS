from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article
from .serializers import PartnershipSerializer, CustomershipSerializer, ProductSerializer, RequestFormSerializer, ProjectReferenceSerializer, NewsSerializer, ArticleSerializer

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