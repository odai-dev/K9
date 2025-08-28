// نظام الإشعارات الفورية - K9 Operations Management System
class NotificationManager {
    constructor() {
        this.socket = null;
        this.serviceWorkerRegistration = null;
        this.vapidPublicKey = null;
        this.isConnected = false;
        this.notifications = [];
        this.settings = {
            enabled: true,
            browser_notifications: true,
            push_notifications: true,
            quiet_hours_start: null,
            quiet_hours_end: null
        };
        
        this.init();
    }

    async init() {
        try {
            // تحميل مفتاح VAPID العام
            await this.loadVapidKey();
            
            // تسجيل Service Worker
            await this.registerServiceWorker();
            
            // تهيئة WebSocket
            this.initWebSocket();
            
            // تحميل الإعدادات
            await this.loadSettings();
            
            // طلب إذن الإشعارات
            await this.requestNotificationPermission();
            
            // تهيئة الواجهة
            this.initUI();
            
            console.log('Notification Manager initialized successfully');
            
        } catch (error) {
            console.error('Error initializing Notification Manager:', error);
        }
    }

    async loadVapidKey() {
        try {
            const response = await fetch('/api/notifications/vapid-key');
            if (response.ok) {
                const data = await response.json();
                this.vapidPublicKey = data.public_key;
            }
        } catch (error) {
            console.error('Error loading VAPID key:', error);
        }
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.serviceWorkerRegistration = await navigator.serviceWorker.register('/static/js/service-worker.js');
                console.log('Service Worker registered successfully');
                
                // معالجة رسائل Service Worker
                navigator.serviceWorker.addEventListener('message', (event) => {
                    this.handleServiceWorkerMessage(event);
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    initWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
            });

            this.socket.on('notification', (data) => {
                this.handleNewNotification(data);
            });

            this.socket.on('unread_notifications', (data) => {
                this.handleUnreadNotifications(data);
            });

            this.socket.on('notification_read', (data) => {
                this.markNotificationAsRead(data.id);
            });

            this.socket.on('error', (data) => {
                console.error('WebSocket error:', data);
                this.showToast(data.message, 'error');
            });

        } catch (error) {
            console.error('Error initializing WebSocket:', error);
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/notifications/settings');
            if (response.ok) {
                const data = await response.json();
                this.settings = { ...this.settings, ...data };
                this.updateSettingsUI();
            }
        } catch (error) {
            console.error('Error loading notification settings:', error);
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('Notification permission granted');
                
                // تسجيل Push Notifications إذا كان مدعوم
                if (this.settings.push_notifications && this.serviceWorkerRegistration && this.vapidPublicKey) {
                    await this.subscribeToPushNotifications();
                }
            } else {
                console.log('Notification permission denied');
                this.settings.browser_notifications = false;
                this.settings.push_notifications = false;
            }
        }
    }

    async subscribeToPushNotifications() {
        try {
            // التحقق من الاشتراك الحالي
            let subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
            
            if (!subscription) {
                // إنشاء اشتراك جديد
                subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
                });
            }
            
            // حفظ الاشتراك في الخادم
            this.socket.emit('subscribe_push_notifications', {
                subscription: subscription.toJSON()
            });
            
            console.log('Push notifications subscription successful');
            
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    handleNewNotification(notification) {
        console.log('New notification received:', notification);
        
        // إضافة للقائمة
        this.notifications.unshift(notification);
        
        // تحديث العداد
        this.updateNotificationCount();
        
        // عرض إشعار المتصفح إذا كان مفعل
        if (this.settings.browser_notifications && 'Notification' in window && Notification.permission === 'granted') {
            this.showBrowserNotification(notification);
        }
        
        // عرض Toast notification
        this.showToast(notification.title, this.getPriorityType(notification.priority), notification.action_url);
        
        // تحديث قائمة الإشعارات
        this.updateNotificationsList();
        
        // تشغيل صوت الإشعار
        this.playNotificationSound(notification.priority);
    }

    showBrowserNotification(notification) {
        const options = {
            body: notification.message,
            icon: '/static/img/logo.png',
            badge: '/static/img/logo.png',
            tag: notification.id,
            requireInteraction: notification.priority === 'URGENT',
            actions: []
        };

        if (notification.action_url) {
            options.actions.push({
                action: 'open',
                title: 'عرض التفاصيل'
            });
        }

        options.actions.push({
            action: 'dismiss',
            title: 'إغلاق'
        });

        const browserNotification = new Notification(notification.title, options);
        
        browserNotification.onclick = () => {
            if (notification.action_url) {
                window.focus();
                window.location.href = notification.action_url;
            }
            this.markAsRead(notification.id);
            browserNotification.close();
        };

        // إغلاق تلقائي بعد 5 ثوان للإشعارات العادية
        if (notification.priority !== 'URGENT') {
            setTimeout(() => {
                browserNotification.close();
            }, 5000);
        }
    }

    showToast(title, type = 'info', actionUrl = null) {
        // إنشاء Toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${this.getBootstrapType(type)} border-0`;
        toast.setAttribute('role', 'alert');
        toast.style.cssText = 'position: fixed; top: 20px; left: 20px; z-index: 9999; min-width: 300px;';
        
        const toastBody = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        if (actionUrl) {
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong>
                        <br>
                        <a href="${actionUrl}" class="text-white text-decoration-underline">عرض التفاصيل</a>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;
        } else {
            toast.innerHTML = toastBody;
        }
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
        bsToast.show();
        
        // إزالة العنصر بعد الإخفاء
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }

    playNotificationSound(priority) {
        try {
            // إنشاء صوت الإشعار
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // تحديد نغمة حسب الأولوية
            let frequency = 800; // افتراضي
            let duration = 200;
            
            switch (priority) {
                case 'URGENT':
                    frequency = 1000;
                    duration = 500;
                    break;
                case 'HIGH':
                    frequency = 900;
                    duration = 300;
                    break;
                case 'MEDIUM':
                    frequency = 800;
                    duration = 200;
                    break;
                case 'LOW':
                    frequency = 700;
                    duration = 150;
                    break;
            }
            
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration / 1000);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration / 1000);
            
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    }

    getPriorityType(priority) {
        const types = {
            'URGENT': 'danger',
            'HIGH': 'warning',
            'MEDIUM': 'info',
            'LOW': 'secondary'
        };
        return types[priority] || 'info';
    }

    getBootstrapType(type) {
        const types = {
            'danger': 'danger',
            'warning': 'warning',
            'info': 'primary',
            'secondary': 'secondary',
            'success': 'success',
            'error': 'danger'
        };
        return types[type] || 'primary';
    }

    handleUnreadNotifications(data) {
        this.notifications = data.notifications;
        this.updateNotificationCount();
        this.updateNotificationsList();
    }

    markAsRead(notificationId) {
        this.socket.emit('mark_notification_read', {
            notification_id: notificationId
        });
    }

    markNotificationAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.status = 'READ';
            notification.read_at = new Date().toISOString();
        }
        this.updateNotificationCount();
        this.updateNotificationsList();
    }

    updateNotificationCount() {
        const unreadCount = this.notifications.filter(n => n.status !== 'READ').length;
        
        // تحديث شارة العداد
        const badge = document.querySelector('#notification-badge');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }
        
        // تحديث عنوان الصفحة
        if (unreadCount > 0) {
            document.title = `(${unreadCount}) K9 Operations`;
        } else {
            document.title = 'K9 Operations';
        }
    }

    updateNotificationsList() {
        const container = document.querySelector('#notifications-list');
        if (!container) return;
        
        if (this.notifications.length === 0) {
            container.innerHTML = '<div class="text-center p-3 text-muted">لا توجد إشعارات</div>';
            return;
        }
        
        const html = this.notifications.slice(0, 10).map(notification => {
            const isUnread = notification.status !== 'READ';
            const timeAgo = this.getTimeAgo(new Date(notification.created_at));
            
            return `
                <div class="notification-item ${isUnread ? 'unread' : ''}" data-id="${notification.id}">
                    <div class="d-flex justify-content-between align-items-start p-3 border-bottom">
                        <div class="flex-grow-1">
                            <h6 class="mb-1 ${isUnread ? 'fw-bold' : ''}">${notification.title}</h6>
                            <p class="mb-1 small text-muted">${notification.message}</p>
                            <small class="text-muted">${timeAgo}</small>
                        </div>
                        <div class="ms-2">
                            <span class="badge bg-${this.getPriorityType(notification.priority)}">${this.getPriorityText(notification.priority)}</span>
                            ${isUnread ? '<span class="badge bg-primary ms-1">جديد</span>' : ''}
                        </div>
                    </div>
                    ${notification.action_url ? `
                        <div class="p-2 bg-light">
                            <a href="${notification.action_url}" class="btn btn-sm btn-outline-primary">عرض التفاصيل</a>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        container.innerHTML = html;
        
        // إضافة معالجات النقر
        container.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = item.dataset.id;
                if (item.classList.contains('unread')) {
                    this.markAsRead(notificationId);
                }
            });
        });
    }

    getPriorityText(priority) {
        const texts = {
            'URGENT': 'عاجل',
            'HIGH': 'مهم',
            'MEDIUM': 'متوسط',
            'LOW': 'منخفض'
        };
        return texts[priority] || 'عادي';
    }

    getTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (days > 0) return `منذ ${days} يوم`;
        if (hours > 0) return `منذ ${hours} ساعة`;
        if (minutes > 0) return `منذ ${minutes} دقيقة`;
        return 'الآن';
    }

    updateConnectionStatus(connected) {
        const indicator = document.querySelector('#connection-status');
        if (indicator) {
            if (connected) {
                indicator.className = 'badge bg-success';
                indicator.textContent = 'متصل';
            } else {
                indicator.className = 'badge bg-danger';
                indicator.textContent = 'غير متصل';
            }
        }
    }

    initUI() {
        // إضافة أيقونة الإشعارات للهيدر
        this.addNotificationIcon();
        
        // إضافة modal الإعدادات
        this.addSettingsModal();
        
        // معالجة النقرات
        this.bindEvents();
    }

    addNotificationIcon() {
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        const notificationItem = document.createElement('li');
        notificationItem.className = 'nav-item dropdown';
        notificationItem.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" id="notificationDropdown" role="button" 
               data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fas fa-bell"></i>
                <span id="notification-badge" class="badge bg-danger position-absolute top-0 start-100 translate-middle" 
                      style="display: none;">0</span>
            </a>
            <div class="dropdown-menu dropdown-menu-end notification-dropdown" style="width: 400px; max-height: 500px; overflow-y: auto;">
                <div class="dropdown-header d-flex justify-content-between align-items-center">
                    <span>الإشعارات</span>
                    <div>
                        <span id="connection-status" class="badge bg-secondary me-2">غير متصل</span>
                        <button class="btn btn-sm btn-outline-primary" onclick="notificationManager.openSettings()">
                            <i class="fas fa-cog"></i>
                        </button>
                    </div>
                </div>
                <div id="notifications-list">
                    <div class="text-center p-3 text-muted">جاري التحميل...</div>
                </div>
                <div class="dropdown-divider"></div>
                <div class="text-center p-2">
                    <button class="btn btn-sm btn-primary" onclick="notificationManager.loadAllNotifications()">
                        عرض جميع الإشعارات
                    </button>
                </div>
            </div>
        `;
        
        navbar.appendChild(notificationItem);
    }

    addSettingsModal() {
        const modalHtml = `
            <div class="modal fade" id="notificationSettingsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">إعدادات الإشعارات</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="notification-settings-form">
                                <div class="mb-3">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="enabled">
                                        <label class="form-check-label" for="enabled">تفعيل الإشعارات</label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <h6>أنواع الإشعارات</h6>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="attendance_alerts">
                                        <label class="form-check-label" for="attendance_alerts">تنبيهات الحضور</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="vaccination_reminders">
                                        <label class="form-check-label" for="vaccination_reminders">تذكيرات التطعيم</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="project_updates">
                                        <label class="form-check-label" for="project_updates">تحديثات المشاريع</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="heat_cycle_alerts">
                                        <label class="form-check-label" for="heat_cycle_alerts">تنبيهات دورة الحرارة</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="emergency_alerts">
                                        <label class="form-check-label" for="emergency_alerts">التنبيهات الطارئة</label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <h6>قنوات الإشعار</h6>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="browser_notifications">
                                        <label class="form-check-label" for="browser_notifications">إشعارات المتصفح</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="push_notifications">
                                        <label class="form-check-label" for="push_notifications">الإشعارات الفورية</label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <h6>الساعات الهادئة</h6>
                                    <div class="row">
                                        <div class="col-6">
                                            <label for="quiet_hours_start" class="form-label">من</label>
                                            <input type="time" class="form-control" id="quiet_hours_start">
                                        </div>
                                        <div class="col-6">
                                            <label for="quiet_hours_end" class="form-label">إلى</label>
                                            <input type="time" class="form-control" id="quiet_hours_end">
                                        </div>
                                    </div>
                                    <small class="text-muted">خلال هذه الفترة لن يتم إرسال إشعارات غير طارئة</small>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                            <button type="button" class="btn btn-primary" onclick="notificationManager.saveSettings()">حفظ</button>
                            <button type="button" class="btn btn-info" onclick="notificationManager.testNotification()">اختبار</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    bindEvents() {
        // معالجة رسائل Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data.type === 'NOTIFICATION_CLICK') {
                    window.location.href = event.data.url;
                    if (event.data.notificationId) {
                        this.markAsRead(event.data.notificationId);
                    }
                }
            });
        }
    }

    openSettings() {
        this.updateSettingsUI();
        const modal = new bootstrap.Modal(document.getElementById('notificationSettingsModal'));
        modal.show();
    }

    updateSettingsUI() {
        const form = document.getElementById('notification-settings-form');
        if (!form) return;
        
        Object.keys(this.settings).forEach(key => {
            const input = form.querySelector(`#${key}`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = this.settings[key];
                } else {
                    input.value = this.settings[key] || '';
                }
            }
        });
    }

    async saveSettings() {
        const form = document.getElementById('notification-settings-form');
        const formData = new FormData(form);
        const settings = {};
        
        // تحويل البيانات
        form.querySelectorAll('input').forEach(input => {
            if (input.type === 'checkbox') {
                settings[input.id] = input.checked;
            } else {
                settings[input.id] = input.value || null;
            }
        });
        
        // إرسال التحديث
        this.socket.emit('update_notification_settings', settings);
        
        // تحديث الإعدادات المحلية
        this.settings = { ...this.settings, ...settings };
        
        // إغلاق المودال
        const modal = bootstrap.Modal.getInstance(document.getElementById('notificationSettingsModal'));
        modal.hide();
        
        this.showToast('تم حفظ الإعدادات بنجاح', 'success');
    }

    testNotification() {
        this.socket.emit('test_notification');
    }

    loadAllNotifications() {
        this.socket.emit('get_notifications', { limit: 50, unread_only: false });
    }

    handleServiceWorkerMessage(event) {
        const { type, data } = event.data;
        
        switch (type) {
            case 'NOTIFICATION_CLICK':
                if (data.url) {
                    window.location.href = data.url;
                }
                if (data.notificationId) {
                    this.markAsRead(data.notificationId);
                }
                break;
        }
    }
}

// تهيئة مدير الإشعارات عند تحميل الصفحة
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    notificationManager = new NotificationManager();
});

// تصدير للاستخدام العالمي
window.notificationManager = notificationManager;