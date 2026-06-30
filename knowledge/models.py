from django.conf import settings
from django.db import models


class FarmingGuide(models.Model):
    """农业技术知识库"""
    CATEGORY_CHOICES = [
        ('planting', '种植技术'),
        ('pest', '病虫害防治'),
        ('fertilizer', '施肥管理'),
        ('harvest', '采收储存'),
        ('storage', '保鲜运输'),
        ('other', '其他'),
    ]
    CROP_CHOICES = [
        ('rice', '水稻'),
        ('wheat', '小麦'),
        ('corn', '玉米'),
        ('fruit', '水果'),
        ('vegetable', '蔬菜'),
        ('tea', '茶叶'),
        ('herb', '中药材'),
        ('livestock', '畜禽'),
        ('aquatic', '水产'),
        ('general', '通用'),
    ]
    title = models.CharField(max_length=200, verbose_name='标题')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name='分类')
    crop_type = models.CharField(max_length=20, choices=CROP_CHOICES, default='general', verbose_name='适用作物')
    content = models.TextField(verbose_name='内容')
    cover_image = models.CharField(max_length=500, blank=True, verbose_name='封面图片URL')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作者')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_farmingguide'
        ordering = ['-created_at']
        verbose_name = '农业技术指南'
        verbose_name_plural = '农业技术指南'

    def __str__(self):
        return self.title
