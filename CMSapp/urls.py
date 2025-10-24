from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_user import PartnershipViewSet, CustomershipViewSet, ProductViewSet, RequestFormViewSet, ProjectReferenceViewSet, NewsViewSet, ArticleViewSet
from .views_admin import AdminPartnershipViewSet, AdminCustomershipViewSet, AdminProductViewSet, AdminRequestFormViewSet, AdminProjectReferenceViewSet, AdminNewsViewSet, AdminArticleViewSet, AdminLogViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 

# Public API routes
router = DefaultRouter()
router.register(r'partnerships', PartnershipViewSet)
router.register(r'customerships', CustomershipViewSet)
router.register(r'products', ProductViewSet)
router.register(r'requestforms', RequestFormViewSet)
router.register(r'projectreferences', ProjectReferenceViewSet)
router.register(r'news', NewsViewSet)
router.register(r'articles', ArticleViewSet)

# Admin API routes
router.register(r'admin/partnerships', AdminPartnershipViewSet, basename='admin-partnership')
router.register(r'admin/customerships', AdminCustomershipViewSet, basename='admin-customer')
router.register(r'admin/products', AdminProductViewSet, basename='admin-product')
router.register(r'admin/requestforms', AdminRequestFormViewSet, basename='admin-requestform')
router.register(r'admin/projectreferences', AdminProjectReferenceViewSet, basename='admin-project')
router.register(r'admin/news', AdminNewsViewSet, basename='admin-news')
router.register(r'admin/articles', AdminArticleViewSet, basename='admin-article')
router.register(r'admin/security', AdminLogViewSet, basename='admin-security')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('admin/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]