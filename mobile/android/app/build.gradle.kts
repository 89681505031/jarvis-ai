import org.gradle.api.tasks.Copy

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val copyJarvisIcon by tasks.registering(Copy::class) {
    from(rootProject.file("../1f4386cf-3673-4265-98a7-7bd1f57be412.png"))
    into(layout.buildDirectory.dir("generated/res/jarvisIcon/drawable"))
    rename { "jarvis_icon.png" }
}

android {
    namespace = "com.jarvis.phone"
    compileSdk = 35

    sourceSets["main"].res.srcDir(layout.buildDirectory.dir("generated/res/jarvisIcon"))

    defaultConfig {
        applicationId = "com.jarvis.phone"
        minSdk = 26
        targetSdk = 35
        versionCode = System.getenv("JARVIS_VERSION_CODE")?.toIntOrNull() ?: 2
        versionName = System.getenv("JARVIS_VERSION_NAME") ?: "0.2.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

tasks.named("preBuild") {
    dependsOn(copyJarvisIcon)
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
}
