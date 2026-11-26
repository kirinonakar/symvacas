package com.kirinonakar.symvacas.calculator

import android.content.Context
import android.os.Bundle
import android.os.ParcelFileDescriptor
import androidx.core.os.BundleCompat
import java.io.Closeable
import java.io.File
import java.io.IOException
import java.util.zip.GZIPInputStream
import java.util.zip.GZIPOutputStream

internal class EnginePayload private constructor(
    private val text: String?,
    private val file: ParcelFileDescriptor?,
) : Closeable {
    fun toBundle(): Bundle = Bundle().apply {
        if (file == null) putString(TEXT, text) else putParcelable(FILE, file)
    }

    fun read(): String {
        if (file == null) return text ?: throw IOException("Missing engine payload")
        return ParcelFileDescriptor.AutoCloseInputStream(file).use { stream ->
            GZIPInputStream(stream).bufferedReader().use { it.readText() }
        }
    }

    override fun close() {
        file?.let { runCatching { it.close() } }
    }

    companion object {
        // Binder stores strings as UTF-16 in a shared transaction buffer.
        private const val INLINE_LIMIT = 64 * 1024
        private const val TEXT = "text"
        private const val FILE = "file"

        fun fromBundle(bundle: Bundle): EnginePayload = EnginePayload(
            bundle.getString(TEXT),
            BundleCompat.getParcelable(bundle, FILE, ParcelFileDescriptor::class.java),
        )

        fun write(context: Context, text: String): EnginePayload {
            if (text.length <= INLINE_LIMIT) return EnginePayload(text, null)

            val temp = File.createTempFile("engine-", ".gz", context.cacheDir)
            var reader: ParcelFileDescriptor? = null
            try {
                temp.outputStream().use { stream ->
                    reader = ParcelFileDescriptor.open(temp, ParcelFileDescriptor.MODE_READ_ONLY)
                    // The open descriptors keep the file alive across both processes.
                    // Unlink it before writing so it is reclaimed even on process death.
                    if (!temp.delete()) throw IOException("Could not unlink engine payload file")
                    GZIPOutputStream(stream).bufferedWriter().use { it.write(text) }
                }
                return EnginePayload(null, reader)
            } catch (failure: Throwable) {
                reader?.let { runCatching { it.close() } }
                temp.delete()
                throw failure
            }
        }
    }
}
