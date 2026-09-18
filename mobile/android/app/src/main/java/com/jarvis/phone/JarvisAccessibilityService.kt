package com.jarvis.phone

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class JarvisAccessibilityService : AccessibilityService() {
    companion object {
        var instance: JarvisAccessibilityService? = null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Future PHONE MODE actions will use the currently allowed app here.
        // We intentionally do not read or transmit screen content automatically.
    }

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        if (instance === this) {
            instance = null
        }
        super.onDestroy()
    }

    fun clickText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        return clickRecursive(root, text)
    }

    fun clickAnyText(vararg texts: String): Boolean {
        val root = rootInActiveWindow ?: return false
        for (text in texts) {
            if (clickRecursive(root, text)) return true
        }
        return false
    }

    fun visibleText(): String {
        val root = rootInActiveWindow ?: return ""
        val out = mutableListOf<String>()
        collectText(root, out)
        return out.distinct().joinToString("\n").take(12000)
    }

    private fun collectText(node: AccessibilityNodeInfo, out: MutableList<String>) {
        node.text?.toString()?.trim()?.takeIf { it.isNotBlank() }?.let(out::add)
        node.contentDescription?.toString()?.trim()?.takeIf { it.isNotBlank() }?.let(out::add)
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { collectText(it, out) }
        }
    }

    private fun clickRecursive(node: AccessibilityNodeInfo, text: String): Boolean {
        val nodeText = node.text?.toString()
        val description = node.contentDescription?.toString()
        if ((nodeText?.equals(text, ignoreCase = true) == true ||
                    description?.equals(text, ignoreCase = true) == true) &&
            node.isClickable) {
            return node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            if (clickRecursive(child, text)) return true
        }
        return false
    }
}
