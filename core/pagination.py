from rest_framework.pagination import PageNumberPagination


class FlexiblePageNumberPagination(PageNumberPagination):
    """支持 ?page_size=N 参数的分页器（最大200）"""
    page_size_query_param = 'page_size'
    max_page_size = 200
