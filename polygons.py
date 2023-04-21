"""This submodule contains tools for handling polygons"""


# External dependencies
from __future__ import division, absolute_import, print_function

from collections import deque
import math

import numpy as np

# from blender
import mathutils




'''does the Point lies inside the Polygon?'''
def inside(point, polygon):
	print('::lies inside: ')

#
# calculates a paralell to a polygon through points with offset
# returns a List of mathutils.Vector
#
def offset(offset, points):
	print('::offset : '+str(points))
	print('::offset : '+str(len(points)))
	
	newpoints = []
	segments = []
	
	
	for index in range(1, len(points)):
		nx, ny = calculateNormalVectors(points[index-1], points[index])
		
		p0 = mathutils.Vector((points[index-1].x + nx * offset, points[index-1].y + ny * offset, points[index-1].z))
		p1 = mathutils.Vector((points[index].x + nx * offset, points[index].y + ny * offset, points[index].z))
		
		segments.append([p0, p1])
		
	# first is just the first Point of the first offset-segment
	newpoints.append(segments[0][0])
	
	if len(segments) > 1:
		for index in range(1, len(segments)):
			s0 = segments[index-1]
			s1 = segments[index]
			
			t,u = intersection(s0[0], s0[1], s1[0], s1[1])
			
			print('::offset t: '+str(t))
			
			ipoint = intersectionPoint(t, s0[0], s0[1])
			
			newpoints.append(ipoint)
	
	# append last point
	newpoints.append(segments[-1][1])
	
	print('::offset newpoints: '+str(newpoints))
	
	return newpoints
	
def calculateNormalVectors(p0, p1):

	#slope = (points[1].y - points[0].y)/(points[1].x - points[0].x)

	dx = (p1.x - p0.x)
	dy = (p1.y - p0.y)
	
	#Perpendicular vector
	px = -dy
	py = dx
	
	len = math.sqrt(px*px + py*py)
	nx = px / len
	ny = py / len
	
	return nx, ny
	
def getOffsetDeltas(offset, p0, p1):
	nx, ny = calculateNormalVectors(p0, p1)
		
	offsetDelta = mathutils.Vector((nx * offset, ny * offset))
	return offsetDelta

#
# calculates intersection-Point beetween Line and Plan
#
# nvec: is the normal vector of the plane
# po: is a point on the plane
# lineorigin: is a point on the line
# linevector: is a vector in the direction of the line
#
def intersectionLinePlane(nvec, po, lineorigin, linevector):
	d = (po - lineorigin).dot(nvec) / linevector.dot(nvec)
	
	p = lineorigin + linevector * d
	
	return p

#
# „Ray Crossings“ – Algorithmus
# polygon ist nur ein Point-List keine Segment-List
#
def raycrossing(point, polygon):
	crossings = 0
	
	#print('::raycrossing '+str(len(polygon)))
	
	for index in range(0, len(polygon) - 1):
		#print('index: '+str(index)+' index+1: '+str(index + 1)+' len: '+str(len(polygon)))
		
		startpoint = polygon[index]
		endpoint = polygon[index+1]
		
		#translate to point as center of coordinate-System
		#startpoint = Point(polygon[index].x-point.x , polygon[index].y-point.y)
		
		# polygon ist nur ein Point-List keine Segment-List
		# if not (index + 1 == len(polygon)):
		#endpoint = Point(polygon[index+1].x-point.x , polygon[index+1].y-point.y)
		
		#print('startpoint: '+str(startpoint))
		#print('endpoint: '+str(endpoint))
		
		# Sonderfall point liegt auf point
		if(point.x == startpoint.x and point.y == startpoint.y):
			#print('q liegt auf startpoint')
			return True
		
		
		
		if(endpoint.y == point.y and startpoint.y > point.y):
			#print('b liegt auf horizontalem Strahl durch q und a darüber ')
			if(point.x <= startpoint.x):
				#print('b in x positiv ')
				crossings += 1
		if(startpoint.y == point.y and endpoint.y > point.y):
			#print('a liegt auf horizontalem Strahl durch q und b darüber ')
			# ray nach x positiv
			if(point.x <= endpoint.x):
				#print('b in x positiv ')
				crossings += 1
		if(startpoint.y < point.y and endpoint.y > point.y):
			#print('a liegt unter horizontalem Strahl durch q und b darüber ')
			
			u = intersectionXAxis(startpoint, endpoint, point)
			
			#print('u: '+str(u))
			
			if 0.0 <= u:
				crossings += 1
			
			
		if(endpoint.y < point.y and startpoint.y > point.y):
			#print('b liegt unter horizontalem Strahl durch q und a darüber')
			
			u = intersectionXAxis(startpoint, endpoint, point)
			
			#print('u: '+str(u))
			if 0.0 <= u:
				crossings += 1
			
			
	
	#print('crossings: '+str(crossings))
	
	if crossings % 2: #ungrade
		return True
	else: #grade
		return False

#
# Schnittpunkte von einem Polygon mit einem Segment
# polygon und segment sind Point-Listen
# brute force jedes segment gegen jedes andere
#
def polySegments(polygon, segments):
	
	#print('poly: '+str(len(polygon))+' segments: '+str(len(segments)))
		
	crossings = []
	
	for index in range(0, len(polygon) - 1):
		#print('index: '+str(index)+' index+1: '+str(index + 1)+' len: '+str(len(polygon)))
		
		startpoint = polygon[index]
		endpoint = polygon[index+1]
		
		for i in range(0, len(segments) - 1):
			sstart = segments[i]
			send = segments[i+1]
			
			#print('startpoint: '+str(startpoint)+' endpoint: '+str(endpoint))
			#print('sstart: '+str(sstart)+ ' send: '+str(send))
			
			t, u = intersection(startpoint, endpoint, sstart, send)
			
			if t and u:
				if 0 <= t <= 1 and 0 <= u <= 1:
					#print('segment schneidet polygon: '+str(u)+' t: '+str(t))
					crossings.append(intersectionPoint(t, startpoint, endpoint))
		
	return crossings

	
	
'''	cross Section of two polygons
	Schnitt von konvexen Polygonen
	Algorithmus von O’Rourke, Chien, Olson und Naddor aus dem Jahr 1982.
'''
def polyCross(polygonP, polygonQ):
	#print('::polyCross begin')
	
	
	# erste Sondersituation: 
	# kein Punkt des einen Polygons liegt im anderen
	'''
	inpoly = False
	for p in polygonP:
		inpoly = raycrossing(p, polygonQ)
		
		if(inpoly):
			print('p '+str(p)+' liegt in polygon2 '+str(polygonP))
			break
	
	print('---- inpoly p2 in p1: '+str(inpoly))
	
	for p in polygonQ:
		inpoly = raycrossing(p, polygonP)
		#print('inpoly '+str(inpoly))
		if(inpoly):
			break
	
	print('---- inpoly p1 in p2: '+str(inpoly))
	'''
	polyResult = []
	
	a = 0
	b = 0
	
	m = len(polygonQ)
	n = len(polygonP)
	

	aadv = 0
	badv = 0
	inFlag = 'unknown'
	
	inFlagBegin = 0
	
	
	while ((aadv < n or badv < m) and (aadv < 2*n) and (badv < 2*m)):
	
		#print('----: ')
		#print('a: '+str(a)+' b: '+str(b))
		#print('aadv: '+str(aadv)+' badv: '+str(badv))
		#print('inFlag: '+str(inFlag))
		#print('len(polygonP): '+str(len(polygonP))+' len(polygonQ): '+str(len(polygonQ)))
	
		segmentA = [polygonP[a], polygonP[a + 1]]
		segmentB = [polygonQ[b], polygonQ[b + 1]]
	
		vectorA = toVector(segmentA)
		vectorB = toVector(segmentB)
	
		cross = determinate(vectorA, vectorB)
		
		#print('cross:  '+str(cross))
		
		bHA = isLeft(segmentA[0], segmentA[1], segmentB[1])
		aHB = isLeft(segmentB[0], segmentB[1], segmentA[1])
		
		#print('bHA:  '+str(bHA))
		#print('aHB:  '+str(aHB))
		
		# compute intersection
		t,u = intersection(segmentA[0], segmentA[1], segmentB[0], segmentB[1])
		intersect = False
		#print('t,u:  '+str(t)+', '+str(u))
		
		
		# gibt es einen Schnittpunkt der beiden Segmente, der auf den Segmenten liegt?
		if((t >= 0 and t<= 1) and ( u >= 0 and u<= 1 )):
			iPoint = intersectionPoint(t, segmentA[0], segmentA[1])
			
			if(inFlag == 'unknown'):
				aadv = badv = 0
				
			# welches Polygon ist zukünftig 'in', dessen segmente werden Teil von S
			# update inFlag
			if (bHA > 0):
				inFlag = 'Qin'
			elif (aHB > 0):
				inFlag = 'Pin'
				
			polyResult.append(iPoint)
			#print('appended intersectionPoint: '+str(iPoint))
			#print('inFlag: '+str(inFlag))
			
		
			
		#print('polyResult:  '+str(polyResult))
		#print('inFlag: '+str(inFlag))
		#print('inFlagBegin: '+str(inFlagBegin))
	
		# Advance-rules
		# Special cases
		
		# Special case: A & B parallel and separated. */
		if cross == 0 and aHB < 0 and bHA < 0:
			print('Special case: A & B parallel and separated')
			break
		# Special case: A & B collinear.
		elif cross == 0 and aHB == 0 and bHA == 0:
			print('Special case: A & B collinear')
			 
			if ( inFlag == 'Pin' ):
				b = (b+1) % (m-1)
				badv += 1
				inFlag == 'Qin'
			else:
				a = (a+1) % (n-1);
				aadv += 1
				inFlag = 'Pin'
		# Special case: 0-Divisor bei Schnittpunkt-Berechnung.
		elif not t and not u:
			print('Special case: 0-Divisor bei Schnittpunkt-Berechnung')
			 
			if ( inFlag == 'Pin' ):
				b = (b+1) % (m-1)
				badv += 1
				inFlag == 'Qin'
			else:
				a = (a+1) % (n-1);
				aadv += 1
				inFlag = 'Pin'
		
		# generic cases
		if((cross > 0 and (not bHA > 0)) or (cross < 0 and aHB > 0) ):
			#print('Vorrücken von B')
			
			if(inFlag == 'Qin'):
				polyResult.append(polygonQ[b + 1]) # append end-point of seggment
			
			#print(' b: '+str(b)+' ,b+2: '+str(b+2)+' (b+2) % m: '+str((b+2) % m))
			
			b = (b+1) % (m-1)
			badv += 1
		elif((cross > 0 and (bHA > 0)) or (cross < 0 and (not aHB > 0)) ):
			#print('Vorrücken von A')
			
			if(inFlag == 'Pin'):
				polyResult.append(polygonP [a + 1]) # append end-point of seggment
			
			#print(' a: '+str(a)+' ,a+2: '+str(a+2)+' (a+2) % n: '+str((a+2) % n))
			
			a = (a+1) % (n-1);
			aadv += 1
		
		#print('a: '+str(a)+' aadv: '+str(aadv))
		#print('b: '+str(b)+' badv: '+str(badv))
		
			
	
	# deal with special cases
	if ( inFlag == 'unknown'):
		#print("The boundaries of P and Q do not cross.")
		#print("checking for inner Polygons")
		
		inPolygonQ = []
		for p in polygonP:
			inpoly = raycrossing(p, polygonQ)
			inPolygonQ.append(inpoly)
			
				
	
		#print('---- inPolygonQ: '+str(inPolygonQ))
		if all(inPolygonQ):
			#print('---- polygon Q in P ')
			polyResult = polygonP
		
		
		inPolygonP = []
		
		for p in polygonQ:
			inpoly = raycrossing(p, polygonP)
			inPolygonP.append(inpoly)
			
				
		#print('---- inPolygonP: '+str(inPolygonP))
		if all(inPolygonP):
			#print('---- polygon P in Q ')
			polyResult = polygonQ
		
	#else:
	#	print("::::: cross: "+str(inFlag))
	
	#print('polyResult:  '+str(polyResult))	
		
	return polyResult
		
	
	
''' is polygon counter-clock-wise?'''
def orientation(polygon):
	print('::orientation ')
	
	n = len(polygon)
	minPoint = np.amin(polygon, axis=0)
	minIndex = np.argmin(polygon, axis=0)
	
	indices = np.where(polygon==minPoint)
	
	print('::minPoint '+str(minPoint))
	print('::minIndex '+str(minIndex))
	print('::indices '+str(indices))
	
def sortVertices(array):
    
    sum_xy = np.sum(array, axis=0)
    
    print('sum xy: '+str(sum_xy))
    
    center_x = sum_xy[0]/len(array)
    center_y = sum_xy[1]/len(array)
    
    
    print('center_x: '+str(center_x))
    
    sarray = sorted(array, key=lambda x: math.atan2(x[1] - center_y, x[0] - center_x))
    
    print('sarray: '+str(sarray))
    
    return sarray
    
	
''' determinante einer 2x2 Matrix '''
''' a,b : zwei Points '''
def determinate(a, b):
	return a.x*b.y - b.x*a.y
	
	
''' creates a convex Hull of a simple Polygon '''
''' polygon: list of Points '''
def convexHull(polygon):
	
	#print('::convexHull polygon: '+str(polygon))
	
	# initialize a deque D[] from bottom to top so that the
	# 1st three vertices of P[] are a ccw triangle
	# Point* D = new Point[2*n+1];
	d = deque([])
	dindices = deque([])
	n = len(polygon)
	
	# initial bottom and top deque indices
	bot = 0
	top = 0    
	#d[bot] = d[top] = polygon[2] # 3rd vertex is at both bot and top
	
	d.append(polygon[2])
	dindices.append(2)
	d.appendleft(polygon[2])
	dindices.appendleft(2)
	
	if (isLeft(polygon[0], polygon[1], polygon[2]) > 0):
		#d[bot+1] = polygon[0]
		
		d.insert(1, polygon[0])
		dindices.insert(1, 0)
		
		#d[bot+2] = polygon[1] 
		
		d.insert(2, polygon[1])
		dindices.insert(2, 1)
		
		# ccw vertices are: 2,0,1,2
	else:
		#d[bot+1] = polygon[1]
		#d[bot+2] = polygon[0] 
		
		# ccw vertices are: 2,1,0,2
		
		d.insert(1, polygon[1])
		dindices.insert(1, 1)
		
		d.insert(2, polygon[0])
		dindices.insert(2, 0)
	
	#print('convexHull init: '+str(d))
	#print('indices init: '+str(dindices))
	
	top = len(d)
	
	# debug
	#fig, ax = plt.subplots()
	
	# compute the hull on the deque d
	# process the rest of vertices
	for index in range(3, len(polygon)):   
		
		#print('index: '+str(index),' bot: '+str(bot))
		#print('dindices: '+str(dindices))
		
		# test if next vertex is inside the deque hull
		if ((isLeft(d[0], d[1], polygon[index]) > 0) and (isLeft(d[-2], d[-1], polygon[index]) > 0) ):
			#print('index '+str(index)+' is in hull')         # skip an interior vertex
			continue
			
		#print('isLeft of bot: '+str(isLeft(d[0], d[1], polygon[index])))
		#print('isLeft of top: '+str(isLeft(d[-2], d[-1], polygon[index])))
		
		# get the rightmost tangent at the deque bot
		# Get the tangent to the bottom
		while (isLeft(d[0], d[1], polygon[index]) <= 0):
			#bot += 1
			#print(str(index)+' is Right of '+str(dindices[0])+' -> '+str(dindices[1]))
			d.popleft()
			dindices.popleft()
		d.appendleft(polygon[index])
		dindices.appendleft(index)
		
		#print('dindices from bottom: '+str(dindices))
		
		# get the leftmost tangent at the deque top  
		while (isLeft(d[-2], d[-1], polygon[index]) <= 0):
			#top -= 1
			#print(str(index)+' is Right of '+str(dindices[-2])+' -> '+str(dindices[-1]))
			d.pop()
			dindices.pop()
		d.append(polygon[index])
		dindices.append(index)
		
		#print('dindices after from top: '+str(dindices))
		
		
		#ax.scatter(polygon[index].x, polygon[index].y, c='g')
			
		#i = dindices[index]
		#ax.annotate(f" {index}", xy=[polygon[index].x,polygon[index].y])
		
			
		#ax.axhline(y=0, color='k')
		#ax.axvline(x=0, color='k')
		#plt.show()
		
		
	#print('indices '+str(dindices))
	#print('d '+str(d))
		
	
	return d, dindices
	
	
''' test if a point is Left|On|Right of an infinite line through P0 and P1. '''	
def isLeft(P0, P1, P2):
	return (P1.x - P0.x)*(P2.y - P0.y) - (P2.x - P0.x)*(P1.y - P0.y)
	

def crossPointOfLines(line1, line2):
	print('::crossPointOfLines ')
	
def translate(polygon, x, y):
	for point in polygon:
		point.x += x
		point.y += y
	return polygon
		
def copy(polygon):
	
	newPoly = []
	for point in polygon:
		newPoly.append(Point(point.x, point.y))

	return newPoly
	
''' Point 2 - Point1'''
def toVector(segment):
	return Point(segment[1].x-segment[0].x, segment[1].y-segment[0].y)
	
def intersection(point1, point2, point3, point4):

	# check for 0-Divisor
	if((point1.x-point2.x)*(point3.y-point4.y) - (point1.y-point2.y)*(point3.x-point4.x)) == 0:
		#print('0')
		t = False
		u =False
		
		'''
		if (point1.x-point2.x)*(point3.y-point4.y) == (point1.y-point2.y)*(point3.x-point4.x):
			print('0?:  '+str((point1.x-point2.x)*(point3.y-point4.y))+' - '+str((point1.y-point2.y)*(point3.x-point4.x)))
		
		if(point1.x-point2.x)*(point3.y-point4.y) == 0:
			print('(point1.x-point2.x)*(point3.y-point4.y)')
			if(point1.x-point2.x) == 0:
				print('(point1.x-point2.x)')
			if(point3.y-point4.y) == 0:
				print('(point3.y-point4.y)')
				print('point3.y: '+str(point3.y)+' point4.y: '+str(point4.y))
			
		if(point1.y-point2.y)*(point3.x-point4.x) == 0:
			print('(point1.y-point2.y)*(point3.x-point4.x)')
			if(point1.y-point2.y) == 0:
				print('(point1.y-point2.y)')
				print('point1.y: '+str(point1.y)+' point2.y: '+str(point2.y))
			if(point3.x-point4.x) == 0:
				print('(point3.x-point4.x)')
				print('point3.x: '+str(point3.x)+' point4.x: '+str(point4.x))
		'''
		return t,u

	# The intersection point falls within the first line segment if 0.0 ≤ t ≤ 1.0,
	t = ((point1.x-point3.x)*(point3.y-point4.y) - (point1.y-point3.y)*(point3.x-point4.x)) / ((point1.x-point2.x)*(point3.y-point4.y) - (point1.y-point2.y)*(point3.x-point4.x))
		
	# The intersection point falls within the second line segment if 0.0 ≤ u ≤ 1.0. 
	u = - ((point1.x-point2.x)*(point1.y-point3.y)-(point1.y-point2.y)*(point1.x-point3.x)) / ((point1.x-point2.x)*(point3.y-point4.y) - (point1.y-point2.y)*(point3.x-point4.x))
		
	return t,u

#
# ähnlich wie obige Intersection, aber benutzt als point 4 einen vector in x-Achsen Richtung (1,0)
# point 1 und point 2 sind die Punkte einer Geraden, point 3 ist der punkt von dem der horizontale Strahl/Vektor ausgeht - hier horizontal in Richtung der x-Achse der geschnitten werden kann
# gibt u zurück: positiv in positiver Richtung der Achse, negativ, wenn negativ
# u entspricht dem Schnittpunkt relativ zu Point 3 in Richtung der x-Achse
#
def intersectionXAxis(point1, point2, point3):
	# The intersection point falls within the second line segment if 0.0 ≤ u ≤ 1.0. 
	u = - ((point1.x-point2.x)*(point1.y-point3.y)-(point1.y-point2.y)*(point1.x-point3.x)) / ((point1.x-point2.x)*(point3.y-point3.y) - (point1.y-point2.y)*(point3.x-(point3.x+1)))
		
	return u
	
'''
	calculates a Point on a Line between point1 and point2 with the Parameter t
	t: when on the line the parameter should be 0 <= t <= 1
	
'''
def intersectionPoint(t, point1, point2):
	
	ipointX = point1.x + t*(point2.x-point1.x)
	ipointY = point1.y + t*(point2.y-point1.y)
	
	ipoint = mathutils.Vector((ipointX, ipointY, point1.z))
	
	return ipoint
	
'''
	calculates a Point on a Line between point1 and point2 with the Parameter t
	t: when on the line the parameter should be 0 <= t <= 1
	point 1 and point2 are coordinate lists or tuples: (x,y)
	returns a tupel with the x,y Coordinates 
'''
def intersectionPointRaw(t, point1, point2):
	
	ipointX = point1[0] + t*(point2[0]-point1[0])
	ipointY = point1[1] + t*(point2[1]-point1[1])
	
	
	return (ipointX, ipointY)
	
#
# [0] Start-Punkt des Rechteckes
# [1] width
# [2] height
#
def rectangleIntersect(rectangleP, rectangleQ):

	print('P: '+str(rectangleP)+' Q: '+str(rectangleQ))
	
	intersectionPoints = []

	pmaxX = rectangleP[0].x + rectangleP[1]
	pmaxY = rectangleP[0].y + rectangleP[2]
	pminX = rectangleP[0].x
	pminY = rectangleP[0].y
	
	qmaxX = rectangleQ[0].x + rectangleQ[1]
	qmaxY = rectangleQ[0].y + rectangleQ[2]
	qminX = rectangleQ[0].x
	qminY = rectangleQ[0].y

	if(qminX <= pminX <= qmaxX 
	and pmaxX <= qmaxX
	and qminY <= pminY <= qmaxY
	and pmaxY <= qmaxY) :
		print('--- P vollständig in Q  ---')
		return 0, intersectionPoints
		
	if(pmaxX < qminX
	or pminX > qmaxX
	or pmaxY < qminY
	or pminY > qmaxY):
		print('--- P vollständig ausserhalb von Q (und umgekehrt)---')
		return -1, intersectionPoints
	
	if(pminX <= qminX <= pminX 
	and qmaxX <= pmaxX
	and pminY <= qminY <= pmaxY
	and qmaxY <= pmaxY) :
		print('--- Q vollständig in P  ---')
		return 0, intersectionPoints
		
		
	crossings = 0	
	# gehe von startpunkt vertikal
	# checke nur die horizontalen des anderen rechteckes
	point1 = rectangleP[0]
	point2 = Point(rectangleP[0].x, rectangleP[0].y + rectangleP[2])
	point3 = rectangleQ[0]
	point4 = Point(rectangleQ[0].x + rectangleQ[1], rectangleP[0].y)
	'''if(rectangleQ[0].x <= point1.x <= rectangleQ[0].x + rectangleQ[1] and (point1.y > point3.y > point2.y or point2.y > point3.y > point1.y )):
		print('--- vertikale von P schneidet horizontale von Q (Startpunkt) ---')
		crossings += 1
	'''
	if(qminX <= pmaxX <= qmaxX 
	and (pmaxY > qmaxY > pminY)):
		print('--- max vertikale von P schneidet max horizontale von Q ---')
		iPoint = Point(pmaxX, qmaxY)
		intersectionPoints.append(iPoint)
		crossings += 1
	
	if(qminX <= pmaxX <= qmaxX 
	and (pmaxY > qminY > pminY)):
		print('--- max vertikale von P schneidet min horizontale von Q ---')
		iPoint = Point(pmaxX, qminY)
		intersectionPoints.append(iPoint)
		crossings += 1
	
	
	
	# zweite vertikale von P
	point1 = Point(rectangleP[0].x + rectangleP[1], rectangleP[0].y)
	point2 = Point(rectangleP[0].x + rectangleP[1], rectangleP[0].y + rectangleP[2])
	if(qminX <= pminX <= qmaxX 
	and (pmaxY > qmaxY > pminY)):
		print('--- min vertikale von P schneidet max horizontale von Q ---')
		iPoint = Point(pminX, qmaxY)
		intersectionPoints.append(iPoint)
		crossings += 1
		
	# zweite vertikale von P zu 1. horizontale von Q
	point3 = rectangleQ[0]
	point4 = Point(rectangleQ[0].x + rectangleQ[1], rectangleQ[0].y)
	
	if(qminX <= pminX <= qmaxX 
	and (pmaxY > qminY > pminY)):
		print('--- min vertikale von P schneidet min horizontale von Q () ---')
		iPoint = Point(pminX, qminY)
		intersectionPoints.append(iPoint)
		crossings += 1
		
		
	# check horizontalen von P
	if(qminY <= pmaxY <= qmaxY):
		if pmaxX > qmaxX > pminX:
			print('--- max horizontale von P schneidet max vertikale von Q ---')
			iPoint = Point(qmaxX, pmaxY)
			intersectionPoints.append(iPoint)
			crossings += 1
		elif pmaxX > qminX > pminX:
			print('--- max horizontale von P schneidet min vertikale von Q ---')
			iPoint = Point(pmaxY, pmaxY)
			intersectionPoints.append(iPoint)
			crossings += 1
		
	if(qminY <= pminY <= qmaxY):
		if pmaxX > qmaxX > pminX: 
			print('--- min horizontale von P schneidet max vertikale von Q ---')
			iPoint = Point(qmaxX, pminY)
			intersectionPoints.append(iPoint)
			crossings += 1
		elif pmaxX > qminX > pminX:
			print('--- min horizontale von P schneidet min vertikale von Q ---')
			iPoint = Point(qminX, pminY)
			intersectionPoints.append(iPoint)
			crossings += 1
	
	print('--- crossings ' + str(crossings))
	return crossings, intersectionPoints

#
# erzeugt Bounding Box aus Coordinaten-List
#
def createBoundingBox(points):
	#maxX = max(points)[0]
	maxX = max(points, key=lambda x: x[0])[0]
	#minX = min(points)[0]
	minX = min(points, key=lambda x: x[0])[0]
	#minY = min(points)[1]
	maxY = max(points, key=lambda x: x[1])[1]
	#maxY = max(points)[1]
	minY = min(points, key=lambda x: x[1])[1]

	startpoint = Point(minX, minY) # im svg-Coordinate System: links oben
	width = maxX - minX  
	height = maxY - minY  
	
	return [startpoint, width, height]
	
	
	
	
	
	
	
	
	
	
		