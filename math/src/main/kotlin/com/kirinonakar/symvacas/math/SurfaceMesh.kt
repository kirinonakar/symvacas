package com.kirinonakar.symvacas.math

import kotlin.math.*

data class SurfaceBounds(val xmin:Double,val xmax:Double,val ymin:Double,val ymax:Double,val zmin:Double,val zmax:Double) {
    val limits=listOf(xmin to xmax,ymin to ymax,zmin to zmax)
}
data class SurfaceLighting(val start:DoubleArray,val end:DoubleArray,val min:Double,val max:Double)
data class SurfaceFace(val points:List<DoubleArray>,val depth:Double,val height:Double,val light:Double,val lighting:SurfaceLighting?=null,val projected:List<DoubleArray> = emptyList(),val front:Boolean=false,val brightness:Double?=null,val group:Int=0,val vertexLevels:List<Double>?=null)
data class PreparedSurfaceFace(val points:List<DoubleArray>,val source:List<DoubleArray>,val normal:DoubleArray,val levels:List<Double>?,val height:Double,val light:Double,val group:Int=0,val closed:Boolean?=null)
data class PreparedSurface(val faces:List<PreparedSurfaceFace>,val convex:Boolean,val closed:Boolean)
data class SurfaceVertexBatch(val positions:FloatArray,val colors:IntArray)

class SurfaceProjection(val bounds:SurfaceBounds,rotation:Double,elevation:Double) {
    private val theta=Math.toRadians(rotation)
    private val tilt=Math.toRadians(elevation)
    private val ct=cos(theta);private val st=sin(theta);private val ce=cos(tilt);private val se=sin(tilt)
    val direction=doubleArrayOf(-st*ce,-ct*ce,se)
    fun normalize(point:DoubleArray)=DoubleArray(3) { i->val (low,high)=bounds.limits[i];2*(point[i]-low)/(high-low)-1 }
    // Screen x, screen y, and depth increasing toward the camera.
    fun project(point:DoubleArray):DoubleArray {
        val p=normalize(point)
        val horizontal=p[0]*ct-p[1]*st
        val depth=p[0]*st+p[1]*ct
        return doubleArrayOf(horizontal,-depth*se-p[2]*ce,p[2]*se-depth*ce)
    }
}

object SurfaceMesh {
    fun colorBatches(faces:List<SurfaceFace>,palette:IntArray,bounds:SurfaceBounds,opacity:Double=1.0,rainbow:Boolean=false):List<SurfaceVertexBatch> {
        val count=faces.sumOf {(it.projected.size-2).coerceAtLeast(0)*3}
        val positions=FloatArray(count*2);val colors=IntArray(count);var index=0
        val cachedColors=Array(palette.size) {java.util.IdentityHashMap<DoubleArray,Int>()}
        val alpha=(opacity*255).roundToInt() shl 24
        for(face in faces) {
          val group=face.group%palette.size
          fun color(k:Int):Int {
            val point=face.points[k]
            if(face.vertexLevels!=null)cachedColors[group][point]?.let {return it}
            val base=if(rainbow)SurfaceColors.rainbow((point[2]-bounds.zmin)/(bounds.zmax-bounds.zmin)) else palette[group]
            val brightness=(face.vertexLevels?.get(k) ?: SurfaceColors.gradientValue(face.lighting,face.projected[k],face.brightness ?: ((.65+.35*face.height)*face.light))).coerceIn(0.0,1.0)
            val result=alpha or ((((base shr 16)and 255)*brightness).roundToInt() shl 16) or ((((base shr 8)and 255)*brightness).roundToInt() shl 8) or (((base and 255)*brightness).roundToInt())
            if(face.vertexLevels!=null)cachedColors[group][point]=result
            return result
          }
          fun vertex(k:Int) {
            val p=face.projected[k]
            positions[index*2]=p[0].toFloat();positions[index*2+1]=p[1].toFloat()
            colors[index]=color(k);index++
          }
          for(i in 1 until face.projected.lastIndex){vertex(0);vertex(i);vertex(i+1)}
        }
        return vertexBatches(positions,colors)
    }
    fun vertexBatches(positions:FloatArray,colors:IntArray):List<SurfaceVertexBatch> {
        require(positions.size%6==0&&colors.size==positions.size/2) {"Surface triangles need three position/color pairs"}
        if(positions.isEmpty())return emptyList()
        // Canvas JNI adds vertOffset to its nullable texture pointer. Nonzero
        // offsets with texs=null can crash in SkVertices::MakeCopy, so every
        // draw owns a contiguous zero-offset buffer. Split only between faces.
        if(positions.size<=65532)return listOf(SurfaceVertexBatch(positions,colors))
        return (positions.indices step 65532).map {offset->
            val end=minOf(offset+65532,positions.size)
            SurfaceVertexBatch(positions.copyOfRange(offset,end),colors.copyOfRange(offset/2,end/2))
        }
    }
    private val circles=java.util.concurrent.ConcurrentHashMap<Int,List<Pair<Double,Double>>>()
    fun radialGeometry(rings:List<DoubleArray>):Pair<List<List<DoubleArray>>,List<List<DoubleArray>>> {
        val vertices=mutableListOf<DoubleArray>();val normals=mutableListOf<DoubleArray>();val rows=mutableListOf<List<Int>>()
        for(ring in rings) {
            val (radius,height,slope)=ring;val count=ring[3].toInt()
            val circle=circles.getOrPut(count) {List(count) {cos(2*PI*it/count) to sin(2*PI*it/count)}}
            rows.add(circle.map {(x,y)->
                val index=vertices.size;vertices.add(doubleArrayOf(radius*x,radius*y,height));normals.add(doubleArrayOf(-slope*x,-slope*y,1.0));index
            })
        }
        val faces=mutableListOf<List<DoubleArray>>();val lights=mutableListOf<List<DoubleArray>>()
        fun face(a:Int,b:Int,c:Int) {faces.add(listOf(vertices[a],vertices[b],vertices[c]));lights.add(listOf(normals[a],normals[b],normals[c]))}
        for(ring in 1 until rows.size) {
            val inner=rows[ring-1];val outer=rows[ring]
            if(inner.size==1) {for(j in outer.indices)face(inner[0],outer[j],outer[(j+1)%outer.size]);continue}
            var i=0;var j=0
            while(i<inner.size||j<outer.size) {
                val a=inner[i%inner.size];val b=outer[j%outer.size]
                if((i+1)*outer.size<=(j+1)*inner.size&&i<inner.size) {face(a,b,inner[(i+1)%inner.size]);i++}
                else {face(a,b,outer[(j+1)%outer.size]);j++}
            }
        }
        return faces to lights
    }
    fun sampleCount(xmin:Double,xmax:Double,ymin:Double,ymax:Double,requested:Int=26,automatic:Boolean=true,zoom:Double=1.0,implicit:Boolean=false):Int {
        val maximum=if(implicit)32 else 96
        if(!automatic)return requested.coerceIn(12,maximum)
        return ceil(max(26.0,max(xmax-xmin,ymax-ymin)*8)*sqrt(zoom)).coerceIn(12.0,maximum.toDouble()).toInt()
    }
    fun animationSampleCount(density:Int,implicit:Boolean)=if(implicit)minOf(density,16) else density
    fun zRange(low:Double,high:Double):Pair<Double,Double> {
        if(!low.isFinite()||!high.isFinite())return -1.0 to 1.0
        if(high>low)return low to high
        val padding=max(1.0,abs(low)*.1)
        return low-padding to low+padding
    }
    private fun finite(point:DoubleArray?)=point!=null&&point.size==3&&point.all(Double::isFinite)
    private fun interpolate(a:DoubleArray,b:DoubleArray,t:Double)=DoubleArray(3) {a[it]+(b[it]-a[it])*t}
    fun clipSegment(a:DoubleArray?,b:DoubleArray?,bounds:SurfaceBounds):Pair<DoubleArray,DoubleArray>? {
        if(!finite(a)||!finite(b))return null
        a!!;b!!
        var start=0.0;var end=1.0
        for((axis,limit) in bounds.limits.withIndex()) {
            val (low,high)=limit;val delta=b[axis]-a[axis]
            if(delta==0.0) {if(a[axis]<low||a[axis]>high)return null;continue}
            val t1=(low-a[axis])/delta;val t2=(high-a[axis])/delta
            start=max(start,min(t1,t2));end=min(end,max(t1,t2))
            if(start>=end)return null
        }
        return interpolate(a,b,start) to interpolate(a,b,end)
    }
    fun clipPolygon(points:List<DoubleArray>,bounds:SurfaceBounds):List<DoubleArray> {
        if(!points.all(::finite))return emptyList()
        if(points.all {p->bounds.limits.withIndex().all {(i,limit)->p[i]>=limit.first&&p[i]<=limit.second}})return points
        var polygon=points
        for((axis,limit) in bounds.limits.withIndex())for((edge,above) in listOf(limit.first to true,limit.second to false)) {
            if(polygon.isEmpty())return emptyList()
            val input=polygon;val output=mutableListOf<DoubleArray>()
            var a=input.last();var insideA=if(above)a[axis]>=edge else a[axis]<=edge
            for(b in input) {
                val insideB=if(above)b[axis]>=edge else b[axis]<=edge
                if(insideA!=insideB)output.add(interpolate(a,b,(edge-a[axis])/(b[axis]-a[axis])))
                if(insideB)output.add(b)
                a=b;insideA=insideB
            }
            polygon=output
        }
        return if(polygon.size>=3)polygon else emptyList()
    }
    fun lightingGradient(points:List<DoubleArray>,levels:List<Double>):SurfaceLighting? {
        val (p,a,b)=points;val dx1=a[0]-p[0];val dy1=a[1]-p[1];val dx2=b[0]-p[0];val dy2=b[1]-p[1]
        val determinant=dx1*dy2-dx2*dy1
        if(abs(determinant)<1e-14)return null
        val l1=levels[1]-levels[0];val l2=levels[2]-levels[0]
        val gx=(l1*dy2-l2*dy1)/determinant;val gy=(dx1*l2-dx2*l1)/determinant
        val length2=gx*gx+gy*gy;val low=levels.min();val high=levels.max()
        if(!length2.isFinite()||length2<1e-16||high-low<1e-7)return null
        val offset=(low-levels[0])/length2;val span=(high-low)/length2
        val start=doubleArrayOf(p[0]+gx*offset,p[1]+gy*offset)
        val end=doubleArrayOf(start[0]+gx*span,start[1]+gy*span)
        return if(start.all(Double::isFinite)&&end.all(Double::isFinite))SurfaceLighting(start,end,low,high) else null
    }
    fun prepare(mesh:List<List<DoubleArray?>>,bounds:SurfaceBounds,triangles:List<List<DoubleArray>> = emptyList(),triangleNormals:List<List<DoubleArray>> = emptyList(),convex:Boolean=false):PreparedSurface {
        val faces=mutableListOf<PreparedSurfaceFace>()
        val projection=SurfaceProjection(bounds,0.0,0.0)
        val normalized=java.util.IdentityHashMap<DoubleArray,DoubleArray>()
        val inside=java.util.IdentityHashMap<DoubleArray,Boolean>()
        fun normalize(point:DoubleArray)=normalized.getOrPut(point){
            inside[point]=point[0]>=bounds.xmin&&point[0]<=bounds.xmax&&point[1]>=bounds.ymin&&point[1]<=bounds.ymax&&point[2]>=bounds.zmin&&point[2]<=bounds.zmax
            projection.normalize(point)
        }
        val normalLights=java.util.IdentityHashMap<DoubleArray,Double>()
        fun normalLight(n:DoubleArray)=normalLights.getOrPut(n) {
            val x=n[0]*(bounds.xmax-bounds.xmin);val y=n[1]*(bounds.ymax-bounds.ymin);val z=n[2]*(bounds.zmax-bounds.zmin)
            val length=sqrt(x*x+y*y+z*z)
            if(length>0).35+.65*abs((x*-.4+y*-.5+z*.75)/(length*sqrt(.4*.4+.5*.5+.75*.75))) else Double.NaN
        }
        val input=triangles.toMutableList()
        // Share central-difference normals across grid faces, stopping at holes.
        val gridNormals=java.util.IdentityHashMap<DoubleArray,DoubleArray>()
        for(row in mesh.indices)for(col in mesh[row].indices) {
            val point=mesh[row][col]?.takeIf(::finite) ?: continue
            fun neighbor(r:Int,c:Int)=mesh.getOrNull(r)?.getOrNull(c)?.takeIf(::finite) ?: point
            val left=neighbor(row,col-1);val right=neighbor(row,col+1)
            val down=neighbor(row-1,col);val up=neighbor(row+1,col)
            val u=DoubleArray(3) {right[it]-left[it]};val v=DoubleArray(3) {up[it]-down[it]}
            gridNormals[point]=doubleArrayOf(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        }
        for(row in 0 until mesh.lastIndex)for(col in 0 until min(mesh[row].size,mesh[row+1].size)-1) {
            val cell=listOf(mesh[row][col],mesh[row][col+1],mesh[row+1][col+1],mesh[row+1][col])
            if(!cell.all(::finite))continue
            input.add(listOf(cell[0]!!,cell[1]!!,cell[2]!!));input.add(listOf(cell[0]!!,cell[2]!!,cell[3]!!))
        }
        val closed=convex&&input.all {triangle->triangle.all {p->finite(p)&&bounds.limits.withIndex().all {(i,limit)->p[i]>=limit.first&&p[i]<=limit.second}}}
        for((index,triangle) in input.withIndex()) {
                if(triangle.size!=3 || !triangle.all(::finite))continue
                val (a,b,c)=triangle.map(::normalize)
                val points=if(triangle.all {inside[it]==true})triangle else clipPolygon(triangle,bounds)
                if(points.isEmpty())continue
                val ux=b[0]-a[0];val uy=b[1]-a[1];val uz=b[2]-a[2];val vx=c[0]-a[0];val vy=c[1]-a[1];val vz=c[2]-a[2]
                val normal=doubleArrayOf(uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx)
                val length=sqrt(normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2]);if(length==0.0)continue
                val light=.35+.65*abs((normal[0]*-.4+normal[1]*-.5+normal[2]*.75)/(length*sqrt(.4*.4+.5*.5+.75*.75)))
                val normals=if(index<triangles.size)triangleNormals.getOrNull(index) else triangle.mapNotNull {gridNormals[it]}
                val levels=if(normals?.size==3 && normals.all {finite(it)&&normalLight(it).isFinite()}) {
                    if(convex) {
                        val average=DoubleArray(3) {axis->normals.sumOf {it[axis]}*(bounds.limits[axis].second-bounds.limits[axis].first)}
                        if(normal.indices.sumOf {normal[it]*average[it]}<0)for(i in normal.indices)normal[i]=-normal[i]
                    }
                    normals.mapIndexed {i,n->
                        (.65+.35*((triangle[i][2]-bounds.zmin)/(bounds.zmax-bounds.zmin)).coerceIn(0.0,1.0))*normalLight(n)
                    }
                } else null
                var height=0.0;for(p in points)height+=(p[2]-bounds.zmin)/(bounds.zmax-bounds.zmin)
                faces.add(PreparedSurfaceFace(points,triangle,normal,levels,height/points.size,light))
        }
        return PreparedSurface(faces,convex,closed)
    }
    fun sectionSegments(faces:List<PreparedSurfaceFace>,position:Double,axis:Int=2):List<Pair<Int,Pair<DoubleArray,DoubleArray>>> {
        if(!position.isFinite() || axis !in 0..2)return emptyList()
        val segments=mutableListOf<Pair<Int,Pair<DoubleArray,DoubleArray>>>()
        for(face in faces) {
            val points=face.points
            if(points.all {it[axis]==position}) {
                points.indices.forEach {i->segments.add(face.group to (points[i] to points[(i+1)%points.size]))}
                continue
            }
            val crossings=mutableListOf<DoubleArray>()
            for(i in points.indices) {
                val a=points[i];val b=points[(i+1)%points.size]
                if(a[axis]==position)crossings.add(a)
                if(a[axis]<position&&b[axis]>position || a[axis]>position&&b[axis]<position)crossings.add(interpolate(a,b,(position-a[axis])/(b[axis]-a[axis])))
            }
            val unique=mutableListOf<DoubleArray>()
            for(p in crossings)if(unique.none {q->p.indices.all {abs(p[it]-q[it])<1e-12}})unique.add(p)
            if(unique.size==2)segments.add(face.group to (unique[0] to unique[1]))
        }
        return segments
    }
    fun sectionPlane(bounds:SurfaceBounds,position:Double,axis:Int=2):List<DoubleArray> {
        if(!position.isFinite() || axis !in 0..2)return emptyList()
        val other=(0..2).filter {it!=axis}
        return listOf(0 to 0,1 to 0,1 to 1,0 to 1).map {(a,b)->
            DoubleArray(3) {bounds.limits[it].first}.apply {
                this[axis]=position
                this[other[0]]=if(a==0)bounds.limits[other[0]].first else bounds.limits[other[0]].second
                this[other[1]]=if(b==0)bounds.limits[other[1]].first else bounds.limits[other[1]].second
            }
        }
    }
    fun project(prepared:PreparedSurface,projection:SurfaceProjection,transparent:Boolean=false,withLighting:Boolean=true):List<SurfaceFace> {
        val cache=java.util.IdentityHashMap<DoubleArray,DoubleArray>()
        fun point(p:DoubleArray)=cache.getOrPut(p){projection.project(p)}
        val faces=prepared.faces.mapNotNull {face->
            val front=(withLighting||prepared.convex||(face.closed ?: prepared.closed))&&face.normal.indices.sumOf {face.normal[it]*projection.direction[it]}>1e-12*sqrt(face.normal.sumOf {it*it})
            if(!transparent&&(face.closed ?: prepared.closed)&&!front)return@mapNotNull null
            val projected=face.points.map(::point)
            val lighting=if(withLighting||face.points!==face.source)face.levels?.let {lightingGradient(face.source.map(::point),it)} else null
            val levels=if(withLighting||face.levels==null)null else if(face.points===face.source)face.levels else projected.map {SurfaceColors.gradientValue(lighting,it,face.levels.average())}
            var depth=0.0;for(p in projected)depth+=p[2]
            SurfaceFace(face.points,depth/projected.size,face.height,face.light,lighting,projected,front,face.levels?.average(),face.group,levels)
        }
        return faces.sortedWith(compareBy<SurfaceFace> {if(!transparent&&prepared.convex&&it.front)1 else 0}.thenBy {it.depth})
    }
    fun combine(groups:List<PreparedSurface>):PreparedSurface {
        if(groups.size==1)return groups.first()
        return PreparedSurface(groups.flatMapIndexed {index,group->group.faces.map {it.copy(group=index,closed=group.closed)}},false,groups.all {it.closed})
    }
    fun faces(mesh:List<List<DoubleArray?>>,projection:SurfaceProjection,triangles:List<List<DoubleArray>> = emptyList(),triangleNormals:List<List<DoubleArray>> = emptyList(),convex:Boolean=false):List<SurfaceFace> {
        return project(prepare(mesh,projection.bounds,triangles,triangleNormals,convex),projection)
    }
}
