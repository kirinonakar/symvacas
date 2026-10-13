package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.math.Editor
import com.kirinonakar.symvacas.math.Parser
import com.kirinonakar.symvacas.math.LatexInput
import java.time.LocalDate
import java.time.temporal.ChronoUnit

internal fun statisticsColumnCount(kind:String):Int = when(kind) {
    "list"->1;"xy"->2;"xyz"->3
    else->kind.removePrefix("columns:").toIntOrNull()?.coerceIn(1,100) ?: 1
}
internal fun statisticsColumnNames(kind:String):List<String> = List(statisticsColumnCount(kind)) {listOf("x","y","z").getOrNull(it) ?: "x${it+1}"}
internal fun statisticsColumnLabels(csv:String,kind:String):List<String> {
    val names=statisticsColumnNames(kind)
    val raw=csv.removePrefix("\uFEFF").replace("\r\n","\n").replace('\r','\n').split('\n').map {it.splitCsvRecord()}
    if(!statisticsHasHeader(raw))return names
    return names.mapIndexed {index,name->raw.first().getOrNull(index)?.trim()?.takeIf {it.isNotBlank()&&it!=name}?.let {"$it ($name)"} ?: name}
}
internal fun statisticsHeatMapColumnNames(csv:String,kind:String):List<String> {
    val names=statisticsColumnNames(kind)
    val raw=csv.removePrefix("\uFEFF").replace("\r\n","\n").replace('\r','\n').split('\n').map {it.splitCsvRecord()}
    if(!statisticsHasHeader(raw))return names
    return names.mapIndexed {index,name->raw.firstOrNull()?.getOrNull(index)?.trim()?.takeIf(String::isNotBlank) ?: name}
}

/** Table editor column headers: a detected header name keeps the column name used by the analysis. */
internal fun statisticsTableColumnLabels(csv:String,kind:String):List<String> {
    val names=if(kind=="list")listOf("value") else statisticsColumnNames(kind)
    val rows=statisticsCsvRows(csv)
    if(!statisticsHasHeader(rows))return names
    return names.mapIndexed {index,name->rows.first().getOrNull(index)?.trim()?.takeIf {it.isNotBlank()&&it!=name}?.let {"$it ($name)"} ?: name}
}
internal fun statisticsKindForColumns(count:Int):String = when(count) {1->"list";2->"xy";3->"xyz";else->"columns:${count.coerceIn(1,100)}"}
internal fun nextStatisticsDatasetName(names:List<String>,currentName:String):String {
    val existing=(names+currentName).toSet()
    var index=1L
    existing.forEach {name->Regex("D([0-9]+)").matchEntire(name)?.groupValues?.get(1)?.toLongOrNull()?.let {number->if(number>=index&&number<Long.MAX_VALUE)index=number+1}}
    while("D$index" in existing)index++
    return "D$index"
}
internal fun newStatisticsDatasetName(requestedName:String,names:List<String>,currentName:String):String {
    val name=requestedName.trim().ifBlank {nextStatisticsDatasetName(names,currentName)}
    require(name.matches(Regex("[A-Za-z][A-Za-z0-9_]*"))) {"Use a letter followed by letters, digits or underscores for the dataset name"}
    require(name !in names) {"Dataset name already exists; choose another name"}
    return name
}
/** n-column selections with one, two, or three columns are handled as List, x,y, and x,y,z data. */
internal fun statisticsEffectiveKind(selectedKind:String,columnCount:Int):String =
    if(selectedKind.startsWith("columns:"))statisticsKindForColumns(columnCount) else selectedKind
internal fun statisticsDetectedColumns(source:String):Int {
    if(source.isBlank())return 1
    val count=source.removePrefix("\uFEFF").replace("\r\n","\n").replace('\r','\n').lineSequence().map {it.splitCsvRecord().size}.maxOrNull() ?: 1
    require(count<=100) {"Column count must be between 1 and 100"}
    return count.coerceAtLeast(1)
}

/** Group labels stay categorical, including numeric and date labels. */
internal fun statisticsPlotGroupingColumn(grouping:String,count:Int):Int = when(grouping){"first"->0;"last"->count-1;else->grouping.removePrefix("column:").toIntOrNull() ?: -1}.takeIf {count>1&&it in 0 until count} ?: -1

internal fun statisticsPlotSeries(rows:List<List<String>>,kind:String,grouping:String="columns",columnNames:List<String> = statisticsColumnNames(kind)):List<Pair<String,List<Double>>> {
    val names=columnNames
    fun number(value:String?)=value?.statisticsNumericCell()?.toDoubleOrNull()?.takeIf(Double::isFinite)
    if(statisticsPlotGroupingColumn(grouping,names.size)<0) {
        val numeric=statisticsNumericRows(rows,if(names.size>1)statisticsDateAxis(rows) else null)
        return names.mapIndexed {index,name->(if(names.size==1)"" else name) to numeric.mapNotNull {number(it.getOrNull(index))}}
    }
    val groupColumn=statisticsPlotGroupingColumn(grouping,names.size)
    val groups=linkedMapOf<String,List<MutableList<Double>>>()
    rows.forEach {row->
        val group=row.getOrNull(groupColumn)?.trim().orEmpty()
        if(group.isNotEmpty()) {
            val samples=groups.getOrPut(group){List(names.size){mutableListOf()}}
            names.indices.filter {it!=groupColumn}.forEach {index->number(row.getOrNull(index))?.let {samples[index].add(it)}}
        }
    }
    return groups.flatMap {(group,samples)->names.indices.filter {it!=groupColumn}.map {index->
        (if(names.size==2)group else "$group · ${names[index]}") to samples[index].toList()
    }}
}

internal data class StatisticsPlotPanel(val label:String,val series:List<Pair<String,List<Double>>>)
internal fun statisticsPlotPanels(rows:List<List<String>>,kind:String,grouping:String,columnNames:List<String> = statisticsColumnNames(kind)):List<StatisticsPlotPanel> {
    val names=columnNames
    if(statisticsPlotGroupingColumn(grouping,names.size)<0)return listOf(StatisticsPlotPanel("",statisticsPlotSeries(rows,kind,columnNames=names)))
    val groupColumn=statisticsPlotGroupingColumn(grouping,names.size)
    return names.indices.filter {it!=groupColumn&&rows.any {row->statisticsPlotNumber(row.getOrNull(it))!=null}}.map {column->
        val pairs=rows.map {row->listOf(row.getOrNull(groupColumn).orEmpty(),row.getOrNull(column).orEmpty())}
        StatisticsPlotPanel(names[column],statisticsPlotSeries(pairs,"xy","first"))
    }
}

internal fun statisticsRows(csv:String):List<List<String>> {
    val rows=statisticsCsvRows(csv)
    return if(statisticsHasHeader(rows))rows.drop(1) else rows
}

/** Every stored row, a detected header included, so table column edits keep header labels with their column. */
internal fun statisticsCsvRows(csv:String):List<List<String>> {
    val normalized=csv.removePrefix("\uFEFF").replace("\r\n","\n").replace('\r','\n')
    val lines=mutableListOf<String>();var start=0
    normalized.forEachIndexed {index,char->if(char=='\n'){lines+=normalized.substring(start,index);start=index+1}}
    lines+=normalized.substring(start)
    return lines.map {it.splitCsvRecord().map(String::trim)}
}

internal fun statisticsRemoveColumn(csv:String,column:Int):String {
    val rows=statisticsCsvRows(csv)
    val updated=rows.map {row->if(column in row.indices)row.filterIndexed {index,_->index!=column} else row}
    if(statisticsHasHeader(rows))registerStatisticsHeader(updated)
    return updated.joinToString("\n",transform=::statisticsCsvLine)
}

internal data class StatisticsColumnAddition(val csv:String,val kind:String)
internal fun statisticsAddColumn(csv:String,columnCount:Int):StatisticsColumnAddition {
    val rows=statisticsCsvRows(csv)
    val count=maxOf(columnCount,rows.maxOfOrNull {it.size} ?: 1)
    require(count in 1 until 100) {"Column count must be between 1 and 100"}
    val kind=statisticsKindForColumns(count+1)
    val header=statisticsHasHeader(rows)
    val name=statisticsColumnNames(kind).last()
    val updated=rows.mapIndexed {index,row->List(count){row.getOrElse(it){""}}+if(index==0&&header)name else ""}
    if(header)registerStatisticsHeader(updated)
    return StatisticsColumnAddition(updated.joinToString("\n",transform=::statisticsCsvLine),kind)
}

internal fun statisticsRenameColumn(csv:String,columnCount:Int,column:Int,header:String):String {
    require(column in 0 until columnCount) {"Choose valid data columns"}
    val name=header.trim();require(name.isNotBlank()) {"Enter a new column header"}
    val raw=statisticsCsvRows(csv);val width=maxOf(columnCount,raw.maxOfOrNull {it.size} ?: 1)
    val hasHeader=statisticsHasHeader(raw);val aliases=statisticsColumnNames(statisticsKindForColumns(width))
    val names=if(hasHeader)List(width){raw.first().getOrElse(it){""}.ifBlank {aliases[it]}} else aliases
    require(names.indices.none {it!=column&&names[it].equals(name,ignoreCase=true)}) {"New column header already exists"}
    val updatedNames=names.toMutableList().apply {this[column]=name}
    require(statisticsHasHeader(listOf(listOf(name),listOf("1")))) {"Use a text column header"}
    val rows=(if(hasHeader)raw.drop(1) else raw).map {row->List(width){row.getOrElse(it){""}}}
    registerStatisticsHeader(listOf(updatedNames)+rows)
    return (listOf(updatedNames)+rows.ifEmpty {listOf(List(width){""})}).joinToString("\n") {row->if(row.size==1&&row[0].isBlank())"\"\"" else statisticsCsvLine(row)}
}

internal fun statisticsMoveColumn(csv:String,column:Int,delta:Int):String {
    val rows=statisticsCsvRows(csv)
    val updated=rows.map {row->
        val target=column+delta
        if(column !in row.indices||target !in row.indices)row
        else row.toMutableList().apply {val value=this[column];this[column]=this[target];this[target]=value}
    }
    if(statisticsHasHeader(rows))registerStatisticsHeader(updated)
    return updated.joinToString("\n",transform=::statisticsCsvLine)
}

/** Rewrites the table editor's data rows while a detected header row stays above them. */
internal fun statisticsReplaceDataRows(csv:String,rows:List<List<String>>):String {
    val stored=statisticsCsvRows(csv)
    val headerCount=if(statisticsHasHeader(stored))1 else 0
    if(headerCount==1)registerStatisticsHeader(stored.take(1)+rows)
    return (stored.take(headerCount)+rows).joinToString("\n",transform=::statisticsCsvLine)
}
internal data class StatisticsCsvImport(val rows:List<List<String>>,val hasHeader:Boolean,val columnCount:Int) {
    val labels:List<String> get()=(0 until columnCount).map {index->
        val header=if(hasHeader)rows.firstOrNull()?.getOrNull(index)?.trim().orEmpty() else ""
        val alias=statisticsColumnNames(statisticsKindForColumns(columnCount))[index]
        if(header.isBlank()||header==alias)alias else "$header ($alias)"
    }
}

internal fun previewStatisticsCsv(csv:String):StatisticsCsvImport {
    val rows=statisticsImportRows(csv.replace("\r\n","\n").replace('\r','\n').removePrefix("\uFEFF")
        .lineSequence().filter(String::isNotBlank).map {it.splitCsvRecord()}.toList())
    return StatisticsCsvImport(rows,statisticsHasHeader(rows),rows.maxOfOrNull(List<String>::size)?:0)
}

internal fun importStatisticsCsv(preview:StatisticsCsvImport,columns:List<Int>,skipHeader:Boolean):String {
    require(columns.isNotEmpty()&&columns.size<=100&&columns.distinct().size==columns.size)
    require(columns.all {it in 0 until preview.columnCount})
    val rows=statisticsImportRows(preview.rows)
    val body=rows.drop(if(skipHeader)1 else 0)
    val keptHeader=if(skipHeader)rows.take(1)+body else body
    val selected=keptHeader.map {row->columns.map {index->row.getOrNull(index).orEmpty()}}
    if(skipHeader)registerStatisticsHeader(selected)
    return selected.joinToString("\n",transform=::statisticsCsvLine)
}

private fun markdownStatisticsCells(line:String):List<String> {
    var body=line.trim()
    if(body.startsWith('|'))body=body.drop(1)
    if(body.endsWith('|')&&!body.endsWith("\\|"))body=body.dropLast(1)
    val cells=mutableListOf<String>();val cell=StringBuilder();var index=0
    while(index<body.length) {
        val char=body[index]
        if(char=='\\'&&body.getOrNull(index+1)=='|'){cell.append('|');index++}
        else if(char=='|'){cells+=cell.toString().trim();cell.setLength(0)}
        else cell.append(char)
        index++
    }
    cells+=cell.toString().trim();return cells
}

internal fun statisticsMarkdownTableCsv(source:String):String? {
    val lines=source.removePrefix("\uFEFF").trim().split(Regex("\\r\\n|\\n|\\r")).filter {it.isNotBlank()}.toMutableList()
    if(lines.firstOrNull()?.startsWith("```")==true&&lines.lastOrNull()?.startsWith("```")==true){lines.removeAt(lines.lastIndex);lines.removeAt(0)}
    if(lines.size<2||lines.any {!it.contains('|')})return null
    val header=markdownStatisticsCells(lines[0]);val divider=markdownStatisticsCells(lines[1])
    if(header.isEmpty()||divider.size!=header.size||divider.any {!it.matches(Regex(":?-{3,}:?"))})return null
    val rows=listOf(header)+lines.drop(2).map(::markdownStatisticsCells)
    if(rows.drop(1).any {it.size>header.size})return null
    return rows.joinToString("\n") {row->(0 until header.size).joinToString(",") {index->(row.getOrNull(index).orEmpty()).csvCell()}}
}

/** Normalize only a bulk insertion, leaving ordinary typing and CSV separators alone. */
internal fun normalizeStatisticsPaste(previous:String,updated:String,singleColumn:Boolean=false,cell:Boolean=false,selectionStart:Int?=null,selectionEnd:Int?=null):String? {
    var prefix=0
    while(prefix<previous.length&&prefix<updated.length&&previous[prefix]==updated[prefix])prefix++
    var suffix=0
    while(suffix<previous.length-prefix&&suffix<updated.length-prefix&&previous[previous.lastIndex-suffix]==updated[updated.lastIndex-suffix])suffix++
    // The actual selection identifies the full pasted value even when it shares digits with the old value.
    if(selectionStart!=null&&selectionEnd!=null&&selectionStart in 0..previous.length&&selectionEnd in selectionStart..previous.length) {
        val trailing=previous.length-selectionEnd
        if(updated.length>=selectionStart+trailing&&updated.startsWith(previous.take(selectionStart))&&updated.endsWith(previous.takeLast(trailing))) {
            prefix=selectionStart;suffix=trailing
        }
    }
    val inserted=updated.substring(prefix,updated.length-suffix)
    if(inserted.length<=1)return null
    val converted=if(cell)statisticsPasteCell(inserted) else statisticsPasteText(inserted,singleColumn)
    val candidate=updated.substring(0,prefix)+converted+updated.substring(updated.length-suffix)
    return candidate.takeIf {it!=updated}
}

internal fun statisticsPasteCell(raw:String):String=statisticsNumericPasteCell(statisticsPasteDataLines(raw))

private val statisticsMarkdownHeading=Regex("^#{1,6} ")
private fun statisticsPasteDataLines(source:String):String {
    // Omit blank lines and unindented Markdown headings, preserving quoted CSV values.
    val result=StringBuilder();var quoted=false;var start=0;var separator="";var hasLine=false
    while(start<source.length) {
        var end=start
        while(end<source.length&&source[end]!='\r'&&source[end]!='\n')end++
        val line=source.substring(start,end)
        var next=end
        if(next<source.length){next++;if(source[end]=='\r'&&source.getOrNull(next)=='\n')next++}
        val content=line.removePrefix("\uFEFF")
        if(quoted||content.isNotBlank()&&!statisticsMarkdownHeading.containsMatchIn(content)) {
            if(hasLine)result.append(separator)
            result.append(line);hasLine=true;separator=source.substring(end,next)
            line.forEach {if(it=='"')quoted=!quoted}
        }
        start=next
    }
    return result.toString()
}

private fun statisticsNumericPasteCell(raw:String):String {
    val trimmed=raw.trim();val quoted=trimmed.startsWith('"')&&trimmed.endsWith('"')&&trimmed.length>=2
    val value=if(quoted)trimmed.substring(1,trimmed.length-1) else trimmed
    val number=value.statisticsNumericCell()
    if(quoted&&number.matches(Regex("^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$")))return raw.replace(trimmed,number)
    return if(number!=value.trim())raw.replace(",","") else raw
}

private fun statisticsPasteDelimiter(source:String,start:Int):Char {
    var quoted=false
    for(index in start until source.length) {
        val ch=source[index]
        if(ch=='"')quoted=!quoted
        else if(!quoted){if(ch=='\t')return '\t';if(ch=='\n'||ch=='\r')break}
    }
    return ','
}

private fun statisticsSpreadsheetCsv(source:String):String? {
    if(!source.contains('\t'))return null
    val result=StringBuilder();val cell=StringBuilder();var quoted=false;var hasTab=false;var index=0
    fun appendCell() {
        val value=cell.toString();val number=value.statisticsNumericCell()
        result.append((if(number!=value.trim())value.replace(",","") else value).csvCell());cell.setLength(0)
    }
    while(index<source.length) {
        val ch=source[index]
        if(ch=='"') {
            if(quoted&&source.getOrNull(index+1)=='"'){cell.append('"');index++}else quoted=!quoted
        }else if(!quoted&&ch=='\t') {
            hasTab=true;appendCell();result.append(',')
        }else if(!quoted&&(ch=='\n'||ch=='\r')) {
            appendCell();result.append(ch)
            if(ch=='\r'&&source.getOrNull(index+1)=='\n'){result.append('\n');index++}
        }else cell.append(ch)
        index++
    }
    appendCell();return result.toString().takeIf {hasTab&&!quoted}
}

internal fun statisticsPasteText(source:String,singleColumn:Boolean=false):String {
    val filtered=statisticsPasteDataLines(source)
    val markdown=statisticsMarkdownTableCsv(filtered)
    if(markdown==null)statisticsSpreadsheetCsv(filtered)?.let {return it}
    val text=markdown?:filtered
    val lines=text.split(Regex("\r\n|\n|\r"))
    // In List mode a pasted spreadsheet column can contain unquoted grouped numbers.
    val groupedColumn=markdown==null&&singleColumn&&!text.contains('\t')&&lines.any {groupedStatisticNumber.matches(it.trim())}&&
        lines.all {!it.contains(',')||groupedStatisticNumber.matches(it.trim())}
    if(groupedColumn)return Regex("[^\r\n]+").replace(text) {match->
        if(groupedStatisticNumber.matches(match.value.trim()))match.value.replace(",","") else match.value
    }
    val result=StringBuilder();var start=0;var quoted=false;var delimiter=statisticsPasteDelimiter(text,0)
    fun appendCell(end:Int) {
        result.append(statisticsNumericPasteCell(text.substring(start,end)))
    }
    text.forEachIndexed {index,ch->
        if(ch=='"')quoted=!quoted
        if(!quoted&&(ch==delimiter||ch=='\n'||ch=='\r')) {
            appendCell(index);result.append(ch);start=index+1
            if(ch=='\n'||ch=='\r')delimiter=statisticsPasteDelimiter(text,index+1)
        }
    }
    appendCell(text.length);return result.toString()
}

internal fun statisticsCsvLine(cells:List<String>):String=cells.joinToString(",") {it.csvCell()}

private fun String.csvCell():String=if(any {it==','||it=='"'||it=='\n'||it=='\r'||it=='\t'})"\"${replace("\"","\"\"")}\"" else this

private val groupedStatisticNumber=Regex("^[+-]?\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?$")
internal fun String.statisticsNumericCell():String=if(groupedStatisticNumber.matches(trim()))trim().replace(",","") else trim()

internal fun statisticsImportRows(rows:List<List<String>>):List<List<String>> {
    val hasHeader=statisticsHasHeader(rows)
    return rows.mapIndexed {index,row->if(index==0&&hasHeader)row else row.map(String::statisticsNumericCell)}
}

internal fun statisticsNumericRows(rows:List<List<String>>,dateAxis:StatisticsDateAxis?=null):List<List<String>> =
    (dateAxis?.numericRows(rows)?:rows).map {row->row.map(String::statisticsNumericCell)}

internal data class StatisticsSummaryPlan(val source:String,val termLabels:Map<String,String>)
internal fun statisticsSummaryPlan(source:String,kind:String,column:Int=0):StatisticsSummaryPlan {
    val rows=statisticsRows(source)
    val numeric=statisticsNumericRows(rows,if(statisticsColumnCount(kind)>1)statisticsDateAxis(rows) else null)
    val values=numeric.mapNotNull {it.getOrNull(column)?.takeIf(String::isNotBlank)}
    require(values.isNotEmpty()) {"Enter at least one data value"}
    val label=statisticsColumnLabels(source,kind)[column]
    val constants=setOf("pi","π","e","E","tau","τ","∞")
    val isNumeric=values.all {value->runCatching {Parser(LatexInput.convert(value)?:value).parse().nodes().none {it.kind=="symbol"&&it.value !in constants}}.getOrDefault(false)}
    if(isNumeric)return StatisticsSummaryPlan(values.joinToString(",","stats([","])"),mapOf("sample:1" to label))
    val categories=rows.mapNotNull {it.getOrNull(column)?.takeIf(String::isNotBlank)}
    val labels=categories.distinct();val indices=labels.withIndex().associate {it.value to it.index}
    return StatisticsSummaryPlan(categories.joinToString(",","stats([","],categorical)"){indices.getValue(it).toString()},
        mapOf("sample:1" to label)+labels.mapIndexed {index,value->"summary:category:$index" to value})
}

internal data class StatisticsDateAxis(val origin:LocalDate) {
    fun x(value:String):String?=parseStatisticsDate(value)?.let {ChronoUnit.DAYS.between(origin,it).toString()}
    fun numericRows(rows:List<List<String>>):List<List<String>> = rows.map {row->
        if(row.isEmpty())row else listOf(x(row[0]).orEmpty())+row.drop(1)
    }
}

internal fun statisticsDateAxis(rows:List<List<String>>):StatisticsDateAxis? {
    val xValues=rows.mapNotNull {it.firstOrNull()?.takeIf(String::isNotBlank)}
    val dates=xValues.mapNotNull(::parseStatisticsDate)
    val numericCount=xValues.count {it.statisticsNumericCell().toDoubleOrNull()!=null}
    if(dates.isEmpty()||dates.size<numericCount)return null
    return StatisticsDateAxis(dates.min().minusDays(1))
}

internal fun parseStatisticsDate(value:String):LocalDate? {
    val match=Regex("^(\\d{4})([-/.])(\\d{1,2})\\2(\\d{1,2})$").matchEntire(value.trim())?:return null
    return runCatching {LocalDate.of(match.groupValues[1].toInt(),match.groupValues[3].toInt(),match.groupValues[4].toInt())}.getOrNull()
}

internal fun statisticsHasHeader(rows:List<List<String>>):Boolean {
    if(hasExplicitStatisticsHeader(rows))return true
    val first=rows.firstOrNull() ?: return false
    if(first.none(String::isNotBlank))return false
    if(statisticsHeader(first))return true
    fun dataCell(value:String):Boolean {
        if(value.isBlank())return false
        if(value.statisticsNumericCell().toDoubleOrNull()?.isFinite()==true||value in listOf("pi","π","e","E","tau","τ","∞")||
            value.matches(Regex("(?i)(NaN|[+-]?Infinity)"))||parseStatisticsDate(value)!=null)return true
        if(value.matches(Regex("[\\p{L}_][\\p{L}\\p{N}_]*(?:\\s+[\\p{L}_][\\p{L}\\p{N}_]*)*")))return false
        // Column names may carry a parenthesized unit (e.g. 자산(만원)); numeric calls such as sqrt(2) stay data.
        if(value.matches(Regex("[\\p{L}_][\\p{L}\\p{N}_]*(?:\\s+[\\p{L}_][\\p{L}\\p{N}_]*)*\\s*\\([^()]*[\\p{L}%][^()]*\\)")))return false
        return runCatching {Parser(value).parse().kind!="symbol"}.getOrDefault(false)
    }
    return first.all(String::isNotBlank)&&first.none(::dataCell)&&(rows.drop(1).any {row->row.size==first.size&&row.any(::dataCell)}||rows.size>1&&rows.drop(1).all {row->row.all(String::isBlank)})
}

private fun statisticsHeader(row:List<String>):Boolean {
    val cells=row.map(String::lowercase)
    return when(cells.size) {
        1->cells[0] in listOf("x","n","value","y")
        2->cells==listOf("x","y")||cells==listOf("group","value")||cells==listOf("date","value")||cells==listOf("date","y")
        else->cells.take(3)==listOf("x","y","z")
    }
}

internal fun statisticsDataSource(csv:String,kind:String):String {
    val rawRows=statisticsRows(csv)
    val rows=statisticsNumericRows(rawRows,if(statisticsColumnCount(kind)>1)statisticsDateAxis(rawRows) else null)
    val columns=statisticsColumnCount(kind)
    return if(columns>1)rows.filter {row->(0 until columns).all {index->row.getOrNull(index)?.isNotBlank()==true}}
        .joinToString(",","[","]") {row->row.take(columns).joinToString(",","[","]")}
    else rows.mapNotNull {it.getOrNull(0)?.takeIf(String::isNotBlank)}.joinToString(",","[","]")
}

internal fun statisticsRecallSource(editor:Editor,csv:String,kind:String,committed:Boolean=false):String {
    val literal=statisticsDataSource(csv,kind)
    if(kind!="xy"||committed||literal=="[]"||editor.cursor!=editor.anchor)return literal
    val caret=editor.cursor
    if(editor.source.getOrNull(caret-1)!='['||editor.source.getOrNull(caret)!=']')return literal
    val regressionList=editor.tree()?.nodes()?.any {node->
        node.kind=="call"&&node.value=="regression"&&node.args.firstOrNull()?.let {arg->
            arg.kind=="list"&&arg.start==caret-1&&arg.end==caret+1
        }==true
    }==true
    return if(regressionList)literal.substring(1,literal.length-1) else literal
}

internal fun String.splitCsvRecord():List<String> {
    // Excel separates columns with tabs; commas inside those cells are literal.
    var inQuotes=false
    val delimiter=if(any {ch->
        if(ch=='"')inQuotes=!inQuotes
        ch=='\t'&&!inQuotes
    })'\t' else ','
    val cells=mutableListOf<String>();val current=StringBuilder();var quoted=false;var i=0
    while(i<length) {
        val ch=this[i]
        when {
            ch=='"'&&quoted&&i+1<length&&this[i+1]=='"'->{current.append('"');i++}
            ch=='"'->quoted=!quoted
            ch==delimiter&&!quoted->{cells+=current.toString().trim();current.setLength(0)}
            else->current.append(ch)
        }
        i++
    }
    cells+=current.toString().trim();return cells
}
