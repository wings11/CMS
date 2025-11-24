from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
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
import logging
import base64

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
    queryset = News.objects.all().order_by('-created_at')
    serializer_class = NewsSerializer
    permission_classes = [IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        """Handle news creation - serializer handles all parsing"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logging.error(f"News serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Handle news update - serializer handles all parsing"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)


class AdminArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        """Handle article creation with PDF file upload"""
        data = request.data.copy()
        
        # Handle PDF file if provided
        pdf_file = request.FILES.get('pdf_file')
        if pdf_file:
            data['pdf_file'] = pdf_file
        
        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Handle article update with PDF file upload"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        
        # Handle PDF file if provided
        pdf_file = request.FILES.get('pdf_file')
        if pdf_file:
            data['pdf_file'] = pdf_file
        
        serializer = self.get_serializer(instance, data=data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload_article(self, request):
        """Upload HTML file and images, process them, and create an article."""
        try:
            # Get form data
            html_file = request.FILES.get('html_file')
            images = request.FILES.getlist('images')
            pdf_file = request.FILES.get('pdf_file')  # Add PDF file support
            article_title = request.data.get('article_title')
            keyword = request.data.get('keyword')
            category = request.data.get('category')

            print(f"Received data: html_file={html_file}, images={len(images)}, pdf_file={pdf_file}, title={article_title}")

            if not article_title:
                return Response({'error': 'Article title is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize content variables
            html_content = ""
            if html_file:
                # Read HTML content
                html_content = html_file.read().decode('utf-8')
                print(f"HTML content length: {len(html_content)}")
            
            # Process images and update HTML
            image_data_list = []
            if images:
                # Create a mapping of original filenames to data URLs for HTML replacement
                image_map = {}
                
                for image in images:
                    # Read image content and encode as base64
                    image_content = image.read()
                    encoded_image = base64.b64encode(image_content).decode('utf-8')
                    
                    # Create data URL
                    content_type = image.content_type or 'image/jpeg'
                    data_url = f"data:{content_type};base64,{encoded_image}"
                    
                    # Store image data in database format
                    image_data = {
                        'name': image.name,
                        'data': encoded_image,
                        'content_type': content_type,
                        'data_url': data_url
                    }
                    image_data_list.append(image_data)
                    
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
                        image_map[variation] = data_url

                # Replace image src attributes in HTML
                def replace_image_src(match):
                    src = match.group(1)  # This is now the src value without quotes
                    
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
                            # Replace the src value in the match
                            return match.group(0).replace(src, image_map[name])
                    
                    return match.group(0)  # No replacement found
                
                # Replace all img src attributes if HTML content exists
                if html_content:
                    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>'
                    html_content = re.sub(img_pattern, replace_image_src, html_content, flags=re.IGNORECASE)
            
            # Create the article
            article = Article.objects.create(
                article_title=article_title,
                keyword=keyword.split(',') if keyword else [],
                category=category,
                content=[],  # Required field, empty for HTML articles
                content_html=html_content,  # Store HTML content
                article_image=image_data_list  # Store list of image data dicts
            )
            
            # Handle PDF file upload separately
            if pdf_file:
                article.pdf_file = pdf_file
                article.save()

            # Get serializer with request context for proper URL generation
            serializer = self.get_serializer(article, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminLogViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        """
        Admin-only API endpoint to fetch chatbot security logs and detect alerts.
        File-based for simplicity; enhanced with pagination and error handling.
        """
        try:
            log_file_path = os.path.join(settings.BASE_DIR, 'security_logs.txt')
            
            if not os.path.exists(log_file_path):
                return Response({
                    'error': 'Log file not found',
                    'logs': [],
                    'total_lines': 0,
                    'alerts': []
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Read the log file
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Pagination: Get limit from query param (default 100)
            limit = request.GET.get('limit', 100)
            try:
                limit = int(limit)
            except ValueError:
                limit = 100
            
            # Get recent lines (last N, reversed for newest first)
            recent_lines = lines[-limit:] if lines else []
            recent_lines.reverse()
            
            # Safely process logs and alerts (ensure line is a string)
            try:
                logs = [line.strip() for line in recent_lines if isinstance(line, str)]
                alerts = [line.strip() for line in recent_lines if isinstance(line, str) and any(keyword in line.upper() for keyword in ['ALERT', 'ERROR', 'SECURITY'])]
            except Exception as e:
                logging.error(f"Error processing log lines: {e}")
                logs = []
                alerts = []
            
            return Response({
                'logs': logs,
                'total_lines': len(lines),
                'showing_lines': len(logs),
                'alerts': alerts,  # For dashboard display
                'file_path': log_file_path
            })
            
        except Exception as e:
            logging.error(f"Error reading chatbot security logs: {e}")
            return Response({
                'error': f'Failed to read log file: {str(e)}',
                'logs': [],
                'total_lines': 0,
                'alerts': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Temporary API endpoint to create superuser (REMOVE AFTER TESTING)
from rest_framework.decorators import api_view
from django.contrib.auth.models import User

@api_view(['POST'])
def create_superuser_api(request):
    """
    Temporary endpoint to create a superuser
    POST /api/create-superuser/
    Body: {"username": "admin", "email": "admin@example.com", "password": "password"}
    """
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([username, email, password]):
            return Response({
                'error': 'Missing required fields: username, email, password'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({
                'message': f'User {username} already exists'
            }, status=status.HTTP_200_OK)

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        return Response({
            'message': f'Superuser {username} created successfully'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)