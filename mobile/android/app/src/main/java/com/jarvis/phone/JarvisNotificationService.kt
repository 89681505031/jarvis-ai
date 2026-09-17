package com.jarvis.phone

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.os.Bundle
import java.util.concurrent.CopyOnWriteArrayList

class JarvisNotificationService : NotificationListenerService() {
    companion object {
        private val messages = CopyOnWriteArrayList<IncomingMessage>()
        private const val MAX_MESSAGES = 100

        fun latest(limit: Int = 20): List<IncomingMessage> = messages.takeLast(limit).reversed()
        fun clear() = messages.clear()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val packageName = sbn.packageName
        if (packageName != WHATSAPP && packageName != TELEGRAM) return

        val extras = sbn.notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE)?.trim().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()
        if (title.isBlank() && text.isBlank()) return

        messages.add(IncomingMessage(packageName, title, text, System.currentTimeMillis()))
        while (messages.size > MAX_MESSAGES) messages.removeAt(0)
    }

    data class IncomingMessage(
        val packageName: String,
        val title: String,
        val text: String,
        val timestamp: Long
    )

    companion object Packages {
        const val WHATSAPP = "com.whatsapp"
        const val TELEGRAM = "org.telegram.messenger"
    }
}
