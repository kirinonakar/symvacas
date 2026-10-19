package com.kirinonakar.symvacas.ui

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import com.kirinonakar.symvacas.math.*
import org.json.JSONObject

internal data class SurfaceSceneRequest(val data:JSONObject?,val bounds:SurfaceBounds,val rotation:Float,val elevation:Float,val mode:String,val opacity:Float,val rainbow:Boolean,val palette:List<Color>,val visible:List<Boolean>,val source:String,val kind:String)
internal data class SurfaceScene(val request:SurfaceSceneRequest,val groups:List<SurfaceGeometry>,val prepared:PreparedSurface,val projection:SurfaceProjection,val faces:List<SurfaceFace>,val batches:List<SurfaceVertexBatch>,val curves:List<List<DoubleArray?>>,val edges:List<List<Pair<DoubleArray,DoubleArray>>>)

/** One conflated worker owns this cache. Completed frames remain drawable while
 * the next frame is prepared; animation never cancels a half-built frame. */
internal class SurfaceSceneBuilder {
    private var previous:SurfaceScene?=null
    fun build(request:SurfaceSceneRequest):SurfaceScene {
        val old=previous;val data=request.data
        val groups=if(old!=null&&old.request.data===data)old.groups else {
            val surfaces=data?.optJSONArray("surfaces")
            val sources=if(surfaces==null)listOfNotNull(data) else (0 until surfaces.length()).map {surfaces.getJSONObject(it)}
            sources.map(::readSurfaceGeometry)
        }
        val curves=if(old!=null&&old.request.data===data)old.curves else {
            val source=data?.optJSONArray("spaceCurves")
            (0 until (source?.length() ?: 0)).map {i->
                val curve=source!!.getJSONArray(i)
                (0 until curve.length()).map {k->curve.optJSONArray(k)?.let {p->doubleArrayOf(p.optDouble(0),p.optDouble(1),p.optDouble(2)).takeIf {it.all(Double::isFinite)}}}
            }
        }
        val bounds=request.bounds
        val prepared=if(old!=null&&old.groups===groups&&old.request.bounds==bounds&&old.request.visible==request.visible)old.prepared else {
            val combined=SurfaceMesh.combine(groups.map {SurfaceMesh.prepare(it.mesh,bounds,it.triangles,it.normals,it.convex)})
            combined.copy(faces=combined.faces.filter {request.visible.getOrElse(it.group){true}})
        }
        val projection=if(old!=null&&old.request.bounds==bounds&&old.request.rotation==request.rotation&&old.request.elevation==request.elevation)old.projection else SurfaceProjection(bounds,request.rotation.toDouble(),request.elevation.toDouble())
        val faces=if(request.mode=="wireframe")emptyList() else if(old!=null&&old.request.mode!="wireframe"&&old.prepared===prepared&&old.projection===projection&&(old.request.opacity<1f)==(request.opacity<1f))old.faces else SurfaceMesh.project(prepared,projection,request.opacity<1f,withLighting=false)
        val batches=if(old!=null&&old.faces===faces&&old.request.palette==request.palette&&old.request.opacity==request.opacity&&old.request.rainbow==request.rainbow)old.batches else SurfaceMesh.colorBatches(faces,request.palette.map {it.toArgb()}.toIntArray(),bounds,request.opacity.toDouble(),request.rainbow)
        val edges=if(request.mode!="wireframe")groups.map {emptyList()} else if(old!=null&&old.groups===groups&&old.request.mode=="wireframe")old.edges else groups.map {group->
            val ids=java.util.IdentityHashMap<DoubleArray,Int>();val seen=mutableSetOf<Long>();val result=mutableListOf<Pair<DoubleArray,DoubleArray>>()
            for(triangle in group.triangles)for(i in 0..2) {
                val a=triangle[i];val b=triangle[(i+1)%3];val ai=ids.getOrPut(a){ids.size};val bi=ids.getOrPut(b){ids.size}
                val key=(minOf(ai,bi).toLong() shl 32) or maxOf(ai,bi).toLong()
                if(seen.add(key))result.add(a to b)
            }
            result
        }
        return SurfaceScene(request,groups,prepared,projection,faces,batches,curves,edges).also {previous=it}
    }
}

internal data class SurfaceGeometry(val mesh:List<List<DoubleArray?>>,val triangles:List<List<DoubleArray>>,val normals:List<List<DoubleArray>>,val convex:Boolean)
internal fun readSurfaceGeometry(data:JSONObject):SurfaceGeometry {
    data.optJSONObject("surfaceGrid")?.let {grid->
        val x=grid.getJSONArray("x");val y=grid.getJSONArray("y");val z=grid.getJSONArray("z")
        val xs=DoubleArray(x.length()) {x.getDouble(it)}
        val mesh=List(y.length()) {row->val yy=y.getDouble(row);val values=z.getJSONArray(row)
            List<DoubleArray?>(xs.size) {col->if(values.isNull(col))null else doubleArrayOf(xs[col],yy,values.getDouble(col))}
        }
        return SurfaceGeometry(mesh,emptyList(),emptyList(),false)
    }
    data.optJSONArray("surfaceRings")?.let {rings->
        val (faces,normals)=SurfaceMesh.radialGeometry((0 until rings.length()).map {i->val ring=rings.getJSONArray(i);DoubleArray(4) {ring.getDouble(it)}})
        return SurfaceGeometry(emptyList(),faces,normals,false)
    }
    fun points(name:String):List<DoubleArray?> {
        val values=data.optJSONArray(name)
        return (0 until (values?.length() ?: 0)).map {i->values!!.optJSONArray(i)?.let {p->
                if(p.isNull(2))null else doubleArrayOf(p.optDouble(0),p.optDouble(1),p.optDouble(2)).takeIf {it.all(Double::isFinite)}
        }}
    }
    val rows=data.optJSONArray("surface")
    val mesh=(0 until (rows?.length() ?: 0)).map {i->
        val row=rows!!.getJSONArray(i)
        (0 until row.length()).map {k->row.optJSONArray(k)?.let {p->if(p.isNull(2))null else doubleArrayOf(p.optDouble(0),p.optDouble(1),p.optDouble(2)).takeIf {it.all(Double::isFinite)}}}
    }
    val vertices=points("surfaceVertices");val normals=points("surfaceNormals")
    val indices=data.optJSONArray("surfaceTriangles")
    val faces=(0 until (indices?.length() ?: 0)).mapNotNull {i->
        val face=indices!!.getJSONArray(i);val ids=(0 until face.length()).map {face.optInt(it,-1)}
        ids.takeIf {it.size==3&&it.all {id->vertices.getOrNull(id)!=null}}
    }
    return SurfaceGeometry(mesh,faces.map {face->face.map {vertices[it]!!}},faces.map {face->face.mapNotNull {normals.getOrNull(it)}},data.optBoolean("convexSurface",false))
}

