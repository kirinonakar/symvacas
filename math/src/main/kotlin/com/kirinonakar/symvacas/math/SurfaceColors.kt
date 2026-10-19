package com.kirinonakar.symvacas.math

import kotlin.math.*

object SurfaceColors {
    // Same low-violet to high-red ramp as web/surface-colors.js and its shader.
    val stops=listOf(0xff8000ff.toInt(),0xff0000ff.toInt(),0xff00ffff.toInt(),0xff00ff00.toInt(),0xffffff00.toInt(),0xffff0000.toInt())
    fun rainbow(height:Double):Int {
        val at=height.coerceIn(0.0,1.0)*5
        val index=min(4,floor(at).toInt());val t=at-index
        fun channel(shift:Int):Int {
            val a=(stops[index] shr shift)and 255;val b=(stops[index+1] shr shift)and 255
            return (a+(b-a)*t).roundToInt() shl shift
        }
        return (255 shl 24) or channel(16) or channel(8) or channel(0)
    }
    fun gradientValue(gradient:SurfaceLighting?,point:DoubleArray,fallback:Double):Double {
        if(gradient==null)return fallback
        val dx=gradient.end[0]-gradient.start[0];val dy=gradient.end[1]-gradient.start[1]
        return gradient.min+(gradient.max-gradient.min)*((point[0]-gradient.start[0])*dx+(point[1]-gradient.start[1])*dy)/(dx*dx+dy*dy)
    }
}
