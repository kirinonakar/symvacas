package com.kirinonakar.symvacas.math

import kotlin.math.*

/** Data remains in real y coordinates; only the viewport uses log10 coordinates. */
class GraphYScale(val logarithmic:Boolean=false) {
    fun coordinate(value:Double)=if(logarithmic) {if(value>0)log10(value) else Double.NaN} else value
    fun value(coordinate:Double)=if(logarithmic)10.0.pow(coordinate) else coordinate
    fun fraction(y:Double,min:Double,max:Double)=(coordinate(y)-coordinate(min))/(coordinate(max)-coordinate(min))
    fun atFraction(fraction:Double,min:Double,max:Double)=value(coordinate(min)+fraction*(coordinate(max)-coordinate(min)))
    fun positiveRange(min:Double,max:Double):Pair<Double,Double> {
        if(min.isFinite()&&max.isFinite()&&min>0&&max>min)return min to max
        val high=if(max.isFinite()&&max>0)max else 10.0
        return high*.001 to high
    }
    fun fit(values:List<Double>):Pair<Double,Double>? {
        val ys=values.filter {it.isFinite()&&(!logarithmic||it>0)}.map(::coordinate)
        if(ys.isEmpty())return null
        val low=ys.min();val high=ys.max();val padding=max((high-low)*.12,if(high==low) {if(logarithmic).5 else 1.0} else 1e-6)
        return value(if(logarithmic)max(-300.0,low-padding) else low-padding) to value(if(logarithmic)min(300.0,high+padding) else high+padding)
    }
    fun ticks(min:Double,max:Double):List<Double> {
        if(min<=0||max<=min)return emptyList()
        val low=log10(min);val high=log10(max);val step=kotlin.math.max(1.0,ceil((high-low)/8));val first=ceil(low/step)*step
        val ticks=(0..9).map {first+it*step}.filter {it<=high+1e-12}.map {10.0.pow(it)}
        return if(ticks.size>=2)ticks else (0..4).map {10.0.pow(low+(high-low)*it/4)}
    }
    fun segment(first:Pair<Double,Double>?,last:Pair<Double,Double>?,xmin:Double,xmax:Double,ymin:Double,ymax:Double):Pair<Pair<Double,Double>,Pair<Double,Double>>? {
        if(!logarithmic)return GraphClip.segment(first,last,xmin,xmax,ymin,ymax)
        if(first==null||last==null)return null
        val pair=if(first.second<=0||last.second<=0)GraphClip.segment(first,last,xmin,xmax,ymin,ymax) ?: return null else first to last
        val line=GraphClip.segment(pair.first.first to coordinate(pair.first.second),pair.second.first to coordinate(pair.second.second),xmin,xmax,coordinate(ymin),coordinate(ymax)) ?: return null
        return (line.first.first to value(line.first.second)) to (line.second.first to value(line.second.second))
    }
    fun view(min:Double,max:Double,previous:Double,current:Double,zoom:Double):Pair<Double,Double> {
        val span=coordinate(max)-coordinate(min);val anchor=coordinate(max)-span*previous
        val next=(span/zoom).coerceIn(2e-7,if(logarithmic)600.0 else 2e8)
        val high=anchor+next*current
        return value(if(logarithmic)(high-next).coerceIn(-300.0,300.0-next) else high-next) to value(if(logarithmic)high.coerceIn(next-300.0,300.0) else high)
    }
    fun linePoints(first:Pair<Double,Double>,last:Pair<Double,Double>,xmin:Double,xmax:Double,ymin:Double,ymax:Double):List<Pair<Double,Double>> {
        val segment=GraphClip.segment(first,last,xmin,xmax,ymin,ymax) ?: return emptyList()
        val (a,b)=segment;if(!logarithmic||a.second==b.second)return listOf(a,b)
        return (0..64).map {i->val y=atFraction(i/64.0,a.second,b.second);val t=(y-a.second)/(b.second-a.second);(a.first+t*(b.first-a.first)) to y}
    }
    fun polygon(points:List<Pair<Double,Double>>,xmin:Double,xmax:Double,ymin:Double,ymax:Double):List<Pair<Double,Double>> {
        if(points.any {!it.first.isFinite()||!it.second.isFinite()})return emptyList()
        var polygon=points
        for((axis,edge,lower) in listOf(Triple(0,xmin,true),Triple(0,xmax,false),Triple(1,ymin,true),Triple(1,ymax,false))) {
            val output=mutableListOf<Pair<Double,Double>>();var a=polygon.lastOrNull() ?: return emptyList()
            fun coordinate(p:Pair<Double,Double>)=if(axis==0)p.first else p.second
            for(b in polygon) {
                val av=coordinate(a);val bv=coordinate(b);val inA=if(lower)av>=edge else av<=edge;val inB=if(lower)bv>=edge else bv<=edge
                if(inA!=inB) {val t=(edge-av)/(bv-av);output.add(if(axis==0)edge to (a.second+t*(b.second-a.second)) else (a.first+t*(b.first-a.first)) to edge)}
                if(inB)output.add(b);a=b
            };polygon=output
        };return polygon
    }
}
