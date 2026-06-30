"""通知发送辅助函数"""
from .models import Notification

def notify(recipient, notification_type, title, message='', link=''):
    """创建一条站内通知"""
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )

def notify_farmer(product, notification_type, title, message='', link=''):
    """通知产品的农户"""
    farmer_user = product.farmer.user
    return notify(farmer_user, notification_type, title, message, link)

def notify_buyer(order, notification_type, title, message='', link=''):
    """通知订单的买家"""
    return notify(order.buyer, notification_type, title, message, link)
