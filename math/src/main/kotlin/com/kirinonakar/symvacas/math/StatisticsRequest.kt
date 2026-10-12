package com.kirinonakar.symvacas.math

data class StatisticsRequest(val tree:Expr,val datasets:Map<String,List<Any>>)

/** Parse the small formula and carry decimal dataset cells separately. */
fun statisticsRequest(source:String,removeComputationLimit:Boolean=false):StatisticsRequest {
    require(removeComputationLimit||source.length<=16*1024*1024) {"Statistics input size limit"}
    val datasets=linkedMapOf<String,List<Any>>()
    val formula=StringBuilder()
    var from=0
    while(from<source.length) {
        val start=source.indexOf('[',from)
        if(start<0){formula.append(source.substring(from));break}
        formula.append(source.substring(from,start))
        var end=start;var depth=0
        do {if(source[end]=='[')depth++ else if(source[end]==']')depth--;end++} while(end<source.length&&depth>0)
        val literal=source.substring(start,end)
        val data=runCatching {NumericStatisticsList(literal).parse()}.getOrNull()
            ?: if(source.length>8192)runCatching {ExpressionStatisticsList(literal,removeComputationLimit).parse()}.getOrNull() else null
        if(data==null)formula.append(literal) else {
            var name="SymvaStatisticsData${datasets.size}"
            while(source.contains(name)||name in datasets)name+="Data"
            datasets[name]=data;formula.append(name)
        }
        from=end
    }
    return StatisticsRequest(Parser(formula.toString(),removeComputationLimit=removeComputationLimit).parse(),datasets)
}

/** Cell AST maps are JSON-compatible; only individual formulas consume parser limits. */
private class ExpressionStatisticsList(val source:String,val removeComputationLimit:Boolean) {
    private var at=0
    private val numeric=Regex("[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?")
    private fun space(){while(source.getOrNull(at)?.isWhitespace()==true)at++}
    fun parse():List<Any> {val result=list(1);space();require(at==source.length);return result}
    private fun ast(node:Expr):Map<String,Any> = mapOf("kind" to node.kind,"value" to node.value,"args" to node.args.map(::ast))
    private fun list(depth:Int):List<Any> {
        require(depth<=2&&source.getOrNull(at++)=='[') {"Statistics dataset expected"}
        space();val values=mutableListOf<Any>()
        if(source.getOrNull(at)==']'){at++;return values}
        while(true) {
            space()
            if(source.getOrNull(at)=='[')values.add(list(depth+1)) else {
                val start=at;val stack=mutableListOf<Char>();val pairs=mapOf('(' to ')','[' to ']','{' to '}')
                while(at<source.length) {
                    val c=source[at];if(stack.isEmpty()&&(c==','||c==']'))break
                    if(c in pairs)stack.add(pairs.getValue(c)) else if(c in ")]}")require(stack.isNotEmpty()&&stack.removeAt(stack.lastIndex)==c) {"Unbalanced dataset cell"}
                    at++
                }
                val cell=source.substring(start,at).trim();require(cell.isNotEmpty()&&stack.isEmpty()) {"Statistics dataset cell expected"}
                values.add(if(numeric.matches(cell))cell else ast(Parser(cell,removeComputationLimit=removeComputationLimit).parse()))
            }
            space();if(source.getOrNull(at)==']'){at++;return values}
            require(source.getOrNull(at++)==',') {"Statistics dataset expected"}
        }
    }
}

private class NumericStatisticsList(val source:String) {
    private var at=0
    private val number=Regex("[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?")
    private fun space(){while(source.getOrNull(at)?.isWhitespace()==true)at++}
    fun parse():List<Any> {val values=list(1);space();require(at==source.length);return values}
    private fun list(depth:Int):List<Any> {
        require(depth<=2&&source.getOrNull(at++)=='[')
        space();val values=mutableListOf<Any>()
        if(source.getOrNull(at)==']'){at++;return values}
        while(true) {
            space()
            if(source.getOrNull(at)=='[')values.add(list(depth+1)) else {
                val token=number.matchAt(source,at)?:error("Numeric dataset expected")
                values.add(token.value);at=token.range.last+1
            }
            space();if(source.getOrNull(at)==']'){at++;return values}
            require(source.getOrNull(at++)==',')
        }
    }
}
