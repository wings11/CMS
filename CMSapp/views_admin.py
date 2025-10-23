from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article
from rest_framework import status
from .serializers import PartnershipSerializer, CustomershipSerializer, ProductSerializer, RequestFormSerializer, ProjectReferenceSerializer, NewsSerializer, ArticleSerializer
import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import re

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

    @action(detail=False, methods=['post'])
    def upload_article(self, request):
        """Upload HTML file and images, process them, and create an article."""
        try:
            # Get form data
            html_file = request.FILES.get('html_file')
            images = request.FILES.getlist('images')
            article_title = request.data.get('article_title')
            keyword = request.data.get('keyword')
            category = request.data.get('category')

            if not html_file:
                return Response({'error': 'HTML file is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not article_title:
                return Response({'error': 'Article title is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Read HTML content
            html_content = html_file.read().decode('utf-8')
            
            # Process images and update HTML
            image_urls = []
            if images:
                # Create a mapping of original filenames to new URLs
                image_map = {}
                
                for image in images:
                    # Generate unique filename
                    file_extension = os.path.splitext(image.name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    
                    # Save image to media directory
                    file_path = os.path.join('articles', 'images', unique_filename)
                    saved_path = default_storage.save(file_path, ContentFile(image.read()))
                    
                    # Get the URL for the saved image
                    image_url = self.request.build_absolute_uri(default_storage.url(saved_path))
                    
                    # Store mapping for HTML replacement
                    # Try multiple variations of the original filename
                    original_name = image.name
                    variations = [
                        original_name,  # original
                        original_name.lower(),  # lowercase
                        os.path.splitext(original_name)[0],  # without extension
                        os.path.splitext(original_name)[0].lower(),  # lowercase without extension
                        # Try different extensions
                        os.path.splitext(original_name)[0] + '.png',
                        os.path.splitext(original_name)[0] + '.jpg',
                        os.path.splitext(original_name)[0] + '.jpeg',
                        os.path.splitext(original_name)[0] + '.gif',
                    ]
                    
                    for variation in variations:
                        image_map[variation] = image_url
                    
                    image_urls.append(image_url)

                # Replace image src attributes in HTML
                def replace_image_src(match):
                    src = match.group(1)
                    
                    # Skip if already a data URL (base64) or external URL
                    if src.startswith('data:') or src.startswith('http://') or src.startswith('https://'):
                        return match.group(0)
                    
                    # Try different ways to match the filename
                    possible_names = [
                        src,  # full path
                        os.path.basename(src),  # just filename
                        os.path.basename(src).lower(),  # lowercase filename
                        os.path.splitext(os.path.basename(src))[0],  # without extension
                        os.path.splitext(os.path.basename(src))[0].lower(),  # lowercase without extension
                        # Try variations with different extensions
                        os.path.splitext(os.path.basename(src))[0] + '.png',
                        os.path.splitext(os.path.basename(src))[0] + '.jpg',
                        os.path.splitext(os.path.basename(src))[0] + '.jpeg',
                        os.path.splitext(os.path.basename(src))[0] + '.gif',
                    ]
                    
                    for name in possible_names:
                        if name in image_map:
                            return match.group(0).replace(src, image_map[name])
                    
                    return match.group(0)  # No replacement found
                
            # Replace all img src attributes
            img_pattern = r'<img[^>]+src=([^ >]+)[^>]*>'
            html_content = re.sub(img_pattern, replace_image_src, html_content, flags=re.IGNORECASE)            # Create the article
            article = Article.objects.create(
                article_title=article_title,
                keyword=keyword.split(',') if keyword else [],
                category=category,
                content_html=html_content,  # Store HTML content
                article_image=image_urls  # Store list of image URLs
            )

            serializer = self.get_serializer(article)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)