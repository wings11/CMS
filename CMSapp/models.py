from django.db import models

class Partnership(models.Model):
    partner_name = models.CharField(max_length=255, null=True, blank=True)
    partner_image = models.JSONField(default=list)
    def __str__(self):
        return self.partner_name

class Customership(models.Model):
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_image = models.JSONField(default=list)
    def __str__(self):
        return self.customer_name

class Product(models.Model):
    product_name = models.CharField(max_length=255, null=False, blank=False)
    product_image = models.JSONField(default=list)
    product_description = models.CharField(max_length=525, null=False, blank=False)
    success = models.JSONField(default=list)
    benefit = models.JSONField(default=list)
    performance = models.JSONField(default=list)
    comments = models.TextField(null=True, blank=True)
    position = models.PositiveIntegerField(default=1, help_text="Display order position")
    def __str__(self):
        return self.product_name

class RequestForm(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('complete', 'Complete')
    ]
    full_name = models.CharField(max_length=255, null=False, blank=False)
    email_address = models.CharField(max_length=255, null=False, blank=False)
    contact_number = models.CharField(max_length=20, null=False, blank=False)
    company_name = models.CharField(max_length=255, null=False, blank=False)
    country = models.CharField(max_length=100, null=False, blank=False)
    comments = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_time = models.DateTimeField(auto_now_add=True)
    product_name = models.CharField(max_length=255, null=False, blank=False, default="Unknown")
    def __str__(self):
         return f"Request from {self.full_name} for {self.product_name}"
    
class ProjectReference(models.Model):  
    project_name = models.CharField(max_length=255, null=False, blank=False)
    project_image = models.JSONField(default=list)
    location = models.CharField(max_length=255, null=False, blank=False)
    site_area = models.CharField(max_length=255, null=False, blank=False)
    date_time = models.CharField(max_length=255, null=False, blank=False)
    contractor = models.CharField(max_length=255, null=True, blank=True)
    layout_type = models.IntegerField(default=1, choices=[(1,'Single Image'), (2,'Two Image'), (3,'Three Image'),(4,'Four Image')])
    is_favorite = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=1, help_text="Display order position")
    def __str__(self):
        return self.project_name

class News(models.Model):
    news_title = models.CharField(max_length=255, null=False, blank=False)
    news_image = models.JSONField(default=list)
    keyword = models.JSONField(null=True, blank=True, default=list)
    content = models.JSONField(null=False, blank=False, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.news_title
    
class Article(models.Model):
    article_title = models.CharField(max_length=255, null=False, blank=False)
    article_image = models.JSONField(default=list)
    keyword = models.JSONField(null=True, blank=True, default=list)
    content = models.JSONField(null=False, blank=False, default=list)
    category = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.article_title
