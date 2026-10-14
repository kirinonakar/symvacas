package com.kirinonakar.symvacas.math

import org.junit.Test
import org.junit.Assert.*

class SurfaceSectionTest {
    @Test fun sectionsUseClippedMeshCoordinatesAndKeepSurfaceIdentity() {
        val bounds=SurfaceBounds(-2.0,2.0,-2.0,2.0,-2.0,2.0)
        val triangle=listOf(doubleArrayOf(0.0,0.0,-1.0),doubleArrayOf(2.0,0.0,1.0),doubleArrayOf(0.0,2.0,1.0))
        val prepared=SurfaceMesh.prepare(emptyList(),bounds,listOf(triangle))
        val faces=prepared.faces.map {it.copy(group=2)}
        val sections=SurfaceMesh.sectionSegments(faces,0.0)
        assertEquals(1,sections.size);assertEquals(2,sections[0].first)
        assertArrayEquals(doubleArrayOf(1.0,0.0,0.0),sections[0].second.first,1e-12)
        assertArrayEquals(doubleArrayOf(0.0,1.0,0.0),sections[0].second.second,1e-12)
        assertTrue(SurfaceMesh.sectionSegments(faces,2.0).isEmpty())
        assertTrue(SurfaceMesh.sectionSegments(faces,Double.NaN).isEmpty())
    }
    @Test fun xAndYSectionsPreserveCoordinatesAndPlaneDirection() {
        val bounds=SurfaceBounds(-4.0,5.0,-6.0,7.0,-8.0,9.0)
        val triangle=listOf(doubleArrayOf(0.0,0.0,-1.0),doubleArrayOf(2.0,0.0,1.0),doubleArrayOf(0.0,2.0,1.0))
        val expected=listOf(doubleArrayOf(1.0,0.0,0.0),doubleArrayOf(0.0,1.0,0.0))
        for(axis in 0..2) {
            fun permute(point:DoubleArray)=point.copyOf().apply {val value=this[axis];this[axis]=this[2];this[2]=value}
            val prepared=SurfaceMesh.prepare(emptyList(),bounds,listOf(triangle.map(::permute)))
            val faces=prepared.faces.map {it.copy(group=3)}
            val sections=SurfaceMesh.sectionSegments(faces,0.0,axis)
            assertEquals(1,sections.size);assertEquals(3,sections[0].first)
            assertArrayEquals(permute(expected[0]),sections[0].second.first,1e-12)
            assertArrayEquals(permute(expected[1]),sections[0].second.second,1e-12)
            assertTrue(SurfaceMesh.sectionSegments(faces,2.0,axis).isEmpty())
            val plane=SurfaceMesh.sectionPlane(bounds,.25,axis)
            assertEquals(4,plane.size);plane.forEach {assertEquals(.25,it[axis],1e-12)}
            for(other in (0..2).filter {it!=axis})assertEquals(setOf(bounds.limits[other].first,bounds.limits[other].second),plane.map {it[other]}.toSet())
        }
    }
    @Test fun transparentClosedSurfacesKeepTheirBackFacesInDepthOrder() {
        val bounds=SurfaceBounds(-2.0,2.0,-2.0,2.0,-2.0,2.0)
        val triangles=listOf(listOf(doubleArrayOf(0.0,0.0,0.0),doubleArrayOf(1.0,0.0,0.0),doubleArrayOf(0.0,1.0,0.0)),
            listOf(doubleArrayOf(0.0,0.0,1.0),doubleArrayOf(0.0,1.0,1.0),doubleArrayOf(1.0,0.0,1.0)))
        val mesh=SurfaceMesh.prepare(emptyList(),bounds,triangles,convex=true)
        val projection=SurfaceProjection(bounds,35.0,32.0)
        assertEquals(1,SurfaceMesh.project(mesh,projection).size)
        val transparent=SurfaceMesh.project(mesh,projection,transparent=true)
        assertEquals(2,transparent.size);assertTrue(transparent[0].depth<=transparent[1].depth)
    }
}
