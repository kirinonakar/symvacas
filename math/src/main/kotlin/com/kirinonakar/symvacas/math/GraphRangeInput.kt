package com.kirinonakar.symvacas.math

import kotlin.math.*

data class GraphRangeInput(val value: Double, val tree: Expr? = null)

/** Read a constant real expression for a graph range or slider position. */
fun parseGraphRangeInput(source: String): GraphRangeInput? {
    source.toDoubleOrNull()?.let { return if (it.isFinite()) GraphRangeInput(it) else null }
    val tree = try {
        Parser(LatexInput.convert(source) ?: source).parse()
    } catch (_: SyntaxException) {
        return null
    }
    val value = rangeValue(tree)
    return if (value.isFinite()) GraphRangeInput(value, tree) else null
}

fun graphRangeNumber(source: String): Double? = parseGraphRangeInput(source)?.value

private fun rangeValue(tree: Expr): Double {
    val op = tree.value
    if (tree.kind == "number") return op.toDoubleOrNull() ?: Double.NaN
    if (tree.kind == "symbol") return when (op) {
        "pi" -> PI
        "e" -> E
        else -> Double.NaN
    }
    val args = tree.args.map(::rangeValue)
    if (args.any { !it.isFinite() }) return Double.NaN
    val a = args.getOrNull(0) ?: Double.NaN
    val b = args.getOrNull(1) ?: Double.NaN
    return when (tree.kind) {
        "group" -> a
        "unary" -> if (op == "-") -a else a
        "binary" -> when (op) {
            "+" -> a + b
            "-" -> a - b
            "*" -> a * b
            "/" -> a / b
            "^" -> a.pow(b)
            else -> Double.NaN
        }
        "call" -> when {
            op == "log" && args.size == 1 -> log10(a)
            op == "log" && args.size == 2 && b > 0 && b != 1.0 -> log(a, b)
            args.size != 1 -> Double.NaN
            else -> when (op) {
                "abs" -> abs(a)
                "sqrt" -> sqrt(a)
                "cbrt" -> cbrt(a)
                "exp" -> exp(a)
                "ln" -> ln(a)
                "sin" -> sin(a)
                "cos" -> cos(a)
                "tan" -> tan(a)
                "asin" -> asin(a)
                "acos" -> acos(a)
                "atan" -> atan(a)
                else -> Double.NaN
            }
        }
        else -> Double.NaN
    }
}
