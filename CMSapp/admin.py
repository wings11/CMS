from django.contrib import admin
from .models import Partnership, Customership, Product, RequestForm, ProjectReference, News, Article

@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    list_display = ('partner_name', 'partner_image')

@admin.register(Customership)
class CustomershipAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_image')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_description', 'product_image')

@admin.register(RequestForm)
class RequestFormAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email_address', 'contact_number', 'company_name', 'country', 'product_name', 'request_time')

@admin.register(ProjectReference)
class ProjectReferenceAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'location', 'site_area', 'date_time', 'contractor', 'project_image')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('news_title', 'keyword', 'content', 'news_image')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('article_title', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('article_title', 'content', 'keyword')

