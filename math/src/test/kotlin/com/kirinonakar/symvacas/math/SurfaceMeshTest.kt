package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class SurfaceMeshTest {
    @Test fun rasterVertexLightingMatchesVectorGradientsAcrossClippingAndRotation() {
        val mesh=List(5) {r->List<DoubleArray?>(5) {c->doubleArrayOf(c-2.0,r-2.0,(c-2.0)*(c-2.0)+(r-2.0)*(r-2.0))}}
        val bounds=SurfaceBounds(-1.7,1.7,-1.7,1.7,-1.0,3.0)
        val prepared=SurfaceMesh.prepare(mesh,bounds)
        for(rotation in listOf(0.0,35.0,120.0))for(opacity in listOf(1.0,.4))for(rainbow in listOf(false,true)) {
            val projection=SurfaceProjection(bounds,rotation,32.0)
            val original=SurfaceMesh.colorBatches(SurfaceMesh.project(prepared,projection,opacity<1),intArrayOf(0xff007b68.toInt()),bounds,opacity,rainbow)
            val fast=SurfaceMesh.colorBatches(SurfaceMesh.project(prepared,projection,opacity<1,false),intArrayOf(0xff007b68.toInt()),bounds,opacity,rainbow)
            assertEquals(original.flatMap {it.positions.toList()},fast.flatMap {it.positions.toList()})
            val before=original.flatMap {it.colors.toList()};val after=fast.flatMap {it.colors.toList()}
            assertEquals(before.size,after.size)
            for(i in before.indices)for(shift in listOf(0,8,16,24))assertTrue(kotlin.math.abs(((before[i] ushr shift)and 255)-((after[i] ushr shift)and 255))<=1)
        }
    }
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
    @Test fun radialTopologyHasNoInternalHolesAndColorsUseZ() {
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
        SurfaceColors.stops.forEachIndexed {i,color->assertEquals(color,SurfaceColors.rainbow(i/5.0))}
        assertEquals(SurfaceColors.stops.first(),SurfaceColors.rainbow(-2.0))
        assertEquals(SurfaceColors.stops.last(),SurfaceColors.rainbow(2.0))
    }
    @Test fun gridFacesShareLightingAndKeepUndefinedHoles() {
        val mesh=List(5) {r->MutableList<DoubleArray?>(5) {c->doubleArrayOf(c-2.0,r-2.0,(c-2.0)*(c-2.0)+(r-2.0)*(r-2.0))}}
        val bounds=SurfaceBounds(-2.0,2.0,-2.0,2.0,-1.0,3.0)
        val prepared=SurfaceMesh.prepare(mesh,bounds)
        val levels=java.util.IdentityHashMap<DoubleArray,Double>()
        for(face in prepared.faces) {
            assertEquals(3,face.levels!!.size)
            face.source.forEachIndexed {i,p->
                levels[p]?.let {assertEquals(it,face.levels[i],0.0)}
                levels[p]=face.levels[i]
            }
        }
        assertTrue(levels.size>10)
        for(rotation in listOf(0.0,35.0,90.0)) {
            val faces=SurfaceMesh.project(prepared,SurfaceProjection(bounds,rotation,32.0))
            assertTrue(faces.any {it.lighting!=null})
            assertTrue(faces.all {it.projected.all {p->p.all(Double::isFinite)}})
        }
        mesh[2][2]=null
        val hole=SurfaceMesh.prepare(mesh,bounds.copy(zmax=8.0))
        assertEquals(24,hole.faces.size)
        assertTrue(hole.faces.all {it.levels!!.all(Double::isFinite)})
    }
}
