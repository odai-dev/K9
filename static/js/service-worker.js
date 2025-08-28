// Service Worker للإشعارات الفورية
const CACHE_NAME = 'k9-notifications-v1';

// تثبيت Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

// تفعيل Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// معالجة Push Notifications
self.addEventListener('push', event => {
    console.log('Push notification received:', event);

    let notificationData = {
        title: 'إشعار جديد',
        body: 'لديك إشعار جديد من نظام K9',
        icon: '/static/img/logo.png',
        badge: '/static/img/logo.png',
        data: {}
    };

    // تحليل بيانات الإشعار
    if (event.data) {
        try {
            const data = event.data.json();
            notificationData = {
                ...notificationData,
                ...data
            };
        } catch (e) {
            console.error('Error parsing push data:', e);
            notificationData.body = event.data.text() || notificationData.body;
        }
    }

    // إظهار الإشعار
    const notificationPromise = self.registration.showNotification(
        notificationData.title,
        {
            body: notificationData.body,
            icon: notificationData.icon,
            badge: notificationData.badge,
            data: notificationData.data,
            actions: notificationData.actions || [
                {
                    action: 'open',
                    title: 'عرض',
                    icon: '/static/img/logo.png'
                },
                {
                    action: 'dismiss',
                    title: 'إغلاق'
                }
            ],
            requireInteraction: notificationData.data?.priority === 'URGENT',
            tag: notificationData.data?.type || 'k9-notification',
            timestamp: Date.now(),
            vibrate: [200, 100, 200], // نمط الاهتزاز
            sound: '/static/sounds/notification.mp3' // صوت الإشعار (إذا توفر)
        }
    );

    event.waitUntil(notificationPromise);
});

// معالجة النقر على الإشعار
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    
    const notification = event.notification;
    const action = event.action;
    const data = notification.data || {};

    notification.close();

    if (action === 'dismiss') {
        // إغلاق الإشعار فقط
        return;
    }

    // تحديد الرابط للفتح
    let urlToOpen = '/dashboard';
    
    if (action === 'open' && data.action_url) {
        urlToOpen = data.action_url;
    } else if (data.action_url) {
        urlToOpen = data.action_url;
    }

    // فتح النافذة أو التركيز عليها
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(clientList => {
            // البحث عن نافذة مفتوحة للتطبيق
            for (let client of clientList) {
                if (client.url.includes(self.location.origin)) {
                    if (client.focus) {
                        return client.focus().then(() => {
                            // إرسال رسالة للصفحة للانتقال للرابط المطلوب
                            return client.postMessage({
                                type: 'NOTIFICATION_CLICK',
                                url: urlToOpen,
                                notificationId: data.id
                            });
                        });
                    }
                }
            }
            
            // فتح نافذة جديدة إذا لم توجد
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );

    // تسجيل النقر في قاعدة البيانات (إذا أمكن)
    if (data.id) {
        event.waitUntil(
            fetch('/api/notifications/mark-clicked', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notification_id: data.id,
                    action: action
                })
            }).catch(err => {
                console.error('Error marking notification as clicked:', err);
            })
        );
    }
});

// معالجة إغلاق الإشعار
self.addEventListener('notificationclose', event => {
    console.log('Notification closed:', event);
    
    const notification = event.notification;
    const data = notification.data || {};
    
    // تسجيل إغلاق الإشعار (إذا أمكن)
    if (data.id) {
        event.waitUntil(
            fetch('/api/notifications/mark-dismissed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notification_id: data.id
                })
            }).catch(err => {
                console.error('Error marking notification as dismissed:', err);
            })
        );
    }
});

// معالجة الرسائل من الصفحة الرئيسية
self.addEventListener('message', event => {
    console.log('Service Worker received message:', event.data);
    
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'GET_VERSION':
            event.ports[0].postMessage({
                version: CACHE_NAME
            });
            break;
            
        case 'CLEAR_NOTIFICATIONS':
            // إغلاق جميع الإشعارات المعروضة
            self.registration.getNotifications().then(notifications => {
                notifications.forEach(notification => {
                    notification.close();
                });
            });
            break;
            
        default:
            console.log('Unknown message type:', type);
    }
});

// معالجة تحديث Service Worker
self.addEventListener('controllerchange', event => {
    console.log('Service Worker controller changed');
    // يمكن إعادة تحميل الصفحة هنا إذا لزم الأمر
});

// معالجة الأخطاء
self.addEventListener('error', event => {
    console.error('Service Worker error:', event);
});

// معالجة الأخطاء غير المعالجة
self.addEventListener('unhandledrejection', event => {
    console.error('Service Worker unhandled rejection:', event);
});

// دالة مساعدة لإرسال الإحصائيات
function sendAnalytics(eventName, data) {
    try {
        fetch('/api/analytics/service-worker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event: eventName,
                data: data,
                timestamp: Date.now(),
                userAgent: navigator.userAgent
            })
        }).catch(err => {
            console.error('Error sending analytics:', err);
        });
    } catch (e) {
        console.error('Analytics error:', e);
    }
}