from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article
from rest_framework import status
from .serializers import PartnershipSerializer, CustomershipSerializer, ProductSerializer, RequestFormSerializer, ProjectReferenceSerializer, NewsSerializer, ArticleSerializer

class AdminPartnershipViewSet(viewsets.ModelViewSet):
    queryset = Partnership.objects.all()
    serializer_class = PartnershipSerializer
    permission_classes = [IsAdminUser]

class AdminCustomershipViewSet(viewsets.ModelViewSet):
    queryset = Customership.objects.all()
    serializer_class = CustomershipSerializer
    permission_classes = [IsAdminUser]

class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('position')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class AdminRequestFormViewSet(viewsets.ModelViewSet):
    queryset = RequestForm.objects.all()
    serializer_class = RequestFormSerializer
    permission_classes = [IsAdminUser]
 
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update the status of a request form."""
        request_form = self.get_object()
        status = request.data.get('status')
        if status not in ['pending', 'complete']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        request_form.status = status
        request_form.save()
        
        serializer = self.get_serializer(request_form)
        return Response(serializer.data)

class AdminProjectReferenceViewSet(viewsets.ModelViewSet):
    queryset = ProjectReference.objects.all().order_by('position')
    serializer_class = ProjectReferenceSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status for a project reference with max limitof 4."""
        project = self.get_object()
        if project.is_favorite: # If currently favorite, remove from favorites
            project.is_favorite = False
            project.save()
            return Response({
                'message': 'Removed from favorites',
                'is_favorite': False,
                'favorites_count': ProjectReference.objects.filter(is_favorite=True).count()
            })
        else: # Check if we already have 4 favorites
            current_favorite_count = ProjectReference.objects.filter(is_favorite=True).count()
            if current_favorite_count >= 4:
                return Response({
                    'error': 'Maximum of 4 favorite projects allowed.',
                    'favorite_count': current_favorite_count
                }, status=status.HTTP_400_BAD_REQUEST)
            # Add to favorite
            project.is_favorite = True
            project.save()
            return Response({
                'message': 'Added to favorites',
                'is_favorite': True,
                'favorite_count': ProjectReference.objects.filter(is_favorite=True).count()
            })
        
        @action(detail=False, methods=['get'])
        def favorites(self, request):
            """Get all favorite project references"""
            favorites = ProjectReference.objects.filter(is_favorite=True)
            serializer = self.get_serializer(favorites, many=True)
            return Response(serializer.data)

class AdminNewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminUser]

class AdminArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminUser]