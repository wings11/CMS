from rest_framework import serializers
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article

class PartnershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partnership
        fields = '__all__'

class CustomershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customership
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        
class RequestFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestForm
        fields = '__all__'

class ProjectReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectReference
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    keyword = serializers.JSONField(required=False, allow_null=True)
    news_image = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = News
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def validate_keyword(self, value):
        """Handle keyword as either list or JSON string from FormData"""
        import json
        
        if value is None or value == '':
            return []
        
        if isinstance(value, str):
            try:
                # Try to parse as JSON string
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    # Filter out empty strings from parsed list
                    return [k.strip() for k in parsed if k and str(k).strip()]
                return []
            except (json.JSONDecodeError, ValueError, TypeError):
                # If not JSON, treat as comma-separated string
                return [k.strip() for k in value.split(',') if k.strip()]
        
        if isinstance(value, list):
            # Filter out empty strings from list
            return [k.strip() for k in value if k and str(k).strip()]
        
        return []
    
    def validate_news_image(self, value):
        """Handle news_image as either list or JSON string from FormData"""
        import json
        
        if value is None or value == '':
            return []
        
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        if isinstance(value, list):
            return value
        
        return []
    
    def validate_content(self, value):
        """Ensure content is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("Content field cannot be empty.")
        return value
    
    def validate_news_title(self, value):
        """Ensure news_title is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("News title cannot be empty.")
        return value.strip() if isinstance(value, str) else value
    
    def create(self, validated_data):
        # Handle image upload
        image = validated_data.pop('image', None)
        
        # Ensure keyword is a list
        if 'keyword' not in validated_data or validated_data.get('keyword') is None:
            validated_data['keyword'] = []
        
        # Ensure news_image is a list
        if 'news_image' not in validated_data or validated_data.get('news_image') is None:
            validated_data['news_image'] = []
        
        # Create the news instance
        news = News.objects.create(**validated_data)
        
        # Process image if provided
        if image:
            import base64
            from io import BytesIO
            
            # Convert image to base64
            buffer = BytesIO()
            for chunk in image.chunks():
                buffer.write(chunk)
            buffer.seek(0)
            
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            image_url = f"data:{image.content_type};base64,{image_data}"
            
            news.news_image = [image_url]
            news.save()
        
        return news
    
    def update(self, instance, validated_data):
        # Handle image upload
        image = validated_data.pop('image', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Process image if provided
        if image:
            import base64
            from io import BytesIO
            
            # Convert image to base64
            buffer = BytesIO()
            for chunk in image.chunks():
                buffer.write(chunk)
            buffer.seek(0)
            
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            image_url = f"data:{image.content_type};base64,{image_data}"
            
            instance.news_image = [image_url]
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """Customize the representation to ensure news_image data is properly formatted."""
        data = super().to_representation(instance)
        
        # Ensure news_image is always a list
        if not isinstance(data.get('news_image'), list):
            data['news_image'] = []
        
        # Ensure keyword is always a list
        if not isinstance(data.get('keyword'), list):
            data['keyword'] = []
        
        # Map fields to match frontend expectations
        data['title'] = data.get('news_title')
        data['image'] = data.get('news_image')[0] if data.get('news_image') else None
        
        return data

class ArticleSerializer(serializers.ModelSerializer):
    pdf_file = serializers.FileField(write_only=True, required=False)
    
    class Meta:
        model = Article
        fields = '__all__'
    
    def create(self, validated_data):
        # Handle PDF file upload
        pdf_file = validated_data.pop('pdf_file', None)
        
        # Create the article instance
        article = Article.objects.create(**validated_data)
        
        # Process PDF file if provided
        if pdf_file:
            article.pdf_file = pdf_file
            article.save()
        
        return article
    
    def update(self, instance, validated_data):
        # Handle PDF file upload
        pdf_file = validated_data.pop('pdf_file', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Process PDF file if provided
        if pdf_file:
            instance.pdf_file = pdf_file
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """Customize the representation to ensure article_image data is properly formatted."""
        data = super().to_representation(instance)
        
        # Ensure article_image is always a list
        if not isinstance(data.get('article_image'), list):
            data['article_image'] = []
        
        # Add full URL for PDF file if it exists
        if instance.pdf_file:
            request = self.context.get('request')
            if request:
                data['pdf_file'] = request.build_absolute_uri(instance.pdf_file.url)
            else:
                data['pdf_file'] = instance.pdf_file.url
        else:
            data['pdf_file'] = None
        
        return data