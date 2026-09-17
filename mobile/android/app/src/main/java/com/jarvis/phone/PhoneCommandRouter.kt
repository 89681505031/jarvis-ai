package com.jarvis.phone

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import android.telecom.TelecomManager
import java.util.Locale

class PhoneCommandRouter(private val context: Context) {
    private val pm = context.packageManager

    fun execute(raw: String): String {
        val command = raw.trim()
        val lower = command.lowercase(Locale("ru", "RU"))

        return when {
            lower == "открой браузер" || lower.contains("открой браузер") -> {
                openBrowser(command)
            }
            lower.contains("открой настройки") -> {
                context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                "Открываю настройки телефона."
            }
            lower.contains("открой камеру") -> {
                val intent = Intent("android.media.action.IMAGE_CAPTURE").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(intent)
                "Открываю камеру."
            }
            lower.startsWith("найди в интернете") || lower.startsWith("найди в интернете") -> {
                val query = command.substringAfter("найди в интернете", "").trim()
                searchWeb(query)
            }
            lower.startsWith("позвони ") -> {
                "Для звонка сначала подключим безопасный поиск контакта и подтверждение вызова."
            }
            else -> "Команда PHONE MODE пока не подключена: $command"
        }
    }

    private fun openBrowser(command: String): String {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return "Открываю браузер."
    }

    private fun searchWeb(query: String): String {
        if (query.isBlank()) return "Что найти в интернете, сэр?"
        val url = Uri.parse("https://www.google.com/search?q=" + Uri.encode(query))
        context.startActivity(Intent(Intent.ACTION_VIEW, url).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        return "Ищу в интернете: $query"
    }

    fun openPackage(packageName: String): Boolean {
        val launch = pm.getLaunchIntentForPackage(packageName) ?: return false
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(launch)
        return true
    }
}
