package com.jarvis.phone

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.ContactsContract
import android.provider.Settings
import androidx.core.content.ContextCompat
import java.util.Locale

class PhoneCommandRouter(private val context: Context) {
    private val pm = context.packageManager
    private val allowedApps = AllowedAppStore(context)

    fun canHandle(raw: String): Boolean {
        val lower = raw.trim().lowercase(Locale("ru", "RU"))
        return lower == "открой браузер" || lower.contains("открой браузер") ||
            lower.contains("открой настройки") || lower.contains("открой камеру") ||
            lower.startsWith("найди в интернете") || lower.startsWith("позвони ") ||
            lower.contains("кто звонил") || lower.contains("пропущенные вызовы") ||
            lower.startsWith("открой ")
    }

    fun execute(raw: String): String {
        val command = raw.trim()
        val lower = command.lowercase(Locale("ru", "RU"))
        return when {
            lower == "открой браузер" || lower.contains("открой браузер") -> openBrowser()
            lower.contains("открой настройки") -> {
                context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                "Открываю настройки телефона."
            }
            lower.contains("открой камеру") -> {
                context.startActivity(Intent("android.media.action.IMAGE_CAPTURE").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                "Открываю камеру."
            }
            lower.startsWith("найди в интернете") -> searchWeb(command.substringAfter("найди в интернете", "").trim())
            lower.startsWith("позвони ") -> callContact(command.substringAfter("позвони ").trim())
            lower.contains("кто звонил") || lower.contains("пропущенные вызовы") -> missedCalls()
            lower.startsWith("открой ") -> openAllowedApp(command.substringAfter("открой ").trim())
            else -> "Команда PHONE MODE пока не подключена: $command"
        }
    }

    private fun openBrowser(): String {
        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        return "Открываю браузер."
    }

    private fun searchWeb(query: String): String {
        if (query.isBlank()) return "Что найти в интернете, сэр?"
        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/search?q=" + Uri.encode(query))).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        return "Ищу в интернете: $query"
    }

    private fun callContact(name: String): String {
        if (name.isBlank()) return "Назовите имя контакта."
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) return "Нужен доступ к контактам Android."
        val projection = arrayOf(ContactsContract.CommonDataKinds.Phone.NUMBER)
        val selection = "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?"
        context.contentResolver.query(ContactsContract.CommonDataKinds.Phone.CONTENT_URI, projection, selection, arrayOf("%$name%"), null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val number = cursor.getString(0)
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.CALL_PHONE) != PackageManager.PERMISSION_GRANTED) return "Нужен доступ к телефону для выполнения вызова."
                context.startActivity(Intent(Intent.ACTION_CALL, Uri.parse("tel:" + Uri.encode(number))).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                return "Звоню контакту $name."
            }
        }
        return "Контакт $name не найден."
    }

    private fun missedCalls(): String {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CALL_LOG) != PackageManager.PERMISSION_GRANTED) return "Нужен доступ к журналу вызовов Android."
        context.contentResolver.query(android.provider.CallLog.Calls.CONTENT_URI, arrayOf("number", "date", "type"), "type = ?", arrayOf("3"), "date DESC")?.use { cursor ->
            if (!cursor.moveToFirst()) return "Пропущенных вызовов не найдено."
            return "Последний пропущенный вызов: ${cursor.getString(0) ?: "неизвестный номер"}."
        }
        return "Не удалось прочитать журнал вызовов."
    }

    private fun normalizeAppName(value: String): String =
        value.trim().lowercase(Locale("ru", "RU")).replace(Regex("[^a-zа-яё0-9]+"), " ").trim()

    private fun openAllowedApp(name: String): String {
        if (name.isBlank()) return "Назовите приложение."
        val wanted = normalizeAppName(name)
        val match = launcherApps().firstOrNull {
            val label = normalizeAppName(it.label)
            label == wanted || label.contains(wanted) || wanted.contains(label)
        }
        if (match == null) return "Приложение «$name» не найдено. Откройте раздел «Приложение», найдите его и добавьте в JARVIS."
        if (!allowedApps.isAllowed(match.packageName)) return "Приложение «" + match.label + "» найдено, но не подключено. Добавьте его в разделе «Приложение»."
        return if (openPackage(match.packageName)) "Открываю " + match.label + "." else "Не удалось открыть " + match.label + "."
    }

    data class LaunchableApp(val label: String, val packageName: String)

    fun launcherApps(): List<LaunchableApp> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        return pm.queryIntentActivities(intent, PackageManager.MATCH_ALL)
            .map { LaunchableApp(it.loadLabel(pm).toString(), it.activityInfo.packageName) }
            .distinctBy { it.packageName }
            .sortedBy { it.label.lowercase(Locale.getDefault()) }
    }

    fun setAppAllowed(packageName: String, allowed: Boolean) = allowedApps.setAllowed(packageName, allowed)
    fun isAppAllowed(packageName: String): Boolean = allowedApps.isAllowed(packageName)

    fun openPackage(packageName: String): Boolean {
        val launch = pm.getLaunchIntentForPackage(packageName) ?: return false
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(launch)
        return true
    }
}
