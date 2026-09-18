package com.jarvis.phone

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

class JarvisMemory(context: Context) {
    private val prefs = context.getSharedPreferences("jarvis_memory", Context.MODE_PRIVATE)
    private val lock = Any()

    fun setUserName(name: String) {
        val clean = name.trim().replace(Regex("\\s+"), " ")
        if (clean.isNotBlank()) prefs.edit().putString("user_name", clean).apply()
    }

    fun getUserName(): String = prefs.getString("user_name", "").orEmpty()

    fun rememberTurn(userText: String, assistantText: String) {
        if (userText.isBlank() || assistantText.isBlank()) return
        synchronized(lock) {
            val old = JSONArray(prefs.getString("dialogues", "[]"))
            val next = JSONArray()
            val start = maxOf(0, old.length() - 19)
            for (i in start until old.length()) next.put(old.opt(i))
            next.put(JSONObject().apply {
                put("user", userText.trim())
                put("assistant", assistantText.trim())
                put("time", System.currentTimeMillis())
            })
            prefs.edit().putString("dialogues", next.toString()).apply()
        }
    }

    fun recentDialogues(): List<Pair<String, String>> = synchronized(lock) {
        val array = JSONArray(prefs.getString("dialogues", "[]"))
        (0 until array.length()).mapNotNull { i ->
            val item = array.optJSONObject(i) ?: return@mapNotNull null
            val user = item.optString("user").trim()
            val assistant = item.optString("assistant").trim()
            if (user.isBlank() || assistant.isBlank()) null else user to assistant
        }
    }

    fun recordHabit(text: String) {
        val category = habitCategory(text)
        synchronized(lock) {
            val habits = JSONObject(prefs.getString("habits", "{}"))
            habits.put(category, habits.optInt(category, 0) + 1)
            prefs.edit().putString("habits", habits.toString()).apply()
        }
    }

    fun habitsSummary(): String {
        val habits = JSONObject(prefs.getString("habits", "{}"))
        if (habits.length() == 0) return "Пока привычки использования не накоплены."
        val names = mapOf(
            "apps" to "открытие приложений",
            "web" to "поиск в интернете",
            "calls" to "звонки и вызовы",
            "settings" to "настройки телефона",
            "camera" to "камера",
            "messages" to "чтение сообщений",
            "ai" to "вопросы ИИ",
            "other" to "другие команды"
        )
        return (0 until habits.length())
            .map { key -> key to habits.optInt(key, 0) }
            .sortedByDescending { it.second }
            .joinToString(", ") { (key, count) -> (names[key] ?: key) + ": " + count }
    }

    fun memoryContext(): String {
        val name = getUserName()
        val dialogues = recentDialogues()
        val habits = habitsSummary()
        return buildString {
            if (name.isNotBlank()) append("Имя пользователя: ").append(name).append("\n")
            append("Наблюдаемые привычки использования телефона: ").append(habits).append("\n")
            if (dialogues.isNotEmpty()) {
                append("Последние ").append(dialogues.size).append(" диалогов:\n")
                dialogues.forEachIndexed { index, pair ->
                    append(index + 1).append(". Пользователь: ").append(pair.first)
                        .append(" | Ассистент: ").append(pair.second).append("\n")
                }
            }
        }.trim()
    }

    private fun habitCategory(text: String): String {
        val s = text.lowercase(Locale("ru", "RU"))
        return when {
            s.contains("открой ") -> "apps"
            s.contains("найди в интернете") || s.contains("поищи") || s.contains("гугл") -> "web"
            s.startsWith("позвони") || s.contains("кто звонил") || s.contains("пропущенн") -> "calls"
            s.contains("настройк") -> "settings"
            s.contains("камер") -> "camera"
            s.contains("сообщен") || s.contains("telegram") || s.contains("whatsapp") -> "messages"
            else -> "ai"
        }
    }
}
