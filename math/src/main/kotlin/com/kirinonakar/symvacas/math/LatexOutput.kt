package com.kirinonakar.symvacas.math

/** Clipboard serialization shared by editable and engine-produced expression trees. */
object LatexOutput {
    private val functions=setOf("sin","cos","tan","sec","csc","cot","sinh","cosh","tanh","arcsin","arccos","arctan","ln","log","exp")
    private val relations=mapOf("==" to "=","<=" to "\\leq ","≤" to "\\leq ",">=" to "\\geq ","≥" to "\\geq ","!=" to "\\neq ","->" to "\\to ","→" to "\\to ","×" to "\\times ","÷" to "\\div ")
    private fun escape(value:String)=value.map {when(it){'\\'->"\\backslash ";'_'->"\\_";'{'->"\\{";'}'->"\\}";'%'->"\\%";'&'->"\\&";'#'->"\\#";'$'->"\\$";else->it.toString()}}.joinToString("")
    private fun fence(value:String)="\\left($value\\right)"
    private fun symbol(value:String):String {
        val name=LatexInput.symbolLabels.entries.firstOrNull {it.value==value}?.key ?: value
        if(name in LatexInput.symbolLabels)return "\\$name "
        if(name in listOf("oo","∞"))return "\\infty "
        if(name=="E")return "e"
        if(name=="I")return "i"
        if(name=="EmptySet")return "\\varnothing"
        if('_' in name) return symbol(name.substringBefore('_')).trimEnd()+"_{\\mathrm{${escape(name.substringAfter('_'))}}}"
        return if(name.length<=1)name else "\\mathrm{${escape(name)}}"
    }
    fun convert(source:String):String=source.split('\n').joinToString("\n") {line->
        if(line.isBlank())line else runCatching {render(Parser(LatexInput.convert(line) ?: line).parse())}.getOrDefault(line)
    }
    fun render(node:Expr):String {
        val a=node.args;val v=node.value
        fun p(i:Int)=a.getOrNull(i)?.let(::render).orEmpty()
        fun operand(i:Int)=if(a.getOrNull(i)?.let {it.kind in listOf("sum","relation","unary") || it.kind=="binary"&&it.value in listOf("+","-") }==true)fence(p(i)) else p(i)
        fun power()="${if(a.getOrNull(0)?.let {it.kind=="power"||it.kind=="binary"&&it.value=="^"}==true)fence(p(0)) else operand(0)}^{${p(1)}}"
        fun fraction()="\\frac{${p(0)}}{${p(1)}}"
        fun call(name:String):String {
            val args=a.joinToString(", "){render(it)}
            return when(name) {
                "sqrt"->"\\sqrt{${p(0)}}"
                "cbrt"->"\\sqrt[3]{${p(0)}}"
                "nthroot"->"\\sqrt[${p(1)}]{${p(0)}}"
                "abs","Abs"->"\\left|${p(0)}\\right|"
                "exp"->"e^{${p(0)}}"
                "log"->if(a.size==2)"\\log_{${p(1)}}${fence(p(0))}" else "\\log${fence(args)}"
                "integrate","Integral","sum","Sum","product","Product"->{
                    val b=if(a.getOrNull(1)?.kind=="tuple")a[1].args else a.drop(1)
                    val integral=name in listOf("integrate","Integral")
                    val op=if(integral)"\\int" else if(name.lowercase()=="sum")"\\sum" else "\\prod"
                    val lower=if(b.size>=3)"_{${if(integral)"" else render(b[0])+"="}${render(b[1])}}^{${render(b[2])}}" else ""
                    "$op$lower ${p(0)}"+if(integral)"\\,d${b.firstOrNull()?.let(::render).orEmpty()}" else ""
                }
                "diff","Derivative"->"\\frac{d${if(a.size>2)"^{${p(2)}}" else ""}}{d${p(1)}${if(a.size>2)"^{${p(2)}}" else ""}}${fence(p(0))}"
                "limit","Limit"->"\\lim_{${p(1)} \\to ${p(2)}${if(a.getOrNull(3)?.value=="right")"^{+}" else if(a.getOrNull(3)?.value=="left")"^{-}" else ""}} ${p(0)}"
                "factorial"->operand(0)+"!"
                "percent"->operand(0)+"\\%"
                "degree"->operand(0)+"^{\\circ}"
                "mixed"->p(0)+"\\,\\frac{${p(1)}}{${p(2)}}"
                else->(if(name in functions)"\\$name" else "\\operatorname{${escape(name)}}")+fence(args)
            }
        }
        return when(node.kind) {
            "number","float","fixed-number"->{val parts=v.split(Regex("[eE]"));if(parts.size==2)"${parts[0]} \\times 10^{${parts[1].removePrefix("+")}}" else v}
            "symbol","snapshot_symbol"->symbol(v).trimEnd()
            "group","parentheses"->fence(p(0))
            "binary"->when(v){"/"->fraction();"^"->power();"*"->operand(0)+" \\cdot "+operand(1);else->p(0)+(relations[v] ?: v)+if(v=="-")operand(1) else p(1)}
            "fraction"->fraction()
            "power"->power()
            "root"->"\\sqrt{${p(0)}}"
            "indexed-root"->"\\sqrt[${p(1)}]{${p(0)}}"
            "unary"->v+operand(0)
            "relation"->a.joinToString(" ${relations[v] ?: v} "){render(it)}
            "sum"->a.mapIndexed {i,x->if(i>0&&x.kind!="unary")"+"+render(x) else render(x)}.joinToString("")
            "product","explicit-product","implicit-product"->a.indices.joinToString(" \\cdot "){operand(it)}
            "call","function","frozen_call"->call(v)
            "integral"->call("integrate")
            "derivative"->call("diff")
            "point-derivative"->"\\left.\\frac{d}{d${p(1)}}${fence(p(0))}\\right|_{${p(1)}=${p(2)}}"
            "limit"->call("limit")
            "large-operator"->call(if(v in listOf("Π","∏"))"product" else "sum")
            "logarithm"->call("log")
            "postfix"->operand(0)+when(v){"%"->"\\%";"°"->"^{\\circ}";else->v}
            "mixed"->p(0)+"\\,"+p(1)
            "dms","sexagesimal"->a.indices.joinToString(""){p(it)+listOf("^{\\circ}","^{\\prime}","^{\\prime\\prime}").getOrElse(it){""}}
            "matrix"->"\\begin{bmatrix}"+a.joinToString(" \\\\ "){row->row.args.joinToString(" & "){render(it)}}+"\\end{bmatrix}"
            "list"->if(a.isNotEmpty()&&a.all {it.kind=="list"&&it.args.size==a[0].args.size})render(node.copy(kind="matrix")) else "\\left["+a.joinToString(", "){render(it)}+"\\right]"
            "set"->"\\left\\{"+a.joinToString(", "){render(it)}+"\\right\\}"
            "tuple"->fence(a.joinToString(", "){render(it)})
            "row-operation"->"\\xrightarrow{${p(0)}}${p(1)}"
            "row"->"\\text{${escape(v)}: }${p(0)}"
            "rows"->a.joinToString("\n"){render(it)}
            "piecewise"->"\\begin{cases}"+a.joinToString(" \\\\ "){render(it.args[0])+" & "+render(it.args[1])}+"\\end{cases}"
            "restricted"->p(0)
            "quantity"->p(0)+"\\,\\mathrm{${escape(v)}}"
            "text","constant","input-text"->runCatching {render(Parser(v).parse())}.getOrElse {"\\text{${escape(v)}}"}
            else->if(v.isNotEmpty())symbol(v) else a.joinToString(" "){render(it)}
        }
    }
}
