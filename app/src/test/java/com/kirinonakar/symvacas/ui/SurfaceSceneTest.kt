package com.kirinonakar.symvacas.ui

import androidx.compose.ui.graphics.Color
import com.kirinonakar.symvacas.math.SurfaceBounds
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SurfaceSceneTest {
    private fun request(data:JSONObject)=SurfaceSceneRequest(data,SurfaceBounds(-1.0,1.0,-1.0,1.0,-2.0,2.0),35f,32f,"surface",1f,true,listOf(Color(0xff007b68)),listOf(true),"x+y","surface")

    @Test fun compactGridRendersTheSamePositionsAndColorsAsTheFullGrid() {
        val full=JSONObject("""{"surface":[[[-1,-1,-2],[0,-1,-1],[1,-1,0]],[[-1,0,-1],[0,0,0],[1,0,1]],[[-1,1,0],[0,1,1],[1,1,2]]]}""")
        val compact=JSONObject("""{"surface":[],"surfaceGrid":{"x":[-1,0,1],"y":[-1,0,1],"z":[[-2,-1,0],[-1,0,1],[0,1,2]]}}""")
        val a=SurfaceSceneBuilder().build(request(full));val b=SurfaceSceneBuilder().build(request(compact))
        assertEquals(8,b.faces.size)
        assertEquals(a.batches.flatMap {it.positions.toList()},b.batches.flatMap {it.positions.toList()})
        assertEquals(a.batches.flatMap {it.colors.toList()},b.batches.flatMap {it.colors.toList()})
        val builder=SurfaceSceneBuilder();val first=builder.build(request(compact))
        val color=builder.build(first.request.copy(rainbow=false))
        assertSame(first.groups,color.groups);assertSame(first.prepared,color.prepared);assertSame(first.faces,color.faces)
        assertNotSame(first.batches,color.batches)
        val camera=builder.build(color.request.copy(rotation=75f))
        assertSame(color.prepared,camera.prepared);assertNotSame(color.faces,camera.faces)
        val hidden=builder.build(camera.request.copy(visible=listOf(false)))
        assertTrue(hidden.faces.isEmpty());assertTrue(hidden.batches.isEmpty())
    }
}
