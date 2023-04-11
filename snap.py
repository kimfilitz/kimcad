import math
from math import pi, radians, sin, cos, tan


import bpy, bmesh
import bpy_extras
import gpu
import bgl
import blf
import mathutils
from gpu_extras.batch import batch_for_shader
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.types import SpaceView3D
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty

from . import polygons
from .polygons import intersectionLinePlane
from .properties import KIMPartAttributes

import numpy as np



class VertexSnap:

	def __init__(self, snapdistance):
		self.snapdistance = snapdistance
		self.name = 'VERTEX'
		
	def snap(self, path, activeObject):
		
		# gehe von Object-Mode aus
		if activeObject:
			print('  ----- snap  name '+str(self.name))
			print('  ----- snap  isinstance '+str(isinstance(activeObject.data, bpy.types.Mesh)))
			
			if isinstance(activeObject.data, bpy.types.Mesh):
				bm = bmesh.new()
				bm.from_mesh(activeObject.data)
				bm.verts.ensure_lookup_table()
				verts = bm.verts
				
				matW = activeObject.matrix_world
				
				worldCoordinates = [matW @ v.co for v in bm.verts] # übersetzung von local in world coordinates
				
				pos = path[-1]
				
				print("::snap len verts: "+str(len(verts)))
				
				bestVerts = [None, None, None]
				bestDistances = [self.snapdistance, self.snapdistance, self.snapdistance]
				for v in worldCoordinates:
					
					if abs(v.x - pos.x) < self.snapdistance and abs( v.y - pos.y) < self.snapdistance and abs(v.z - pos.z) < self.snapdistance:
						if abs(v.x - pos.x) < bestDistances[0]:
								bestDistances[1] = abs(pos.x - v.x)
								bestVerts[0] = v
						if abs( v.y - pos.y) < bestDistances[1]:
								bestDistances[1] = abs(pos.y - v.y)
								bestVerts[1] = v
						if abs(v.z - pos.z) < bestDistances[2]:
								bestDistances[2] = abs(pos.z - v.z)
								bestVerts[2] = v
						
				print("  bestDistances: "+str(bestDistances))	
				index = bestDistances.index(min(bestDistances))
				print("  index: "+str(index)+ ' bestVerts: '+str(bestVerts))
				bestVertCo = bestVerts[index]
				
				return bestVertCo
		
		return None


class EdgeSnap:
	def __init__(self, snapdistance):
		self.snapdistance = snapdistance
		self.name = 'EDGE'
		
		
	def snap(self, path, activeObject):
		
		# gehe von Object-Mode aus
		if activeObject:
			
			print('  ----- snap  name '+str(self.name))
			print('  ----- snap  isinstance '+str(isinstance(activeObject.data, bpy.types.Mesh)))
			
			if isinstance(activeObject.data, bpy.types.Mesh):
				bm = bmesh.new()
				bm.from_mesh(activeObject.data)
				bm.verts.ensure_lookup_table()
				
				matW = activeObject.matrix_world
				
				pos = path[-1]
				p = np.array([pos.x, pos.y])
				
				print('  p: '+str(p))
				
				snappedEdge = getNearestEdge(p, bm, matW, self.snapdistance)
				
				if snappedEdge:
					pOnEdge, t = pointOnLine(snappedEdge, p)
					if 0 < t < 1: # auf der Linie zwischen den beiden Vertices
						return mathutils.Vector((pOnEdge[0], pOnEdge[1], 0))
					else:
						return None # ausserhalb des Edges
						
				
				
					
		return None

#
# ckecks if a edge in bm is in snapdistance to p 
# p: np.array([pos.x, pos.y])
#
def getNearestEdge(p, bm, matW, snapdistance):
				snappedEdge = None
				snappedEdges = []
				snappedEdgesDistance = []
				
				edges = bm.edges
				for edge in edges:
					#print(' edge: '+str(edge))
					#print(' edge verts: '+str(edge.verts))
					
					pstartWorld = matW @ edge.verts[0].co
					pendWorld = matW @ edge.verts[1].co
					
					pstart = np.array([pstartWorld.x, pstartWorld.y])
					pend = np.array([pendWorld.x, pendWorld.y])
					
					#print(' pstart: '+str(pstart))
					#print(' pend: '+str(pend))
					
					d = perpendicularDistance(p, pstart, pend)
					print('  d: '+str(d))
					
					if d < snapdistance:
						print('  d < self.snapdistance ')
						snappedEdge = [pstart, pend]
						snappedEdges.append([pstart, pend])
						snappedEdgesDistance.append(d)
				
				if snappedEdge:
					index = snappedEdgesDistance.index(min(snappedEdgesDistance))
					print("  index: "+str(index)+ ' snappedEdges: '+str(snappedEdges))
					snappedEdge = snappedEdges[index]
					return snappedEdge
				
				return None
				
				
	
# funktioniert nur richtig bei 2D Punkten
def perpendicularDistance(p, pstart, pend):
	#return (pend-pstart).cross(pstart-p) / (pend-pstart).normalized()
	return np.abs(np.cross(pend-pstart, pstart-p)) / np.linalg.norm(pend-pstart)
		
#
# the point on line which has closest distance to p (x0,y0)
# returns a tupel with (x,y) and t , 0 < t < 1, wenn zwischen den zwei Punkten der Linie
#
def pointOnLine(line, p):
		p1 = line[0]
		p2 = line[-1]
		
		# Geradengleichung Parameter
		a = p1[1] - p2[1]
		b = p2[0] - p1[0]
		c = p1[0]*p2[1] - p2[0]*p1[1]
		
		#print("a: %d, b: %d, c: %d " % (a, b, c))
		
		x = (b*(b*p[0] - a*p[1]) - a*c) / (math.pow(a,2)+math.pow(b,2))
		y = (a*(-b*p[0] + a*p[1]) - b*c) / (math.pow(a,2)+math.pow(b,2))
		
		dxP = p2[0] - p1[0]
		dyP = p2[1] - p1[1]
		
		#print("dxP: %f , dyP: %f" % (dxP, dyP))
		
		dx1 = x - p1[0] # delta x zu Punkt 1
		dy1 = y - p1[1] # delta y
		
		dx2 = x - p2[0] # delta x zu Punkt 2
		dy2 = y - p2[1] # delta y
		
		# is the point on the line between p1 and p2 ?
		tx = dx1/dxP
		ty = dy1/dyP
		
		#print("tx: %f , ty: %f" % (tx, ty))
		t = 0
		if math.isnan(tx) and not math.isnan(ty):
			t = ty #vertikale Linie
		elif not math.isnan(tx) and math.isnan(ty):
			t = tx #horizontale Linie
		else:
			t = tx
		
		#print("x: %d, y: %d " % (x, y))
		return (x, y), t
		

#
# Snap to the nearest Point of Edge
#
class EdgePerpendicularSnap:
	def __init__(self, snapdistance):
		self.snapdistance = snapdistance
		self.name = 'EDGE_PERPENDICULAR'
		
		
	def snap(self, path, activeObject):
		print('  ----- snap  name '+str(self.name))
		# gehe von Object-Mode aus
		if activeObject and len(path) > 1:
			
			print('  ----- snap  isinstance '+str(isinstance(activeObject.data, bpy.types.Mesh)))
			
			if isinstance(activeObject.data, bpy.types.Mesh):
				bm = bmesh.new()
				bm.from_mesh(activeObject.data)
				bm.verts.ensure_lookup_table()
				verts = bm.verts
				
				matW = activeObject.matrix_world
				
				pos = path[-1]
				p = np.array([pos.x, pos.y])
				print(' p: '+str(p))
				
				snappedEdge = getNearestEdge(p, bm, matW, self.snapdistance)
				
				if snappedEdge:
					# calculating the point on Edge, perpindicular to the last Point in the path
					pos2 = path[-2]
					p2 = np.array([pos2.x, pos2.y])
					#d2 = perpendicularDistance(p2, snappedEdge[0], snappedEdge[1])
					
					pOnEdge, t = pointOnLine(snappedEdge, p2)
					if 0 < t < 1: # auf der Linie zwischen den beiden Vertices
						
						self.snappoint = mathutils.Vector((pOnEdge[0], pOnEdge[1], 0))
						
						# is pOnEDge in Snapdistance?
						if abs(pOnEdge[0] - pos.x) < self.snapdistance and abs( pOnEdge[1] - pos.y) < self.snapdistance:
							return mathutils.Vector((pOnEdge[0], pOnEdge[1], 0))
					else:
						return None # ausserhalb des Edges
					
		return None
	
	
#
# Snap to the nearest Point of Edge
#
class EdgeCenterSnap:
	def __init__(self, snapdistance):
		self.snapdistance = snapdistance
		self.name = 'EDGE_MIDPOINT'
		
		
	def snap(self, path, activeObject):
		
		# gehe von Object-Mode aus
		if activeObject:
			print('  ----- snap  name '+str(self.name))
			print('  ----- snap  isinstance '+str(isinstance(activeObject.data, bpy.types.Mesh)))
			
			if isinstance(activeObject.data, bpy.types.Mesh):
				bm = bmesh.new()
				bm.from_mesh(activeObject.data)
				bm.verts.ensure_lookup_table()
				verts = bm.verts
				
				matW = activeObject.matrix_world
				
				pos = path[-1]
				p = np.array([pos.x, pos.y])
				print(' p: '+str(p))
				
				snappedEdge = getNearestEdge(p, bm, matW, self.snapdistance)
				
				if snappedEdge:
					print("  snappedEdge: "+str(snappedEdge))
					# calculating the Middle point on Edge
					middlePointx = snappedEdge[1][0] - ((snappedEdge[1][0] - snappedEdge[0][0]) / 2 )
					middlePointy = snappedEdge[1][1] - ((snappedEdge[1][1] - snappedEdge[0][1]) / 2 )
					
					print("  middlePointx: "+str(middlePointx)+' - pos.x '+str(pos.x)+' = '+str(abs(middlePointx - pos.x)))
					
					self.snappoint = mathutils.Vector((middlePointx, middlePointy, 0))
					
					# is middlePoint in Snapdistance?
					if abs(middlePointx - pos.x) < self.snapdistance and abs( middlePointy - pos.y) < self.snapdistance:
						print("  middlePoint in Snapdistance going to return Vector")
						return mathutils.Vector((middlePointx, middlePointy, 0))
					
		return None	
		
#
# Snap to Grid
#
class IncrementSnap:
	def __init__(self, snapdistance):
		self.snapdistance = snapdistance
		self.name = 'INCREMENT'
		self.absolute = bpy.context.tool_settings.use_snap_grid_absolute
		
	def snap(self, path, activeObject):
		pos = path[-1]
		
		if self.absolute: # springt auf absolute Rasterpunkte
			resultX = round(pos.x)
			resultY = round(pos.y)
			return mathutils.Vector((resultX, resultY, 0))
		
		elif not self.absolute and len(path) > 1: # macht nur Sinn, wenn es bereits zwei Punkte gibt
			
			beforepos = path[-2]
			
			dX = beforepos.x - round(beforepos.x)
			dY = beforepos.y - round(beforepos.y)
		
			resultX = round(pos.x) + dX
			resultY = round(pos.y) + dY
			return mathutils.Vector((resultX, resultY, 0))
	

def createSnapCircle(radius):
	numberOfVertices = 32
	
	# Make a new BMesh
	bm = bmesh.new()

	# Add a circle XXX, should return all geometry created, not just verts.
	bmesh.ops.create_circle(
		bm,
		cap_ends=False,
		radius=0.2,
		segments=8)
		
	return bm
		
	
	
class SnapHandler:
	
	# possible values: 'VERTEX', 'EDGE'
	snap_Element = 'UNDEFINED'
	
	def __init__(self):
		self.activeSnaps = []
		
	def activate(self, snaplist):
		print('snaplist: '+str(snaplist))
		self.activeSnaps = []
		for s in snaplist:
			if s == 'VERTEX':	
				self.activeSnaps.append(VertexSnap(0.2))
			elif s == 'EDGE':
				self.activeSnaps.append(EdgeSnap(0.2))
			elif s == 'EDGE_PERPENDICULAR':
				self.activeSnaps.append(EdgePerpendicularSnap(0.2))
			elif s == 'EDGE_MIDPOINT':
				self.activeSnaps.append(EdgeCenterSnap(0.2))
			elif s == 'INCREMENT':
				self.activeSnaps.append(IncrementSnap(0.2))
				
		print('self.activeSnaps: '+str(self.activeSnaps))
	
	def snap(self, pos, active_object):
		
		foundSnaps = {}
		for s in self.activeSnaps:
			result = s.snap(pos, active_object)
			if result:
				foundSnaps[s.name] = result
				
		print ('foundSnaps '+str(foundSnaps))
		
		# Order of Importance
		if 'VERTEX' in foundSnaps.keys():
			self.snap_Element = 'VERTEX'
			return foundSnaps['VERTEX']
		if 'EDGE_PERPENDICULAR' in foundSnaps.keys():
			self.snap_Element = 'EDGE_PERPENDICULAR'
			return foundSnaps['EDGE_PERPENDICULAR']
		if 'EDGE_MIDPOINT' in foundSnaps.keys():
			self.snap_Element = 'EDGE_MIDPOINT'
			return foundSnaps['EDGE_MIDPOINT']
		if 'EDGE' in foundSnaps.keys():
			self.snap_Element = 'EDGE'
			return foundSnaps['EDGE']
		if 'INCREMENT' in foundSnaps.keys():
			self.snap_Element = 'INCREMENT'
			return foundSnaps['INCREMENT']
		
		return result
	
		