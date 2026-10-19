package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.ui.theme.InstrumentColors

@Composable internal fun GraphInputHelp(kind: String, c: InstrumentColors) {
    // Each category owns its syntax, examples, and required settings.
    val entries = when (kind) {
        "parametric" -> listOf(
            false to "Enter one [x(t),y(t)] pair per line.",
            true to "[cos(t),sin(t)]",
            false to "Set the t interval in Range. Angles are in radians."
        )
        "polar" -> listOf(
            false to "Enter one radius expression per line; r= is optional.",
            true to "1+cos(t)",
            false to "Use t for the angle in radians. Set the θ interval in Range."
        )
        "sequence" -> listOf(
            false to "Enter one rule per line using n. For a recurrence, use u(n-1).",
            true to "u(n-1)+1",
            false to "For recurrences, enter initial values from n=0, separated by commas."
        )
        "surface" -> listOf(
            false to "Enter z=f(x,y) or F(x,y,z)=0, one surface per line (up to 5).",
            true to "z=sin(x)*cos(y)\nx^2+y^2+z^2=9",
            false to "Set x, y and z bounds in Range. Automatic z range uses the y bounds for implicit surfaces.",
            false to "Parametric surfaces: enter [x(u,v),y(u,v),z(u,v)]. Set u and v intervals in Range (default 0 to 2π).",
            true to "[(2+cos(v))*cos(u),(2+cos(v))*sin(u),sin(v)]",
            false to "Define helpers inside one list, followed by z=... or x=...,y=...,z=.... Free t creates an animation slider.",
            true to "[R=2+0.35*sin(6*u-3*t),x=(R+cos(v))*cos(u),y=(R+cos(v))*sin(u),z=sin(v)]",
            true to "[r1=sqrt((x-2)^2+y^2),r2=sqrt((x+2)^2+y^2),z=sin(4*r1-5*t)/(1+0.2*r1)+sin(4*r2-5*t)/(1+0.2*r2)]"
        )
        "space" -> listOf(
            false to "Enter one [x(t),y(t),z(t)] triple per line (up to 5).",
            true to "[cos(t),sin(t),t/4]",
            false to "Set the t interval in Range. Angles are in radians.",
            false to "Append {0<t<1} to restrict t. Add k=[...] in the same braces to draw one curve for each k; other parameters remain sliders.",
            true to "[(1-2*t)*cos(k*pi/2+a),(1-2*t)*sin(k*pi/2+a),k*pi/8] {0<t<1, k=[0,0.1,0.2,0.3,0.4,0.5]}"
        )
        "differential" -> listOf(
            false to "Enter one derivative rule f(t,y) for dy/dt=f(t,y).",
            true to "-y",
            false to "Enter t₀ and initial y values, separated by commas. Set a t interval containing t₀ in Range."
        )
        else -> listOf(
            false to "Enter one expression per line. Functions, implicit equations, polar curves and parametric pairs can be combined.",
            true to "y=x^2\nx^2+y^2=9\nr=2*cos(3*θ)\n[cos(t),sin(t)]",
            false to "For parametric or polar curves, set the t or θ interval in Range. Angles are in radians.",
            false to "Inequalities shade regions. Separate multiple conditions with commas. < and > use dashed boundaries; <= and >= use solid boundaries.",
            true to "x^2+y^2<4\n-1<x<1, -1<y<x",
            false to "Piecewise: {condition:value,...,default}. The first match wins; omit default to leave other values undefined.",
            true to "f(x)={x<0:x^2,x>=0:2*x}",
            true to "f(x)={x<0:x^2,3}",
            false to "Here, 3 is the default: x<0 gives x²; x>=0 gives 3.",
            false to "Append {condition} to restrict the domain.",
            true to "y=x^2 {0<=x<=2}"
        )
    }
    SelectionContainer {
        Column(Modifier.fillMaxWidth().padding(horizontal=14.dp).testTag("graph-input-help"), verticalArrangement=Arrangement.spacedBy(6.dp)) {
            entries.forEach { (example, text) ->
                Text(if(example) text else tr(text), fontSize=12.sp, color=if(example) c.ink else c.muted)
            }
        }
    }
}
