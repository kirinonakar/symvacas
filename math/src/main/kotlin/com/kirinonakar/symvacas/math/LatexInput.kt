package com.kirinonakar.symvacas.math

/** Converts pasted, supported LaTeX math into the calculator's editable expression syntax. */
object LatexInput {
    private val functions = setOf("sin","cos","tan","sec","csc","cot","sinh","cosh","tanh","arcsin","arccos","arctan","ln","exp")
    val symbolLabels = mapOf("alpha" to "α","beta" to "β","gamma" to "γ","delta" to "δ","epsilon" to "ϵ","varepsilon" to "ε","zeta" to "ζ","eta" to "η","theta" to "θ","vartheta" to "ϑ","iota" to "ι","kappa" to "κ","varkappa" to "ϰ","lambda" to "λ","mu" to "μ","nu" to "ν","xi" to "ξ","pi" to "π","varpi" to "ϖ","rho" to "ρ","varrho" to "ϱ","sigma" to "σ","varsigma" to "ς","tau" to "τ","upsilon" to "υ","phi" to "ϕ","varphi" to "φ","chi" to "χ","psi" to "ψ","omega" to "ω","Gamma" to "Γ","Delta" to "Δ","Theta" to "Θ","Lambda" to "Λ","Xi" to "Ξ","Pi" to "Π","Sigma" to "Σ","Upsilon" to "Υ","Phi" to "Φ","Psi" to "Ψ","Omega" to "Ω")
    private val greek = symbolLabels.keys
    private val commands = setOf("boxed","operatorname","mathrm","int","sum","prod","binom","begin","lim","frac","dfrac","tfrac","sqrt","log","infty","times","cdot","left","right","quad","qquad","le","leq","ge","geq","ne","neq") + functions + greek
    private val commandPattern = Regex("""\\([A-Za-z]+)""")
    private val bracedPower = Regex("""\^\s*\{""")

    /** Returns null for ordinary text or unsupported LaTeX. Prefix/suffix preserve insertion scope. */
    fun convert(input: String, prefix:String="", suffix:String=""): String? {
        val trimmed=input.trim()
        val wrapped=trimmed.startsWith("\\[") || trimmed.startsWith("\\(") || trimmed.startsWith('$')
        if(!wrapped && !bracedPower.containsMatchIn(input) && !commandPattern.findAll(input).any {it.groupValues[1] in commands || it.groupValues[1]=="int"})return null
        var source=trimmed
        source=when {
            source.startsWith("\\[") && source.endsWith("\\]") -> source.substring(2,source.length-2)
            source.startsWith("\\(") && source.endsWith("\\)") -> source.substring(2,source.length-2)
            source.startsWith("$$") && source.endsWith("$$") && source.length>=4 -> source.substring(2,source.length-2)
            source.startsWith('$') && source.endsWith('$') && source.length>=2 -> source.substring(1,source.length-1)
            else -> source
        }.trim()
        return runCatching {
            val converted=convertBody(source)
            Parser(converted).parse()
            if(prefix.isEmpty() && suffix.isEmpty())compactExpression(converted)
            // Remove only inserted fences and check precedence against the complete edit.
            else runCatching {
                compactExpression(prefix+converted+suffix,prefix.length,prefix.length+converted.length)
                    .let {it.substring(prefix.length,it.length-suffix.length)}
            }.getOrDefault(converted)
        }.getOrNull()
    }

    /** Preserve independent graph/equation lines, including the surrounding line's precedence. */
    fun convertPaste(input:String,prefix:String="",suffix:String="",multiline:Boolean=false):String? {
        if(!multiline || '\n' !in input)return convert(input,prefix.substringAfterLast('\n'),suffix.substringBefore('\n'))
        val lines=input.split('\n')
        var changed=false
        val converted=lines.mapIndexed {index,line->
            val result=convert(line,if(index==0)prefix.substringAfterLast('\n') else "",if(index==lines.lastIndex)suffix.substringBefore('\n') else "")
            // A wrapped expression or matrix can span physical lines; convert it as one unit.
            if(result==null && (line.trim().startsWith('$') || line.contains('\\') || bracedPower.containsMatchIn(line)))return convert(input,prefix.substringAfterLast('\n'),suffix.substringBefore('\n'))
            if(result!=null)changed=true
            result ?: line
        }.joinToString("\n")
        return converted.takeIf {changed}
    }

    /** Convert only inserted text and leave selection-only updates intact. */
    fun convertEdit(previous:Editor,updated:String,multiline:Boolean=false):Editor? {
        if(updated==previous.source)return null
        val start=minOf(previous.cursor,previous.anchor)
        val end=maxOf(previous.cursor,previous.anchor)
        val prefix=previous.source.substring(0,start)
        val suffix=previous.source.substring(end)
        if(updated.length>=prefix.length+suffix.length && updated.startsWith(prefix) && updated.endsWith(suffix)) {
            val inserted=updated.substring(prefix.length,updated.length-suffix.length)
            convertPaste(inserted,prefix,suffix,multiline)?.let {return Editor(prefix+it+suffix,start+it.length)}
            return null
        }
        return convertPaste(updated,multiline=multiline)?.let {Editor(it)}
    }

    private fun convertBody(source:String):String = buildString {
        var index=0
        var absolute=false
        while(index<source.length) {
            val c=source[index]
            if(c=='|') {
                append(if(absolute)")" else "abs(");absolute=!absolute;index++;continue
            }
            if(c in 'a'..'z' || c in 'A'..'Z') {
                val start=index++
                while(source.getOrNull(index)?.let {it in 'a'..'z' || it in 'A'..'Z'}==true)index++
                val name=source.substring(start,index)
                // Bare LaTeX letters are factors; commands and explicit names stay intact.
                val named=name in greek || name in functions || name in setOf("log","pi","oo","Ans","true","false","mod") || source.substring(index).trimStart().startsWith('(')
                if(toString().trimEnd().lastOrNull()?.let {it.isLetter() || it=='_'}==true && name!="mod")append('*')
                append(if(named)name else name.toList().joinToString("*"))
                if(source.getOrNull(index)=='_' && source.getOrNull(index+1)!='{') {
                    val subscript=index++
                    while(source.getOrNull(index)?.let {it.isLetterOrDigit() || it=='_'}==true)index++
                    append(source.substring(subscript,index))
                }
                continue
            }
            if(c=='_' && source.getOrNull(index+1)=='{') {
                val (raw,next)=group(source,index+1)
                val name=if(raw.matches(Regex("[A-Za-z0-9_]+")))raw else convertBody(raw)
                require(name.matches(Regex("[A-Za-z0-9_]+"))) {"Unsupported LaTeX subscript"}
                append('_').append(name);index=next;continue
            }
            if(c=='(' || c=='{') {
                val (raw,next)=group(source,index,c,if(c=='(')')' else '}')
                var converted=convertBody(raw)
                // An explicit fence already groups a sole fraction; reuse that fence.
                if(c=='(' && Regex("""^\s*\\(?:frac|dfrac|tfrac)\b""").containsMatchIn(raw)) {
                    val tree=runCatching {Parser(converted).parse()}.getOrNull()
                    if(tree?.kind=="group" && tree.args[0].kind=="binary" && tree.args[0].value=="/")converted=converted.substring(1,converted.length-1)
                }
                append('(').append(converted).append(')')
                index=next
                continue
            }
            if(c!='\\') {
                append(when(c){'{','}' -> if(c=='{')'(' else ')';'−' -> '-';else -> c})
                index++
                continue
            }
            index++
            if(index>=source.length)error("Incomplete LaTeX command")
            val start=index
            while(index<source.length && source[index].isLetter())index++
            if(index==start) {
                if(source[index] in "{}%") {append(source[index]);index++;continue}
                if(source[index] !in ",;! ")error("Unsupported LaTeX spacing")
                index++
                continue
            }
            val command=source.substring(start,index)
            if(command !in commands)error("Unsupported LaTeX command: $command")
            when(command) {
                "boxed" -> {
                    val (raw,next)=group(source,index)
                    append('(').append(convertBody(raw)).append(')');index=next
                }
                "operatorname","mathrm" -> {
                    val (raw,next)=group(source,index)
                    require(raw.matches(Regex("[A-Za-z0-9_]+"))) {"Unsupported LaTeX name"}
                    append(raw);index=next
                }
                "begin" -> {
                    val (environment,start)=group(source,index)
                    require(environment in setOf("matrix","pmatrix","bmatrix","Bmatrix","vmatrix","Vmatrix","smallmatrix")) {"Unsupported LaTeX environment"}
                    val endCommand="\\end{$environment}"
                    val end=source.indexOf(endCommand,start)
                    require(end>=0) {"Unclosed LaTeX matrix"}
                    append(convertMatrix(source.substring(start,end)))
                    index=end+endCommand.length
                }
                "int", "sum", "prod" -> {
                    val (limits,next)=bounds(source,index)
                    index=next
                    if(command=="int") {
                        val (expression,variable,end)=integralExpression(source,index)
                        append("integrate(").append(expression).append(',').append(variable)
                        if(limits.containsKey('_'))append(',').append(limits['_']).append(',').append(limits['^'])
                        append(')');index=end
                    } else {
                        val lower=limits['_'] ?: error("Expected LaTeX sum/product bounds")
                        val tree=Parser(lower).parse()
                        require(tree.kind=="relation" && tree.value=="=" && tree.args[0].kind=="symbol") {"Expected index=lower bound"}
                        val split=lower.indexOf('=')
                        val end=limitExpressionEnd(source,index)
                        val expression=compactExpression(convertBody(source.substring(index,end)))
                        append(if(command=="sum")"sum(" else "product(").append(expression).append(',').append(lower.substring(0,split)).append(',').append(lower.substring(split+1)).append(',').append(limits['^']).append(')')
                        index=end
                    }
                }
                "lim" -> {
                    index=skipSpacing(source,index)
                    require(source.getOrNull(index)=='_') {"Expected LaTeX limit approach"}
                    val (approach,next)=group(source,index+1)
                    index=next
                    val parts=approach.split(Regex("""\\(?:to|rightarrow)\b|->|→"""))
                    require(parts.size==2) {"Expected LaTeX limit arrow"}
                    val variable=convertBody(parts[0])
                    require(Parser(variable).parse().kind=="symbol") {"Expected limit variable"}
                    var point=parts[1].trim()
                    val side=Regex("""\^\s*(?:\{\s*([+-])\s*\}|([+-]))\s*$""").find(point)
                    val direction=if(side==null)"" else {
                        point=point.substring(0,side.range.first)
                        if((side.groupValues[1]+side.groupValues[2])=="+")",right" else ",left"
                    }
                    point=convertBody(point)
                    Parser(point).parse()
                    val end=limitExpressionEnd(source,index)
                    val expression=compactExpression(convertBody(source.substring(index,end)))
                    append("limit(").append(expression).append(',').append(variable).append(',').append(point).append(direction).append(')')
                    index=end
                }
                "frac", "dfrac", "tfrac" -> {
                    val (top,afterTop)=group(source,index)
                    val (bottom,afterBottom)=group(source,afterTop)
                    append("((").append(convertBody(top)).append(")/(").append(convertBody(bottom)).append("))")
                    index=afterBottom
                }
                "binom" -> {
                    val (top,afterTop)=group(source,index)
                    val (bottom,next)=group(source,afterTop)
                    append("nCr(").append(logOperand(top)).append(',').append(logOperand(bottom)).append(')')
                    index=next
                }
                "sqrt" -> {
                    while(source.getOrNull(index)?.isWhitespace()==true)index++
                    val degree=if(source.getOrNull(index)=='[') {
                        val (value,next)=group(source,index,'[',']')
                        index=next
                        convertBody(value)
                    } else null
                    val (argument,next)=group(source,index)
                    if(degree==null)append("sqrt(").append(convertBody(argument)).append(")")
                    else append("nthroot(").append(convertBody(argument)).append(',').append(degree).append(")")
                    index=next
                }
                "log" -> {
                    index=skipSpacing(source,index)
                    val base=if(source.getOrNull(index)=='_') {
                        val (value,next)=argument(source,index+1,singleToken=true)
                        index=skipSpacing(source,next)
                        logOperand(value)
                    } else null
                    // Keep the calculator's existing explicit log(value,base) syntax.
                    if(base==null && (source.getOrNull(index)=='(' || source.startsWith("\\left",index))) {
                        append("log")
                    } else {
                        val (value,next)=argument(source,index)
                        append("log(").append(logOperand(value))
                        if(base!=null)append(',').append(base)
                        append(')')
                        index=next
                    }
                }
                "infty" -> append("oo")
                "times", "cdot" -> append('*')
                "left", "right" -> {
                    index=skipSpacing(source,index)
                    if(source.getOrNull(index)=='|') {append(if(command=="left")"abs(" else ")");index++}
                    else if(command=="left" && source.getOrNull(index)=='[') {append('(');index++}
                    else if(command=="right" && source.getOrNull(index)==']') {append(')');index++}
                }
                "quad", "qquad" -> Unit
                in functions -> {
                    val name=mapOf("arcsin" to "asin","arccos" to "acos","arctan" to "atan")[command] ?: command
                    index=skipSpacing(source,index)
                    val exponent=if(source.getOrNull(index)=='^') {
                        val (value,next)=argument(source,index+1,true)
                        index=skipSpacing(source,next)
                        convertBody(value)
                    } else null
                    if(exponent==null && (source.getOrNull(index)=='(' || source.startsWith("\\left",index)))append(name)
                    else {
                        val (value,next)=argument(source,index)
                        append(name).append('(').append(convertBody(value)).append(')')
                        if(exponent!=null)append("^(").append(exponent).append(')')
                        index=next
                    }
                }
                "le", "leq" -> append("<=")
                "ge", "geq" -> append(">=")
                "ne", "neq" -> append("!=")
                in greek -> {
                    if(toString().trimEnd().lastOrNull()?.let {it.isLetter() || it=='_'}==true)append('*')
                    append(command)
                    val following=source.substring(index).trimStart()
                    val nextCommand=commandPattern.find(following)?.takeIf {it.range.first==0}?.groupValues?.get(1)
                    if(following.firstOrNull()?.isLetterOrDigit()==true || nextCommand in greek || nextCommand in functions || nextCommand in setOf("boxed","frac","dfrac","tfrac","sqrt","binom","log","sum","prod","int","lim"))append('*')
                }
                else -> append(command)
            }
        }
        require(!absolute) {"Unclosed LaTeX absolute value"}
    }.replace(Regex("""\s+"""), "")

    private fun bounds(source:String,from:Int):Pair<Map<Char,String>,Int> {
        val values=mutableMapOf<Char,String>()
        var index=skipSpacing(source,from)
        while(source.getOrNull(index) in listOf('_','^')) {
            val marker=source[index++]
            require(marker !in values) {"Duplicate LaTeX bound"}
            val (value,next)=argument(source,index,true)
            values[marker]=logOperand(value);index=skipSpacing(source,next)
        }
        require(values.containsKey('_')==values.containsKey('^')) {"Expected both LaTeX bounds"}
        return values to index
    }

    private val scopeEnd=Regex("""^\\(?:right|leq?|geq?|neq?)\b""")
    private val differential=Regex("""^(?:\\mathrm\s*\{\s*d\s*\}|d)\s*(\\[A-Za-z]+|[A-Za-z])(?=\s*(?:$|[+\-)=<>,}\]]|\\(?:right|leq?|geq?|neq?)\b|d\s*[A-Za-z]))""")
    private fun integralExpression(source:String,from:Int):Triple<String,String,Int> {
        var index=from;var depth=0;var nested=0
        while(index<source.length) {
            val tail=source.substring(index);val c=source[index]
            if(depth==0) {
                if(Regex("""^\\[,;! ]""").containsMatchIn(tail)) {index+=2;continue}
                val match=differential.find(tail)
                if(match!=null && (index==from || !source[index-1].isLetter())) {
                    if(nested>0)nested--
                    else {
                        val raw=source.substring(from,index).trim().replace(Regex("""\\[,;! ]\s*$"""),"")
                        val variable=convertBody(match.groupValues[1])
                        require(Parser(variable).parse().kind=="symbol") {"Expected integration variable"}
                        return Triple(if(raw.isEmpty())"1" else convertBody(raw),variable,index+match.value.length)
                    }
                }
                if(Regex("""^\\int\b""").containsMatchIn(tail))nested++
                if(c in ")]},=<>" || scopeEnd.containsMatchIn(tail))break
            }
            if(c in "([{")depth++ else if(c in ")]}")depth--
            index++
        }
        error("Expected LaTeX integral differential")
    }

    private fun convertMatrix(content:String):String {
        val rows=mutableListOf(mutableListOf<String>())
        var index=0;var start=0;var depth=0
        while(index<content.length) {
            val c=content[index]
            if(c in "([{")depth++ else if(c in ")]}")depth--
            if(depth==0 && (c=='&' || content.startsWith("\\\\",index))) {
                rows.last().add(convertBody(content.substring(start,index)))
                if(c!='&') {rows.add(mutableListOf());index++}
                start=index+1
            }
            index++
        }
        if(content.substring(start).isNotBlank())rows.last().add(convertBody(content.substring(start)))
        else if(rows.last().isEmpty() && rows.size>1)rows.removeAt(rows.lastIndex)
        else rows.last().add("")
        require(rows.first().isNotEmpty() && rows.all {row->row.size==rows.first().size && row.all {it.isNotEmpty()}}) {"Expected rectangular LaTeX matrix"}
        return rows.joinToString(",","[","]") {it.joinToString(",","[","]")}
    }

    private fun compactExpression(source:String, from:Int=0, to:Int=source.length):String {
        val tree=Parser(source).parse()
        // -(a/b) and -a/b have the same value, even though the sign's AST scope differs.
        fun signed(value:String,arg:Expr):Expr = if(arg.kind=="binary" && arg.value=="/")
            Expr("binary","/",listOf(signed(value,arg.args[0]),arg.args[1]))
            else Expr("unary",value,listOf(arg))
        fun shape(node:Expr):Expr {
            if(node.kind=="group")return shape(node.args[0])
            val args=node.args.map(::shape)
            return if(node.kind=="unary" && node.value in setOf("+","-"))signed(node.value,args[0])
                else Expr(node.kind,node.value,args)
        }
        val expected=shape(tree)
        val removed=mutableSetOf<Int>()
        var result=source
        // Remove only parentheses whose absence preserves the complete parsed expression.
        for(group in tree.nodes().filter {it.kind=="group" && it.start>=from && it.end<=to}.sortedByDescending {it.start}) {
            removed.add(group.start);removed.add(group.end-1)
            val candidate=source.filterIndexed {index,_->index !in removed}
            if(runCatching {shape(Parser(candidate).parse())==expected}.getOrDefault(false))result=candidate
            else {removed.remove(group.start);removed.remove(group.end-1)}
        }
        return result
    }

    /** A limit applies to the remaining expression within its enclosing group. */
    private fun limitExpressionEnd(source:String,from:Int):Int {
        var index=from
        var depth=0
        while(index<source.length) {
            val c=source[index]
            if(depth==0 && (c in ")]},=<>" || scopeEnd.containsMatchIn(source.substring(index))))break
            if(c in "([{")depth++
            else if(c in ")]}")depth--
            index++
        }
        return index
    }

    private fun logOperand(source:String):String {
        var converted=convertBody(source)
        // The call's comma/closing parenthesis already delimits each operand.
        while(Parser(converted).parse().kind=="group")converted=converted.substring(1,converted.length-1)
        return converted
    }

    private fun skipSpacing(source:String,from:Int):Int {
        var index=from
        while(index<source.length) {
            if(source[index].isWhitespace())index++
            else if(source[index]=='\\' && source.getOrNull(index+1) in listOf(',', ';', '!', ' '))index+=2
            else break
        }
        return index
    }

    /** Read one logarithm base/argument before whitespace is removed. */
    private fun argument(source:String,from:Int,singleToken:Boolean=false):Pair<String,Int> {
        val start=skipSpacing(source,from)
        var index=start
        when(val c=source.getOrNull(index)) {
            '{','(' -> index=group(source,index,c,if(c=='{')'}' else ')').second
            '\\' -> {
                val match=commandPattern.find(source,index)?.takeIf {it.range.first==index}
                    ?: error("Expected LaTeX argument")
                val command=match.groupValues[1]
                index=match.range.last+1
                when(command) {
                    "boxed" -> index=group(source,index).second
                    "frac","dfrac","tfrac","binom" -> {
                        index=group(source,index).second
                        index=group(source,index).second
                    }
                    "sqrt" -> {
                        index=skipSpacing(source,index)
                        if(source.getOrNull(index)=='[')index=group(source,index,'[',']').second
                        index=group(source,index).second
                    }
                    "left" -> {
                        index=skipSpacing(source,index)
                        val open=source.getOrNull(index)
                        require(open=='(' || open=='[') {"Expected LaTeX fence"}
                        index=group(source,index,open,if(open=='(')')' else ']').second
                    }
                    "log" -> {
                        index=skipSpacing(source,index)
                        if(source.getOrNull(index)=='_')index=argument(source,index+1,true).second
                        index=argument(source,index).second
                    }
                    in functions -> {
                        index=skipSpacing(source,index)
                        if(source.getOrNull(index)=='^')index=argument(source,index+1,true).second
                        index=argument(source,index).second
                    }
                }
            }
            else -> {
                require(c!=null && (c.isLetterOrDigit() || c=='.')) {"Expected LaTeX argument"}
                index++
                if(!singleToken) {
                    if(c.isDigit() || c=='.') {
                        while(source.getOrNull(index)?.let {it.isDigit() || it=='.'}==true)index++
                        while(source.getOrNull(index)?.isLetterOrDigit()==true)index++
                    }
                    else while(source.getOrNull(index)?.isLetterOrDigit()==true)index++
                }
            }
        }
        if(!singleToken) {
            val power=skipSpacing(source,index)
            if(source.getOrNull(power)=='^')index=argument(source,power+1,true).second
        }
        return source.substring(start,index) to index
    }

    private fun group(source:String,from:Int,open:Char='{',close:Char='}'):Pair<String,Int> {
        var index=from
        while(index<source.length && source[index].isWhitespace())index++
        require(source.getOrNull(index)==open) { "Expected LaTeX group" }
        val start=++index
        var depth=1
        var braces=0
        while(index<source.length && depth>0) {
            val character=source[index]
            if(open=='[' && character=='{')braces++
            else if(open=='[' && character=='}') {require(braces>0);braces--}
            else if(braces==0)when(character) {open -> depth++;close -> depth--}
            index++
        }
        require(depth==0) { "Unclosed LaTeX group" }
        return source.substring(start,index-1) to index
    }
}
