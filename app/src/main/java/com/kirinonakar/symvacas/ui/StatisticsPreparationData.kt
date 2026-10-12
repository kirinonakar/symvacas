package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.math.Expr
import com.kirinonakar.symvacas.math.Parser
import org.json.JSONArray
import kotlin.math.*

internal data class StatisticsPreparationDataset(val headers:List<String>,val rows:List<List<String>>)
internal data class StatisticsPreparationResult(val csv:String,val kind:String,val headers:List<String>,val rows:List<List<String>>,val changed:Int,val omitted:Int=0)
private val preparationNumber=Regex("^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
private val preparationIdentifier=Regex("^[\\p{L}][\\p{L}\\p{N}_]*$")
internal fun preparationDataset(source:String,kind:String):StatisticsPreparationDataset {
    val raw=statisticsCsvRows(source);val width=maxOf(statisticsColumnCount(kind),raw.maxOfOrNull {it.size} ?: 1)
    val header=statisticsHasHeader(raw);val aliases=statisticsColumnNames(statisticsKindForColumns(width))
    return StatisticsPreparationDataset(if(header)List(width){raw.first().getOrElse(it){""}.ifBlank {aliases[it]}} else aliases,(if(header)raw.drop(1) else raw).map {row->List(width){row.getOrElse(it){""}}})
}
private fun preparationNumber(cell:String):Double=cell.statisticsNumericCell().let {if(preparationNumber.matches(it))it.toDoubleOrNull()?.takeIf(Double::isFinite) ?: Double.NaN else Double.NaN}
private fun preparationIndices(text:String,width:Int,defaults:List<Int> = emptyList()):List<Int> {
    val values=if(text=="auto")defaults else text.split(',').filter(String::isNotBlank).map {it.trim().toIntOrNull() ?: -1}
    require(values.all {it in 0 until width}&&values.distinct().size==values.size) {"Choose valid data columns"};return values
}
private fun preparationNumericText(value:Double):String=if(value==0.0)"0" else value.toString().removeSuffix(".0")
private fun preparationResult(headers:List<String>,rows:List<List<String>>,changed:Int,omitted:Int,removeLimits:Boolean,filter:Boolean=false):StatisticsPreparationResult {
    require(headers.size in 1..100) {"Column count must be between 1 and 100"}
    require(filter||headers.all {it.isNotBlank()&&statisticsHasHeader(listOf(listOf(it),listOf("1")))}) {"Use a text column header"}
    require(filter||headers.map(String::lowercase).distinct().size==headers.size) {"New column header already exists"}
    require((filter||rows.isNotEmpty())&&(removeLimits||rows.size<=5000)) {"Enter 1–5000 data rows"}
    val all=listOf(headers)+rows;registerStatisticsHeader(all)
    return StatisticsPreparationResult(all.joinToString("\n"){row->if(row.size==1&&row[0].isBlank())"\"\"" else statisticsCsvLine(row)},statisticsKindForColumns(headers.size),headers,rows,changed,omitted)
}
internal fun preparationTransform(source:String,kind:String,operation:String,settings:Map<String,String> = emptyMap(),removeLimits:Boolean=false):StatisticsPreparationResult {
    val (headers,rows)=preparationDataset(source,kind);val width=headers.size
    require(rows.any {row->row.any(String::isNotBlank)}) {"Enter data first"}
    fun get(key:String,fallback:String="")=settings[key] ?: fallback
    fun result(names:List<String>,values:List<List<String>>,changed:Int,omitted:Int=0)=preparationResult(names,values,changed,omitted,removeLimits)
    when(operation) {
        "filter"->{
            val match=get("match","all");require(match in listOf("all","any")) {"Choose how to combine filter conditions"}
            val conditions=preparationFilterConditions(get("conditions","[{\"column\":\"0\",\"operator\":\"notBlank\",\"value\":\"\"}]"))
            val predicates=conditions.map {condition->
                require(Regex("[0-9]+").matches(condition.column)) {"Choose valid data columns"}
                val column=condition.column.toIntOrNull() ?: -1;preparationIndices(column.toString(),width)
                val op=condition.operator;val value=condition.value
                if(op in listOf("eq","neq","lt","lte","gt","gte")) {
                    val target=preparationNumber(value);require(target.isFinite()) {"Enter a finite numeric filter value"}
                    val predicate:(List<String>)->Boolean={row->val n=preparationNumber(row[column]);n.isFinite()&&when(op){"eq"->n==target;"neq"->n!=target;"lt"->n<target;"lte"->n<=target;"gt"->n>target;else->n>=target}}
                    predicate
                }else {
                    require(op in listOf("textEquals","textNotEquals","contains","startsWith","endsWith","blank","notBlank")) {"Choose a valid filter operator"}
                    require(op !in listOf("contains","startsWith","endsWith")||value.isNotBlank()) {"Enter a text filter value"}
                    val predicate:(List<String>)->Boolean={row->val cell=row[column];when(op){"textEquals"->cell==value;"textNotEquals"->cell!=value;"contains"->cell.contains(value);"startsWith"->cell.startsWith(value);"endsWith"->cell.endsWith(value);"blank"->cell.isBlank();else->cell.isNotBlank()}}
                    predicate
                }
            }
            val output=rows.filter {row->if(match=="all")predicates.all {it(row)} else predicates.any {it(row)}}
            return preparationResult(headers,output,rows.size-output.size,0,removeLimits,filter=true)
        }
        "wideToLong"->{
            val ids=preparationIndices(get("ids","0"),width)
            val measures=preparationIndices(get("measures","auto"),width,headers.indices.filter {it !in ids})
            require(measures.isNotEmpty()&&measures.none {it in ids}) {"Choose distinct ID and measurement columns"}
            val names=(if(ids.isEmpty())listOf(get("rowHeader","row_id").trim()) else ids.map {headers[it]})+listOf(get("variableHeader","variable").trim(),get("valueHeader","value").trim())
            require(names.size<=100) {"Column count must be between 1 and 100"}
            require(removeLimits||rows.size.toLong()*measures.size<=5000) {"Enter 1–5000 data rows"}
            val output=rows.flatMapIndexed {index,row->measures.map {column->(if(ids.isEmpty())listOf((index+1).toString()) else ids.map {row[it]})+listOf(headers[column],row[column])}}
            return result(names,output,output.size)
        }
        "longToWide"->{
            val ids=preparationIndices(get("ids","0"),width);val variable=get("variable","1").toIntOrNull() ?: -1
            val value=get("value","-1").toIntOrNull()?.let {if(it==-1)width-1 else it} ?: -1
            require(ids.isNotEmpty()&&variable in headers.indices&&value in headers.indices&&variable!=value&&variable !in ids&&value !in ids) {"Choose distinct ID, variable and value columns"}
            val policy=get("duplicates","error");require(policy in listOf("error","first","last","sum","mean")) {"Invalid duplicate policy"}
            val variables=linkedSetOf<String>();val groups=linkedMapOf<List<String>,MutableMap<String,MutableList<String>>>()
            rows.forEach {row->
                require(ids.all {row[it].isNotBlank()}&&row[variable].isNotBlank()) {"ID and variable cells must not be blank"}
                val id=ids.map {row[it]};val name=row[variable];variables.add(name)
                require(ids.size+variables.size<=100) {"Column count must be between 1 and 100"}
                groups.getOrPut(id){linkedMapOf()}.getOrPut(name){mutableListOf()}.add(row[value])
            }
            val output=groups.map {(id,entries)->id+variables.map {name->
                val cells=entries[name].orEmpty();require(cells.size<=1||policy!="error") {"Duplicate ID / variable pair; choose an aggregation"}
                if(policy in listOf("sum","mean")) {
                    val values=cells.filter(String::isNotBlank).map(::preparationNumber)
                    require(values.all(Double::isFinite)) {"Aggregation requires finite numeric values"}
                    if(values.isEmpty())"" else {
                        val aggregate=if(policy=="mean")values.sumOf {it/values.size} else values.sum()
                        require(aggregate.isFinite()) {"Aggregation result is not finite"};preparationNumericText(aggregate)
                    }
                }else (if(policy=="last")cells.lastOrNull() else cells.firstOrNull()).orEmpty()
            }}
            return result(ids.map {headers[it]}+variables.map {get("prefix")+it},output,output.size)
        }
        "recode"->{
            val column=get("column","0").toIntOrNull() ?: -1;preparationIndices(column.toString(),width)
            val method=get("method","exact");val otherwise=get("otherwise","keep");val output=get("output","append")
            require(method in listOf("exact","intervals")&&otherwise in listOf("keep","blank","value")&&output in listOf("append","replace")) {"Invalid recode option"}
            val mapping=linkedMapOf<String,String>();var cuts=emptyList<Double>();var labels=emptyList<String>()
            if(method=="exact") {
                get("rules").lineSequence().filter(String::isNotBlank).forEach {line->
                    val match=Regex("^(.*?)\\s*,\\s*(.*)$").matchEntire(line)
                    require(match!=null&&match.groupValues[1].trim().isNotBlank()) {"Use one old value, new value mapping per line"}
                    val key=match.groupValues[1].trim().let {if(it=="<missing>")"" else it}
                    require(key !in mapping) {"Duplicate value mapping"};mapping[key]=match.groupValues[2].trim()
                }
                require(mapping.isNotEmpty()) {"Enter value mappings"}
            }else {
                cuts=get("cuts").trim().split(Regex("[,;\\s]+")).filter(String::isNotBlank).map(::preparationNumber)
                require(cuts.isNotEmpty()&&cuts.all(Double::isFinite)&&cuts.zipWithNext().all {(a,b)->a<b}) {"Cut points must be strictly increasing"}
                labels=get("groups","0,1").split(Regex("[,;\\r\\n]")).map(String::trim)
                require(labels.size==cuts.size+1) {"Enter one group value per interval"}
            }
            var changed=0
            val values=rows.map {row->
                val original=row[column];val n=preparationNumber(original)
                val replacement=if(method=="exact"&&original in mapping)mapping.getValue(original) else if(method=="intervals"&&n.isFinite())labels[cuts.indexOfFirst {n<it}.takeIf {it>=0} ?: cuts.size]
                    else when(otherwise){"keep"->original;"value"->get("otherwiseValue");else->""}
                if(replacement!=original)changed++;replacement
            }
            val names=headers.toMutableList().apply {if(output=="append")add(get("header","recoded").trim()) else this[column]=get("header","recoded").trim()}
            return result(names,rows.mapIndexed {i,row->if(output=="append")row+values[i] else row.mapIndexed {j,cell->if(j==column)values[i] else cell}},changed)
        }
        "derive"->{
            val tree=Parser(get("formula"),removeComputationLimit=removeLimits).parse();val bindings=linkedMapOf<String,Int>()
            headers.forEachIndexed {index,name->if(preparationIdentifier.matches(name))bindings[name]=index}
            statisticsColumnNames(statisticsKindForColumns(width)).forEachIndexed {i,name->bindings.putIfAbsent(name,i)}
            validatePreparationFormula(tree,bindings)
            var omitted=0
            val output=rows.map {row->val value=evaluatePreparationFormula(tree,row,bindings);if(value.isFinite())row+preparationNumericText(value) else {omitted++;row+""}}
            require(omitted<rows.size) {"No finite derived values; check the formula and data"}
            return result(headers+get("header","derived").trim(),output,rows.size-omitted,omitted)
        }
        else->error("Unknown preparation operation")
    }
}
internal data class StatisticsFilterCondition(val column:String,val operator:String,val value:String)
internal fun preparationFilterConditions(text:String):List<StatisticsFilterCondition> {
    val array=runCatching {JSONArray(text)}.getOrElse {error("Enter valid filter conditions")}
    require(array.length()>0) {"Enter valid filter conditions"}
    return List(array.length()){index->
        val item=array.optJSONObject(index);require(item!=null) {"Enter valid filter conditions"}
        val column=item.opt("column");val op=item.opt("operator");val value=item.opt("value")
        require((column is String||column is Number)&&op is String&&value is String) {"Enter valid filter conditions"}
        StatisticsFilterCondition(column.toString(),op,value)
    }
}
private val preparationUnary=setOf("abs","sqrt","exp","ln","log10","sin","cos","tan","asin","acos","atan","floor","ceil","sign","percent","degree")
private fun validatePreparationFormula(node:Expr,bindings:Map<String,Int>) {
    when(node.kind) {
        "number"->return
        "symbol"->{require(node.value in bindings||node.value in listOf("pi","e","true","false")) {"Unknown column in formula: ${node.value}"};return}
        "group"->Unit
        "unary"->require(node.value in listOf("+","-")) {"Unsupported formula expression"}
        "binary"->require(node.value in listOf("+","-","*","/","^","mod")) {"Unsupported formula expression"}
        "relation"->require(node.value in listOf("=","==","!=","<",">","<=",">=")) {"Unsupported formula expression"}
        "call"->{val n=node.args.size;val name=node.value;require(name in preparationUnary&&n==1||name in listOf("log","round")&&n in 1..2||name=="pow"&&n==2||name=="if"&&n==3||name in listOf("min","max","sum","mean")&&n>=1) {"Unsupported function or argument count: $name"}}
        else->error("Unsupported formula expression")
    }
    node.args.forEach {validatePreparationFormula(it,bindings)}
}
private fun evaluatePreparationFormula(node:Expr,row:List<String>,bindings:Map<String,Int>):Double {
    if(node.kind=="number")return node.value.toDouble()
    if(node.kind=="symbol")return bindings[node.value]?.let {preparationNumber(row[it])} ?: when(node.value){"pi"->PI;"e"->E;"true"->1.0;else->0.0}
    if(node.kind=="group")return evaluatePreparationFormula(node.args.first(),row,bindings)
    if(node.kind=="call"&&node.value=="if") {val condition=evaluatePreparationFormula(node.args[0],row,bindings);return if(condition.isFinite())evaluatePreparationFormula(node.args[if(condition==0.0)2 else 1],row,bindings) else Double.NaN}
    val values=node.args.map {evaluatePreparationFormula(it,row,bindings)};if(values.any {!it.isFinite()})return Double.NaN
    val a=values[0];val b=values.getOrElse(1){0.0};val op=node.value
    if(node.kind=="unary")return if(op=="-")-a else a
    if(node.kind=="binary")return when(op){"+"->a+b;"-"->a-b;"*"->a*b;"/"->a/b;"^"->a.pow(b);else->((a%b)+b)%b}
    if(node.kind=="relation")return if(when(op){"=","=="->a==b;"!="->a!=b;"<"->a<b;">"->a>b;"<="->a<=b;else->a>=b})1.0 else 0.0
    return when(op) {
        "log"->ln(a)/if(values.size==2)ln(b) else 1.0
        "round"->if(b!=floor(b)||abs(b)>15)Double.NaN else 10.0.pow(b).let {scale->sign(a)*floor(abs(a)*scale+.5)/scale}
        "pow"->a.pow(b);"sum"->values.sum();"mean"->values.sumOf {it/values.size};"min"->values.min();"max"->values.max()
        "abs"->abs(a);"sqrt"->sqrt(a);"exp"->exp(a);"ln"->ln(a);"log10"->log10(a)
        "sin"->sin(a);"cos"->cos(a);"tan"->tan(a);"asin"->asin(a);"acos"->acos(a);"atan"->atan(a)
        "floor"->floor(a);"ceil"->ceil(a);"sign"->sign(a);"percent"->a/100;"degree"->a*PI/180
        else->Double.NaN
    }
}
