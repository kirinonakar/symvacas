package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class SurfaceMeshTest {
    @Test fun nativeVertexBatchesOwnContiguousTriangleAndColorBuffers() {
        for(count in listOf(0,3,32766,32769,65535)) {
            val positions=FloatArray(count*2) {it.toFloat()};val colors=IntArray(count) {it}
            val batches=SurfaceMesh.vertexBatches(positions,colors)
            assertEquals(positions.toList(),batches.flatMap {it.positions.toList()})
            assertEquals(colors.toList(),batches.flatMap {it.colors.toList()})
            for(batch in batches) {
                assertTrue(batch.positions.size<=65532)
                assertEquals(0,batch.positions.size%6)
                assertEquals(batch.positions.size/2,batch.colors.size)
            }
        }
        assertThrows(IllegalArgumentException::class.java){SurfaceMesh.vertexBatches(FloatArray(8),IntArray(4))}
    }
    @Test fun radialTopologyHasNoInternalHoles() {
        val (faces,normals)=SurfaceMesh.radialGeometry(listOf(doubleArrayOf(0.0,1.0,0.0,1.0),doubleArrayOf(1.0,.5,-1.0,12.0),doubleArrayOf(2.0,0.0,0.0,20.0),doubleArrayOf(3.0,-.2,0.0,24.0)))
        assertEquals(88,faces.size);assertEquals(faces.size,normals.size)
        val edges=mutableMapOf<String,Int>();var area=0.0
        for(face in faces) {
            val (a,b,c)=face;val cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            assertTrue(cross>0);area+=cross/2
            for(i in 0..2) {
                val key=listOf(face[i].joinToString(","),face[(i+1)%3].joinToString(",")).sorted().joinToString("|")
                edges[key]=(edges[key] ?: 0)+1
            }
        }
        assertEquals(24*9*kotlin.math.sin(2*kotlin.math.PI/24)/2,area,1e-10)
        assertEquals(24,edges.values.count {it==1});assertTrue(edges.values.all {it==1||it==2})
    }
}
