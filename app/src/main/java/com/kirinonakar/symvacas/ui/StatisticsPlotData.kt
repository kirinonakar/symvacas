package com.kirinonakar.symvacas.ui

import kotlin.math.*

internal data class StatisticsScatterColumns(val groupColumn:Int,val xColumn:Int,val yColumn:Int)
internal fun statisticsScatterColumns(count:Int,grouping:String="columns",xColumn:Int=0,yColumn:Int=1):StatisticsScatterColumns {
    val group=if(count>=3)statisticsPlotGroupingColumn(grouping,count) else -1
    val columns=(0 until count).filter {it!=group}
    val x=xColumn.takeIf {it in columns} ?: columns.firstOrNull() ?: -1
    val y=yColumn.takeIf {it in columns&&it!=x} ?: columns.firstOrNull {it!=x} ?: -1
    return StatisticsScatterColumns(group,x,y)
}
internal data class StatisticsScatterSeries(val label:String,val points:List<Pair<Double,Double>>)
internal data class StatisticsScatterData(val columns:StatisticsScatterColumns,val series:List<StatisticsScatterSeries>,val dateAxis:StatisticsDateAxis?)
internal fun statisticsScatterData(rows:List<List<String>>,kind:String,grouping:String="columns",xColumn:Int=0,yColumn:Int=1):StatisticsScatterData {
    val columns=statisticsScatterColumns(statisticsColumnCount(kind),grouping,xColumn,yColumn)
    val pairs=rows.map {listOf(it.getOrNull(columns.xColumn).orEmpty(),it.getOrNull(columns.yColumn).orEmpty())}
    val dateAxis=statisticsDateAxis(pairs)
    val numeric=statisticsNumericRows(pairs,dateAxis)
    val groups=linkedMapOf<String,MutableList<Pair<Double,Double>>>()
    numeric.forEachIndexed {index,row->
        val x=statisticsPlotNumber(row.getOrNull(0));val y=statisticsPlotNumber(row.getOrNull(1))
        val label=if(columns.groupColumn<0)"" else rows[index].getOrNull(columns.groupColumn)?.trim().orEmpty()
        if(x!=null&&y!=null&&(columns.groupColumn<0||label.isNotBlank()))groups.getOrPut(label){mutableListOf()}.add(x to y)
    }
    return StatisticsScatterData(columns,groups.map {(label,points)->StatisticsScatterSeries(label,points)},dateAxis)
}

internal data class StatisticsHistogramData(val scale:Double,val minimum:Double,val span:Double,val bins:Int,val counts:List<List<Int>>,val heights:List<List<Double>>,val curves:List<List<Pair<Double,Double>>>,val viewMinimum:Double,val viewMaximum:Double,val peak:Double,val kde:Boolean,val unavailable:List<Int>)

/** Keep density in normalized x units, converting to physical units only for labels. */
internal fun statisticsHistogramData(series:List<List<Double>>,kde:Boolean=false):StatisticsHistogramData {
    val finite=series.map {it.filter(Double::isFinite)};val all=finite.flatten()
    var scale=all.maxOfOrNull {abs(it)}?.takeIf {it>0} ?: 1.0
    if(all.isNotEmpty()&&all.all {it==all.first()}&&scale<1)scale=1.0
    var minimum=(all.minOrNull() ?: 0.0)/scale;var maximum=(all.maxOrNull() ?: 1.0)/scale
    if(minimum==maximum){val pad=max(.5/scale,abs(minimum)*.05);minimum-=pad;maximum+=pad}
    val limit=Double.MAX_VALUE/scale;minimum=max(-limit,minimum);maximum=min(limit,maximum)
    val span=maximum-minimum;val bins=ceil(1+ln(all.size.coerceAtLeast(2).toDouble())/ln(2.0)).toInt().coerceIn(3,14)
    val normalized=finite.map {values->values.map {(it/scale-minimum)/span}}
    val counts=normalized.map {values->IntArray(bins).also {row->values.forEach {row[floor(it*bins).toInt().coerceIn(0,bins-1)]++}}.toList()}
    val heights=counts.mapIndexed {index,row->row.map {if(kde&&finite[index].isNotEmpty())it.toDouble()*bins/finite[index].size else it.toDouble()}}
    val lowerLimit=(-limit-minimum)/span;val upperLimit=(limit-minimum)/span
    val curves=normalized.map {values->
        if(!kde||values.size<2)return@map emptyList<Pair<Double,Double>>()
        val lo=values.min();val hi=values.max();if(lo==hi)return@map emptyList<Pair<Double,Double>>()
        val mean=values.sumOf {it/values.size};val sd=sqrt(values.sumOf {(it-mean).pow(2)/(values.size-1)})
        val bandwidth=sd*values.size.toDouble().pow(-.2);if(bandwidth<=0)return@map emptyList<Pair<Double,Double>>()
        val start=max(lowerLimit,lo-3*bandwidth);val end=min(upperLimit,hi+3*bandwidth);val divisor=values.size*bandwidth*sqrt(2*PI)
        List(129) {index->val fraction=index/128.0;val at=start*(1-fraction)+end*fraction;at to values.sumOf {exp(-.5*((at-it)/bandwidth).pow(2))}/divisor}
            .takeIf {points->points.all {it.second.isFinite()}} ?: emptyList()
    }
    val points=curves.flatten();val viewMinimum=minOf(0.0,points.minOfOrNull {it.first} ?: 0.0);val viewMaximum=maxOf(1.0,points.maxOfOrNull {it.first} ?: 1.0)
    val peak=maxOf(heights.flatten().maxOrNull() ?: 0.0,points.maxOfOrNull {it.second} ?: 0.0).takeIf {it>0} ?: 1.0
    return StatisticsHistogramData(scale,minimum,span,bins,counts,heights,curves,viewMinimum,viewMaximum,peak,kde,if(kde)curves.indices.filter {curves[it].isEmpty()} else emptyList())
}

internal fun histogramDensityNumber(value:Double,data:StatisticsHistogramData):String {
    if(value==0.0)return "0"
    val density=value/data.span/data.scale
    if(density.isFinite()&&density>0)return density.toString()
    val logarithm=log10(value)-log10(data.span)-log10(data.scale);val exponent=floor(logarithm).toInt()
    return "${10.0.pow(logarithm-exponent)}e$exponent"
}

internal data class StatisticsFrequencyData(val values:List<Double>,val counts:List<List<Int>>,val positions:List<Double>,val barWidth:Double,val peak:Int)

internal data class StatisticsNamedBarSeries(val label:String,val values:List<Double?>)
internal data class StatisticsNamedBarData(val labels:List<String>,val series:List<StatisticsNamedBarSeries>,val categoryLabel:String,val valueLabel:String,val minimum:Double,val maximum:Double,val baseline:Double,val positions:List<List<Double?>>)

/** x supplies names, numeric columns supply heights, and an optional column supplies groups. */
internal fun statisticsNamedBarData(rows:List<List<String>>,kind:String,grouping:String="columns",columnNames:List<String> = statisticsColumnNames(kind)):StatisticsNamedBarData {
    val columns=statisticsColumnNames(kind).indices
    val groupColumn=statisticsPlotGroupingColumn(grouping,columns.count())
    val categoryColumn=columns.firstOrNull {it!=groupColumn} ?: 0
    val valueColumns=columns.filter {it!=groupColumn&&it!=categoryColumn&&rows.any {row->statisticsPlotNumber(row.getOrNull(it))!=null}}
    val labels=mutableListOf<String>();val series=linkedMapOf<Pair<String,Int>,MutableMap<Int,Double?>>()
    val slots=mutableMapOf<Pair<String,Int>,Int>();val occurrences=mutableMapOf<Pair<String,String>,Int>()
    rows.forEach {row->
        val label=row.getOrNull(categoryColumn)?.trim().orEmpty();val group=if(groupColumn<0)"" else row.getOrNull(groupColumn)?.trim().orEmpty()
        if(label.isBlank()||groupColumn>=0&&group.isBlank()||valueColumns.none {statisticsPlotNumber(row.getOrNull(it))!=null})return@forEach
        val slot=if(groupColumn<0)labels.size.also {labels.add(label)} else {
            val key=group to label;val occurrence=occurrences[key] ?: 0;occurrences[key]=occurrence+1
            slots.getOrPut(label to occurrence){labels.size.also {labels.add(label)}}
        }
        valueColumns.forEach {column->series.getOrPut(group to column){mutableMapOf()}[slot]=statisticsPlotNumber(row.getOrNull(column))}
    }
    val entries=series.map {(key,values)->
        val (group,column)=key
        StatisticsNamedBarSeries(if(groupColumn<0)columnNames[column] else if(valueColumns.size==1)group else "$group · ${columnNames[column]}",List(labels.size){values[it]})
    }
    val values=entries.flatMap {it.values}.filterNotNull()
    val minimum=minOf(0.0,values.minOrNull() ?: 0.0);val maximum=maxOf(0.0,values.maxOrNull() ?: 0.0)
    val scale=maxOf(abs(minimum),abs(maximum)).takeIf {it>0} ?: 1.0;val span=maximum/scale-minimum/scale
    fun position(value:Double)=if(span==0.0)1.0 else (maximum/scale-value/scale)/span
    return StatisticsNamedBarData(labels,entries,columnNames[categoryColumn],if(valueColumns.size==1)columnNames[valueColumns[0]] else "Value",minimum,maximum,position(0.0),entries.map {entry->entry.values.map {it?.let(::position)}})
}

/** One bar per observed numeric value, retaining the spacing on the value axis. */
internal fun statisticsFrequencyData(series:List<List<Double>>):StatisticsFrequencyData {
    val frequencies=series.map {values->values.filter(Double::isFinite).map {if(it==0.0)0.0 else it}.groupingBy {it}.eachCount()}
    val values=frequencies.flatMap {it.keys}.distinct().sorted()
    val counts=frequencies.map {entry->values.map {entry[it] ?: 0}}
    val peak=counts.maxOfOrNull {it.maxOrNull() ?: 0}?.coerceAtLeast(1) ?: 1
    val scale=values.maxOfOrNull {abs(it)}?.takeIf {it>0} ?: 1.0
    val lo=(values.firstOrNull() ?: 0.0)/scale;val hi=(values.lastOrNull() ?: 0.0)/scale;val span=hi-lo
    val positions=values.map {if(span==0.0).5 else .08+.84*((it/scale-lo)/span)}
    var barWidth=.08
    for(i in 1 until positions.size) {
        val gap=positions[i]-positions[i-1]
        if(gap>0)barWidth=min(barWidth,gap*.75)
    }
    return StatisticsFrequencyData(values,counts,positions,barWidth,peak)
}

/** Gaussian KDE with Scott's bandwidth, normalized to each violin's peak. */
internal fun violinDensity(values:List<Double>):List<Pair<Double,Double>> {
    val finite=values.filter(Double::isFinite)
    if(finite.size<2)return emptyList()
    val scale=finite.maxOf {abs(it)}.takeIf {it>0} ?: 1.0
    val data=finite.map {it/scale};val lo=data.min();val hi=data.max()
    if(lo==hi)return emptyList()
    val mean=data.sumOf {it/data.size}
    val sd=sqrt(data.sumOf {(it-mean).pow(2)/(data.size-1)})
    val bandwidth=max(sd*data.size.toDouble().pow(-.2),(hi-lo)/1000)
    val samples=List(97) {index->
        val fraction=index/96.0;val at=lo*(1-fraction)+hi*fraction
        at*scale to data.sumOf {exp(-.5*((at-it)/bandwidth).pow(2))}
    }
    val peak=samples.maxOf {it.second}
    return samples.map {it.first to it.second/peak}
}

internal data class StatisticsBeeswarm(val radius:Double,val offsets:List<Double>)

internal data class StatisticsRaincloudSummary(val low:Double,val q1:Double,val median:Double,val q3:Double,val high:Double)

/** Quartiles with Tukey whiskers; outliers remain visible in the raw-point strip. */
internal fun raincloudSummary(values:List<Double>):StatisticsRaincloudSummary? {
    val sorted=values.filter(Double::isFinite).sorted()
    if(sorted.isEmpty())return null
    fun q(p:Double):Double {val at=(sorted.size-1)*p;val lo=floor(at).toInt();val hi=ceil(at).toInt();val f=at-lo;return sorted[lo]*(1-f)+sorted[hi]*f}
    val q1=q(.25);val median=q(.5);val q3=q(.75)
    val scale=max(abs(sorted.first()),abs(sorted.last())).takeIf {it>0} ?: 1.0
    val iqr=q3/scale-q1/scale
    return StatisticsRaincloudSummary(sorted.first {it/scale>=q1/scale-1.5*iqr},q1,median,q3,sorted.last {it/scale<=q3/scale+1.5*iqr})
}

/** Pack circles along the category axis without changing the value coordinates. */
internal fun beeswarmLayout(axisPositions:List<Double>,preferredRadius:Double,halfWidth:Double):StatisticsBeeswarm {
    if(axisPositions.isEmpty())return StatisticsBeeswarm(preferredRadius,emptyList())
    val order=axisPositions.indices.sortedWith(compareBy<Int> {axisPositions[it]}.thenBy {it})
    var duplicates=1;var run=1
    for(i in 1 until order.size) {
        run=if(axisPositions[order[i]]==axisPositions[order[i-1]])run+1 else 1
        duplicates=max(duplicates,run)
    }
    var radius=min(preferredRadius,halfWidth/(1+ceil((duplicates-1)/2.0)*2.15))
    fun pack(radius:Double):List<Double>? {
        val spacing=radius*2.15;val offsets=MutableList(axisPositions.size){0.0};val placed=mutableListOf<Pair<Double,Double>>()
        var first=0;var i=0
        while(i<order.size) {
            val axis=axisPositions[order[i]]
            while(first<placed.size&&axis-placed[first].first>=spacing)first++
            if(first==placed.size) {
                var end=i+1;while(end<order.size&&axisPositions[order[end]]==axis)end++
                for(j in i until end) {
                    val rank=j-i;val offset=if(rank==0)0.0 else ceil(rank/2.0)*spacing*(if(rank%2==1)1 else -1)
                    if(abs(offset)+radius>halfWidth+1e-9)return null
                    offsets[order[j]]=offset;placed.add(axis to offset)
                }
                i=end;continue
            }
            val intervals=(first until placed.size).map {index->
                val (otherAxis,otherOffset)=placed[index];val distance=axis-otherAxis
                val reach=sqrt(max(0.0,spacing*spacing-distance*distance))
                (otherOffset-reach) to (otherOffset+reach)
            }.sortedBy {it.first}
            val merged=mutableListOf<Pair<Double,Double>>()
            intervals.forEach {interval->
                val last=merged.lastOrNull()
                if(last!=null&&interval.first<last.second)merged[merged.lastIndex]=last.first to max(last.second,interval.second) else merged.add(interval)
            }
            val blocked=merged.firstOrNull {it.first<0&&it.second>0}
            val offset=when {
                blocked==null->0.0
                abs(blocked.first)<blocked.second->blocked.first
                abs(blocked.first)>blocked.second->blocked.second
                i%2==1->blocked.second
                else->blocked.first
            }
            if(abs(offset)+radius>halfWidth+1e-9)return null
            offsets[order[i]]=offset;placed.add(axis to offset);i++
        }
        return offsets
    }
    var offsets=pack(radius)
    while(offsets==null){radius*=.8;offsets=pack(radius)}
    return StatisticsBeeswarm(radius,offsets)
}

internal data class StatisticsHeatMapRow(val label:String,val values:List<Double?>,val counts:List<Int>?=null)
internal data class StatisticsHeatMapData(val columns:List<String>,val rows:List<StatisticsHeatMapRow>,val correlation:Boolean=false,val clustered:Boolean=false,val rowLinks:List<StatisticsClusterLink> = emptyList(),val columnLinks:List<StatisticsClusterLink> = emptyList(),val mode:String="raw",val correlationMethod:String="pearson")
internal fun statisticsPlotNumber(value:String?)=value?.statisticsNumericCell()?.toDoubleOrNull()?.takeIf(Double::isFinite)

internal fun statisticsHeatMapData(rows:List<List<String>>,kind:String,grouping:String="columns",mode:String="raw",columnNames:List<String> = statisticsColumnNames(kind)):StatisticsHeatMapData {
    val names=statisticsColumnNames(kind)
    val groupColumn=statisticsPlotGroupingColumn(grouping,names.size)
    val indices=names.indices.filter {it!=groupColumn}
    val values=rows.map {row->indices.map {statisticsPlotNumber(row.getOrNull(it))}.toMutableList()}.toMutableList()
    when(mode) {
        "zrow"->values.forEach(::standardizeHeatMapValues)
        "zcolumn"->indices.indices.forEach {column->
            val standardized=values.map {it[column]}.toMutableList();standardizeHeatMapValues(standardized)
            standardized.forEachIndexed {row,value->values[row][column]=value}
        }
    }
    return StatisticsHeatMapData(indices.map {columnNames.getOrNull(it)?.takeIf(String::isNotBlank) ?: names[it]},rows.mapIndexed {index,row->
        StatisticsHeatMapRow(if(groupColumn<0)(index+1).toString() else row.getOrNull(groupColumn)?.trim().orEmpty().ifBlank {(index+1).toString()},values[index])
    },mode=mode)
}

private fun standardizeHeatMapValues(values:MutableList<Double?>) {
    val finite=values.mapIndexedNotNull {index,value->value?.let {index to it}}
    if(finite.isEmpty())return
    val scale=finite.maxOf {abs(it.second)}.takeIf {it>0} ?: 1.0
    val mean=finite.sumOf {it.second/scale/finite.size}
    val deviation=sqrt(finite.sumOf {(it.second/scale-mean).pow(2)/finite.size})
    finite.forEach {(index,value)->values[index]=if(deviation==0.0)0.0 else (value/scale-mean)/deviation}
}

internal fun statisticsCorrelationHeatMap(rows:List<List<String>>,kind:String,method:String="pearson",xColumns:List<Int>?=null,yColumns:List<Int>?=null,columnNames:List<String> = statisticsColumnNames(kind)):StatisticsHeatMapData {
    val defaults=statisticsColumnNames(kind)
    val usable=defaults.indices.filter {column->rows.any {statisticsPlotNumber(it.getOrNull(column))!=null}}
    val x=(xColumns?:usable).filter(usable::contains);val y=(yColumns?:usable).filter(usable::contains)
    val cells=y.map {yi->x.map {xi->
        val pairs=rows.mapNotNull {row->val a=statisticsPlotNumber(row.getOrNull(xi));val b=statisticsPlotNumber(row.getOrNull(yi));if(a==null||b==null)null else a to b}
        correlationCoefficient(pairs,method) to pairs.size
    }}
    return StatisticsHeatMapData(x.map {columnNames.getOrNull(it)?.takeIf(String::isNotBlank) ?: defaults[it]},y.mapIndexed {index,column->
        StatisticsHeatMapRow(columnNames.getOrNull(column)?.takeIf(String::isNotBlank) ?: defaults[column],cells[index].map {it.first},cells[index].map {it.second})
    },correlation=true,mode="correlation",correlationMethod=method)
}

private fun correlationCoefficient(source:List<Pair<Double,Double>>,method:String):Double? {
    if(source.size<2)return null
    val pairs=when(method) {"spearman"->rankPairs(source);"kendall"->return kendallTauB(source);else->source}
    val x=pairs.map {it.first};val y=pairs.map {it.second}
    if(x.all {it==x.first()}||y.all {it==y.first()})return null
    val sx=x.maxOf {abs(it)}.takeIf {it>0} ?: 1.0;val sy=y.maxOf {abs(it)}.takeIf {it>0} ?: 1.0
    val mx=x.sumOf {it/sx/x.size};val my=y.sumOf {it/sy/y.size}
    var xx=0.0;var yy=0.0;var xy=0.0
    pairs.forEach {(a,b)->val dx=a/sx-mx;val dy=b/sy-my;xx+=dx*dx;yy+=dy*dy;xy+=dx*dy}
    return if(xx>0&&yy>0)(xy/sqrt(xx*yy)).coerceIn(-1.0,1.0) else null
}

private fun rankPairs(pairs:List<Pair<Double,Double>>):List<Pair<Double,Double>> {
    val ranks=Array(pairs.size){DoubleArray(2)}
    for(axis in 0..1) {
        val ordered=pairs.indices.sortedWith(compareBy<Int> {if(axis==0)pairs[it].first else pairs[it].second}.thenBy {it})
        var start=0
        while(start<ordered.size) {
            val first=if(axis==0)pairs[ordered[start]].first else pairs[ordered[start]].second
            var end=start+1
            while(end<ordered.size&&(if(axis==0)pairs[ordered[end]].first else pairs[ordered[end]].second)==first)end++
            val averageRank=(start+1+end)/2.0
            for(index in start until end)ranks[ordered[index]][axis]=averageRank
            start=end
        }
    }
    return ranks.map {it[0] to it[1]}
}

private fun kendallTauB(pairs:List<Pair<Double,Double>>):Double? {
    val n=pairs.size;val total=n.toDouble()*(n-1)/2.0
    fun ties(axis:Int)=pairs.groupingBy {if(axis==0)it.first else it.second}.eachCount().values.sumOf {it.toDouble()*(it-1)/2.0}
    val tiesX=ties(0);val tiesY=ties(1);val sortedY=pairs.map {it.second}.distinct().sorted();val ranks=sortedY.withIndex().associate {(index,value)->value to index+1}
    val tree=DoubleArray(sortedY.size+1)
    fun query(index:Int):Double {var i=index;var sum=0.0;while(i>0){sum+=tree[i];i-=i and -i};return sum}
    fun add(index:Int){var i=index;while(i<tree.size){tree[i]++;i+=i and -i}}
    val sorted=pairs.sortedWith(compareBy<Pair<Double,Double>> {it.first}.thenBy {it.second});var previous=0.0;var score=0.0;var start=0
    while(start<sorted.size) {
        var end=start+1;while(end<sorted.size&&sorted[end].first==sorted[start].first)end++
        for(index in start until end){val rank=ranks.getValue(sorted[index].second);score+=query(rank-1)-(previous-query(rank))}
        for(index in start until end){add(ranks.getValue(sorted[index].second));previous++}
        start=end
    }
    val denominator=sqrt((total-tiesX)*(total-tiesY))
    return if(denominator>0)(score/denominator).coerceIn(-1.0,1.0) else null
}

internal fun heatMapFraction(value:Double,minimum:Double,maximum:Double):Double {
    if(minimum==maximum)return .5
    val scale=max(abs(minimum),abs(maximum)).takeIf {it>0} ?: 1.0
    return ((value/scale-minimum/scale)/(maximum/scale-minimum/scale)).coerceIn(0.0,1.0)
}
