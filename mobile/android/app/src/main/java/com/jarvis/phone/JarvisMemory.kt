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
            val commands = JSONObject(prefs.getString("habit_commands", "{}"))
            val key = text.trim().lowercase(Locale("ru", "RU")).replace(Regex("\\s+"), " ").take(120)
            if (key.isNotBlank()) commands.put(key, commands.optInt(key, 0) + 1)
            prefs.edit().putString("habits", habits.toString()).putString("habit_commands", commands.toString()).apply()
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
        val parts = mutableListOf<String>()
        val keys = habits.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            parts += (names[key] ?: key) + ": " + habits.optInt(key, 0)
        }
        return parts.sortedByDescending { it.substringAfterLast(": ").toIntOrNull() ?: 0 }.joinToString(", ")
    }

    fun memoryContext(): String {
        val name = getUserName()
        val dialogues = recentDialogues()
        val habits = habitsSummary()
        val commands = JSONObject(prefs.getString("habit_commands", "{}"))
        val commandKeys = commands.keys()
        val frequent = mutableListOf<Pair<String, Int>>()
        while (commandKeys.hasNext()) { val key = commandKeys.next(); frequent += Pair(key, commands.optInt(key, 0)) }
        val frequentText = frequent.sortedByDescending { pair -> pair.second }.take(5).joinToString(", ") { pair -> "«" + pair.first + "» (" + pair.second + " раз)" }
        return buildString {
            if (name.isNotBlank()) append("Имя пользователя: ").append(name).append("\n")
            append("Наблюдаемые привычки использования телефона: ").append(habits).append("\n")
            if (frequentText.isNotBlank()) append("Частые команды пользователя: ").append(frequentText).append("\n")
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