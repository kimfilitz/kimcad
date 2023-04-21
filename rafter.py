import math

import bpy, bmesh
import bpy_extras
from bpy_extras.view3d_utils import location_3d_to_region_2d 
import gpu
import bgl
import blf
import mathutils
from gpu_extras.batch import batch_for_shader
from math import pi, radians, sin, cos, tan
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.types import SpaceView3D
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty

from . import polygons
from . import properties
from .polygons import intersectionLinePlane
from .polygons import getOffsetDeltas
from .polygons import intersectionPoint
from .properties import KIMPartAttributes
from .snap import SnapHandler
from .snap import createSnapCircle
from .ctrlline_drawhandler import CtrlLineDrawHandler

lastcoords = []

#
# Factory for creating Simple Walls
#
class Rafter:
	type = 'Rafter'

	def __init__(self, initValues):
		
		self.initDic = initValues
		
	#
	# create main object and mesh
	#	
	def create_object(self, context):

		print("::create_rafter_object context: "+str(context))
		print("::create_rafter_object self: "+str(self))
		print("::create_rafter_object angle: "+str(self.initDic.get('rafter_angle')))
		print("::create_rafter_object type: "+str(self.initDic.get('type')))
		print("::create_rafter_object ueber: "+str(self.initDic.get('ueber')))
		
		angle = self.initDic.get('rafter_angle')
		ueber = self.initDic.get('ueber')
		path = self.initDic.get('path')
	
		# deselect all objects
		for o in bpy.data.objects:
			o.select_set(False)
		
		#
		# we create main object and mesh
		#
		mainmesh = bpy.data.meshes.new("rafter")
		
		mainobject = bpy.data.objects.new('Rafter', mainmesh)
		mainobject.location = path[0] # take first point
		bpy.context.collection.objects.link(mainobject)
		
		
	
		# we select, and activate, main object
		mainobject.select_set(True)
		bpy.context.view_layer.objects.active = mainobject
		
		ma = mainobject.KIMAttributes
		ma.parttype = KIMPartAttributes.RAFTER
		ma.objecttype = KIMPartAttributes.MAINOBJECT
		
		# we shape the main object and create other objects as children
		# set Standard -Values
		mp = mainobject.KIMPartProps
		mp.update = False #prevent updating before object creation
		
		mp.type = 'Rafter'
		mp.standards = "6"
		mp.rafter_angle = angle
		mp.ueber = ueber
		
		mp.listener = self
		
		print("::create_rafter_object mp: "+str(mp))
		print("::create_rafter_object mp.listener: "+str(mp.listener))
		
		#
		# generate sub-object for ctrl-Line
		#
		ctrlmesh = bpy.data.meshes.new("ctrl-Line")
	
		ctrl_o = bpy.data.objects.new("ctrl-Line", ctrlmesh)
		bpy.context.collection.objects.link(ctrl_o)
		
		# create control-line
		self.generate_CtrlLine(mp, ctrlmesh, path)
		
		ma = ctrl_o.KIMAttributes
		ma.parttype = KIMPartAttributes.RAFTER
		ma.objecttype = KIMPartAttributes.CTRLLINE
	
		#set_normals(ctrl_o)
		ctrl_o.parent = mainobject
		ctrl_o.location.x = 0 # relative to parent
		ctrl_o.location.y = 0
		ctrl_o.location.z = 0
		ctrl_o.lock_location = (True, True, True)
		ctrl_o.lock_rotation = (True, True, True)
		ctrl_o.display_type = 'WIRE'
		ctrl_o.hide_viewport = False
		ctrl_o.hide_render = True
		
		ctrl_o.data.vertices[0].hide = True
		
		#
		# generate mesh for rafter from ctrl-Line
		#
		bm = bmesh.new()
	
		current_mode = ctrl_o.mode
		if current_mode == 'OBJECT':
			bm.from_mesh(ctrl_o.data)
			bm.verts.ensure_lookup_table()
		elif current_mode == 'EDIT':
			bm = bmesh.from_edit_mesh(ctrl_o.data)
			
		ctrl_path = [item.co for item in bm.verts]
		
		generate_Rafter2(mp, mainmesh, ctrl_path)
	
		# deactivate others
		for o in bpy.data.objects:
			if o.select_get() is True and o.name != mainobject.name:
				o.select_set(False)
		
		# at the end, all further changes should be updated
		mp.update = True
		
	#
	# generates Crl-Line-Mesh from path
	#
	def generate_CtrlLine(self, mp, tmp_mesh, path):
		global lastcoords
		
		vertices = []
		edges = []
		lastcoords = []
		
		for point in path:
			print('point: '+str(point))
			vertices.extend([(point[0] - path[0][0], point[1] - path[0][1], 0)]) # delta values to first point
			lastcoords.extend([point])
			
		for index in range(1, len(path)):
			edges.append((index-1, index))	
						 
		tmp_mesh.from_pydata(vertices, edges, [])
		
		
	#
	# Update main Mesh
	#
	def update_object(self, context):
		
		print("::update_object ")
		
		o = context.active_object
		
		mattr = o.KIMAttributes
		
		print("::update_object "+str(mattr.objecttype))
		
		if mattr.objecttype == KIMPartAttributes.MAINOBJECT:
	
			mp = o.KIMPartProps
			
			if mp.update:
				
				if mp.standards == '1':
				 	context.scene.sebi_showcustomsize_property = True
				else:
					context.scene.sebi_showcustomsize_property = False
				
				oldmesh = o.data
				oldname = o.data.name
				
				# Now we select that object to not delete it.
				o.select_set(True)
				bpy.context.view_layer.objects.active = o
				
				# and we create a new mesh
				tmp_mesh = bpy.data.meshes.new("temp")
				
				print("::update_object width: "+str(mp.width)+", "+str(mp.height)+", "+str(mp.depth))
				
				o.data = tmp_mesh
				
				# get the ctrl-Line
				ctrl_o = None
				for child in o.children:
					if child.KIMAttributes.objecttype ==  KIMPartAttributes.CTRLLINE:
						ctrl_o = child
						break
				
				#get the coordinates from ctrl-Object
				bm = bmesh.new()
	
				current_mode = ctrl_o.mode
				if current_mode == 'OBJECT':
					bm.from_mesh(ctrl_o.data)
					bm.verts.ensure_lookup_table()
				elif current_mode == 'EDIT':
					bm = bmesh.from_edit_mesh(ctrl_o.data)
				
				ctrl_co = [v.co for v in bm.verts]
				
				# Finally we create all that again (except main object),
				generate_Rafter2( mp, tmp_mesh, ctrl_co)
				
				
				# Remove data (mesh of active object),
				#bpy.data.meshes.remove(oldmesh)
				tmp_mesh.name = oldname
				# and select, and activate, the main object
				o.select_set(True)
				bpy.context.view_layer.objects.active = o
		
		elif mattr.objecttype == KIMPartAttributes.CTRLLINE:
			mainobject = o.parent
			updateFromCtrlLine(mainobject, o)

#
# converts Object as List of Vertices Coordinates (mathutil.Vectors) 
#
def getVertsCo(ctrl_o):
		#
		# generate mesh for rafter from ctrl-Line
		#
		bm = bmesh.new()
	
		current_mode = ctrl_o.mode
		if current_mode == 'OBJECT':
			bm.from_mesh(ctrl_o.data)
			bm.verts.ensure_lookup_table()
		elif current_mode == 'EDIT':
			bm = bmesh.from_edit_mesh(ctrl_o.data)
			
		ctrl_path = [item.co for item in bm.verts]
		
		return ctrl_path
		
#
# Update main Mesh
#
def update_object(context):
		
		print("::update_object Module ")
		
		o = context.active_object
		
		mattr = o.KIMAttributes
		
		print("::update_object "+str(mattr.objecttype))
		
		if mattr.objecttype == KIMPartAttributes.MAINOBJECT:
	
			mp = o.KIMPartProps
			
			if mp.update:
				
				if mp.standards == '1':
				 	context.scene.sebiBauteile.sebi_showcustomsize_property = True
				else:
					context.scene.sebiBauteile.sebi_showcustomsize_property = False
				
				oldmesh = o.data
				oldname = o.data.name
				
				# Now we select that object to not delete it.
				o.select_set(True)
				bpy.context.view_layer.objects.active = o
				
				# and we create a new mesh
				tmp_mesh = bpy.data.meshes.new("temp")
				
				print("::update_object width: "+str(mp.width)+", "+str(mp.height)+", "+str(mp.depth))
				
				o.data = tmp_mesh
				
				# get the ctrl-Line
				ctrl_o = None
				for child in o.children:
					if child.KIMAttributes.objecttype ==  KIMPartAttributes.CTRLLINE:
						ctrl_o = child
						break
				
				#get the coordinates from ctrl-Object
				bm = bmesh.new()
	
				current_mode = ctrl_o.mode
				if current_mode == 'OBJECT':
					bm.from_mesh(ctrl_o.data)
					bm.verts.ensure_lookup_table()
				elif current_mode == 'EDIT':
					bm = bmesh.from_edit_mesh(ctrl_o.data)
				
				ctrl_co = [v.co for v in bm.verts]
				
				# Finally we create all that again (except main object),
				generate_Rafter2( mp, tmp_mesh, ctrl_co)
				
				
				# Remove data (mesh of active object),
				#bpy.data.meshes.remove(oldmesh)
				tmp_mesh.name = oldname
				# and select, and activate, the main object
				o.select_set(True)
				bpy.context.view_layer.objects.active = o
		
		elif mattr.objecttype == KIMPartAttributes.CTRLLINE:
			mainobject = o.parent
			updateFromCtrlLine(mainobject, o)	

#
# generates a Rafter mesh from ctrl-Line, 
# with the properties of mp, 
# updates tmp_mesh
#
def generate_Rafter( mp, tmp_mesh, ctrl_o):
	
	myvertex = []
	myfaces = []
	v = 0
	
	print("::generate_Rafter  mp.rafter_angle: "+str(mp.rafter_angle))
	bm = bmesh.new()
	
	current_mode = ctrl_o.mode
	if current_mode == 'OBJECT':
		bm.from_mesh(ctrl_o.data)
		bm.verts.ensure_lookup_table()
	elif current_mode == 'EDIT':
		bm = bmesh.from_edit_mesh(ctrl_o.data)
	
	endvertex = bm.verts[-1].co
	
	# Mesh defined in Object-Coordinates
	# Rafter will span from Origin to endvertex of Ctrl-Line (also in Object-Coordinates)
	sWidth, sHeight = mp.getSizeOfElement(mp.standards)
	angle = mp.rafter_angle 
	ueber = mp.ueber
	
	deltaXHeight = sin(radians(angle))*sHeight
	deltaZHeight = cos(radians(angle))*sHeight
	
	
	
	
	deltaZHeightFirst = sHeight/cos(radians(angle))
	
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	myvertex.extend([(0, +sWidth/2, 0), 
					 (endvertex.x, +sWidth/2, tan(radians(angle))*endvertex.x ),
					 (endvertex.x, +sWidth/2, tan(radians(angle))*endvertex.x + deltaZHeightFirst),
					 (-ueber - deltaXHeight, +sWidth/2, -(tan(radians(angle))*ueber) + deltaZHeight ),
					 (-ueber, +sWidth/2, -(tan(radians(angle))*ueber) )
					 ])
	
	
		
		
		
	myfaces = [(0, 1, 2, 3, 4)]
					 
	myvertex.extend([(0, -sWidth/2, 0), 
					 (endvertex.x, -sWidth/2, tan(radians(angle))*endvertex.x ),
					 (endvertex.x, -sWidth/2, tan(radians(angle))*endvertex.x + deltaZHeightFirst),
					 (-ueber - deltaXHeight, -sWidth/2, -(tan(radians(angle))*ueber) + deltaZHeight ),
					 (-ueber, -sWidth/2, -(tan(radians(angle))*ueber) )
					 ])
							 
	myfaces.extend([(5, 6, 7, 8, 9)])
	
	myfaces.extend([(3, 2, 7, 8, 3)])#oben
	myfaces.extend([(0, 1, 6, 5, 9, 4)])#unten
	myfaces.extend([(1, 2, 7, 6)])
	myfaces.extend([(3, 4, 9, 8)])
	
	v = len(myvertex)
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)

#
# generates a Rafter mesh from list of Vector-Coordinates, 
# with the properties of mp, 
# updates tmp_mesh
#
def generate_Rafter2( mp, tmp_mesh, ctrl_path):
	
	myvertex = []
	myfaces = []
	v = 0
	
	print("::generate_Rafter  mp.rafter_angle: "+str(mp.rafter_angle))
	print("::generate_Rafter  mp.right_angled: "+str(mp.right_angled)+" level_cut: "+str(mp.level_cut))
	
	endvertex = ctrl_path[-1]
	
	# Mesh defined in Object-Coordinates
	# Rafter will span from Origin to endvertex of Ctrl-Line (also in Object-Coordinates)
	sWidth, sHeight = mp.getSizeOfElement(mp.standards)
	angle = mp.rafter_angle 
	ueber = mp.ueber
	
	overhang_style = mp.overhang_style
	print("::generate_Rafter  overhang_style: "+str(overhang_style))
	
	# distance in x-y Plane
	d = math.sqrt( math.pow(ctrl_path[-1].x - ctrl_path[0].x, 2) + math.pow(ctrl_path[-1].y - ctrl_path[0].y, 2))
	
	# delta values for senkrechter Ueberstand (Sparren rechtwinklig geschnitten)
	deltaXHeight = sin(radians(angle))*sHeight
	deltaZHeight = cos(radians(angle))*sHeight
	
	
	deltaZHeightFirst = sHeight/cos(radians(angle))
	
	offsetdeltas = getOffsetDeltas(sWidth/2, ctrl_path[0], ctrl_path[-1])
	offsetX = offsetdeltas.x
	offsetY = offsetdeltas.y
	
	deltaZOne = tan(radians(angle))*ueber
	
	# axis point of ueber
	t = ueber/d
	ueberpoint = intersectionPoint(t, ctrl_path[0], ctrl_path[-1])
	
	deltaLengthRightAngle = sin(radians(angle))*sHeight
	rightAnglePoint = intersectionPoint(deltaLengthRightAngle/ueber, ueberpoint, mathutils.Vector((0,0,0)))
	deltaZRightAngle = ((tan(radians(angle))*ueber) / ueber) * (ueber-deltaLengthRightAngle)
	
	
	deltaLengthLevelCut = (deltaZHeightFirst/2) * (ueber/ deltaZOne)
	levelCutPoint = intersectionPoint(deltaLengthLevelCut/ueber, ueberpoint, mathutils.Vector((0,0,0)))
	
	# 
	# in x-z Ebene counter-clockwise
	#
	myvertex.extend([(0 + offsetX, offsetY, 0), 
					 (endvertex.x + offsetX, endvertex.y + offsetY, tan(radians(angle))*d ),
					 (endvertex.x + offsetX, endvertex.y + offsetY, tan(radians(angle))*d + deltaZHeightFirst),
					 (-ueberpoint.x + offsetX, -ueberpoint.y + offsetY, -(tan(radians(angle))*ueber) + deltaZHeightFirst )
					 ])
	
	
	
	# doing different Overhangs
	if overhang_style == 'plumb_cut': # straight lotrecht
		myvertex.extend([
					 (-ueberpoint.x + offsetX , -ueberpoint.y + offsetY, -(tan(radians(angle))*ueber) )
					 ])
		myfaces = [(0, 1, 2, 3, 4)]
	elif overhang_style == 'tail_cut': # right-angle
		myvertex.extend([
					 (-rightAnglePoint.x + offsetX , -rightAnglePoint.y + offsetY, -deltaZRightAngle)
					 ])
		myfaces = [(0, 1, 2, 3, 4)]
	elif overhang_style == 'level_cut': # plumb and level-cut, one vertex more
		myvertex.extend([
					 (-ueberpoint.x + offsetX , -ueberpoint.y + offsetY, -(tan(radians(angle))*ueber) + (deltaZHeightFirst / 2)),
					 (-levelCutPoint.x + offsetX , -levelCutPoint.y + offsetY, -(tan(radians(angle))*ueber) + (deltaZHeightFirst / 2))
					 ])
		myfaces = [(0, 1, 2, 3, 4, 5)]
	
	 
	# other side of rafter
	myvertex.extend([(0 - offsetX, -offsetY, 0), 
					 (endvertex.x - offsetX, endvertex.y - offsetY, tan(radians(angle))*d ),
					 (endvertex.x - offsetX, endvertex.y - offsetY, tan(radians(angle))*d + deltaZHeightFirst),
					 (-ueberpoint.x - offsetX, -ueberpoint.y - offsetY, -(tan(radians(angle))*ueber) + deltaZHeightFirst )
					 ])
					 
	if overhang_style == 'plumb_cut': # straight lotrecht
		myvertex.extend([
					 (-ueberpoint.x - offsetX, -ueberpoint.y - offsetY, -(tan(radians(angle))*ueber) )
					 ])
		myfaces.extend([(5, 6, 7, 8, 9)])
	elif overhang_style == 'tail_cut': # right-angle
		myvertex.extend([
					 (-rightAnglePoint.x - offsetX , -rightAnglePoint.y - offsetY, -deltaZRightAngle)
					 ])
		myfaces.extend([(5, 6, 7, 8, 9)])
	elif overhang_style == 'level_cut': # plumb and level-cut, one vertex more
		myvertex.extend([
					 (-ueberpoint.x - offsetX , -ueberpoint.y - offsetY, -(tan(radians(angle))*ueber) + (deltaZHeightFirst / 2)),
					 (-levelCutPoint.x - offsetX , -levelCutPoint.y - offsetY, -(tan(radians(angle))*ueber) + (deltaZHeightFirst / 2))
					 ])
		myfaces.extend([(6, 7, 8, 9, 10, 11)])
		
	if overhang_style == 'tail_cut' or overhang_style == 'plumb_cut':
		myfaces.extend([(3, 2, 7, 8, 3)])#oben
		myfaces.extend([(0, 1, 6, 5, 9, 4)])#unten
		myfaces.extend([(1, 2, 7, 6)])
		myfaces.extend([(3, 4, 9, 8)])
	
	if overhang_style == 'level_cut':
		myfaces.extend([(3, 2, 8, 9)])#oben
		myfaces.extend([(0, 1, 7, 6, 11, 10, 4, 5)])#unten
		myfaces.extend([(4, 10, 9, 3)]) # plumb cut
		myfaces.extend([(4, 5, 11, 10)]) # level-cut
		myfaces.extend([(1, 7, 8, 2)]) # First
	
	v = len(myvertex)
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)



#
# Operator for Add-Mesh
#
class SEBITEILE_OT_RAFTER(Operator):
	bl_idname = "mesh.sebiteile_rafter"
	bl_label = "Sparren"
	bl_description = "Rafter Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
	bl_property = "angle"
	
	#text: bpy.props.StringProperty(name="Name", default="")
	type: bpy.props.StringProperty(name="Type", default="Rafter")
	angle: FloatProperty(name="Roof-Angle", default = 45.0)
	ueber: FloatProperty(name="Überstand", default = 0.5)
	
	@classmethod
	def poll(cls, context):
		return True
	
	# -----------------------------------------------------
	# Draw (create UI interface)
	# -----------------------------------------------------
	
	def draw(self, context):
		print("SEBITEILE_OT_RAFTER::draw context: "+str(context))
		
		row = self.layout
		#row.label(text="Winkel")
		row.prop(self, 'angle', text="Dach Winkel")
		row.prop(self, 'ueber', text="Überstand")
	
	# -----------------------------------------------------
	# Execute
	# -----------------------------------------------------
	def execute(self, context):
		print("SEBITEILE_OT_RAFTER::execute rafter_angle: "+str(self.angle))
		print("SEBITEILE_OT_RAFTER::execute as_keywords(): "+str(self.as_keywords() ) )
		
		type = "Rafter"
		
		if bpy.context.mode == "OBJECT":
			
			# fixed size Rafter on cursor-Location
			cursor_loc = bpy.context.scene.cursor.location
			path = [cursor_loc, mathutils.Vector((cursor_loc.x + 2,cursor_loc.y,cursor_loc.z))]
			
			initDic = self.as_keywords()
			initDic['path'] = path
			
			rafter = Rafter(initDic)
			
			rafter.create_object(context)
			
			CtrlLineDrawHandler.install()
			
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
			
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)
		
		
#
# POST_View call
#
def draw_callback(self, context):
		#print("mouse points", len(self.screen_path))
		print("::draw_callback (view) self.mouse_path: ", len(self.mouse_path))
		
		blue = (0.157, 0.565, 1, 1)
		orange = (1.0, 1.0, 0, 1.0)
		
		edges = []
		for index in range(1, len(self.mouse_path)):
			edges.append((index-1, index))
			
		shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
		gpu.state.blend_set('ALPHA')
		#gpu.state.line_width_set(60.0)
		batch = batch_for_shader(shader, 'LINES', {"pos": self.mouse_path}, indices=edges)
		shader.uniform_float("color", blue)
		shader.uniform_float("lineWidth", (3.0))
		shader.uniform_float("viewportSize", (1000, 900))
		batch.draw(shader)
		
		#
		# draw the snapradius
		#
		translated = translateBMesh(self.bmCircle, self.mouse_path[-1])
		
		shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
		batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": translated})
		shader.uniform_float("color", orange)
		batch.draw(shader)
		
		# restore opengl defaults
		gpu.state.line_width_set(1.0)
		gpu.state.blend_set('NONE')

#
# returns List of vertex-coordinates out of the b-mesh
#
def get_coords(bm):
	return [v.co for v in bm.verts]

#
# translates a bmesh, returns new Vector-Coordinates, do not change the original bmesh
#
def translateBMesh(bm, vec):
	vertices = []
	for v in bm.verts:
		nv = v.co.copy()
		vertices.append(nv + vec)
	return vertices
		
#
# POST_PIXEL call
#
def draw_callback_px(self, context):
	print("::draw_callback_px self.mouse_path: ", len(self.mouse_path))
		
	blue = (0.157, 0.565, 1, 1)
	orange = (1.0, 1.0, 0, 1.0)
	pink = (0.7, 0, 0.9, 1.0)
	green = (0.1, 1.0, 0.1, 1.0)
	white = (1.0, 1.0, 1.0, 1.0)
	
	#
	# draw infos for rubber-band: length
	#
	if len(self.mouse_path) > 1:
		
		font_id = 0  # default-font
		
		currentPoint = self.mouse_path[-1]
		lastPoint = self.mouse_path[-2]
		
		region = context.region
		rv3d = context.region_data
			
		currentPoint_2d = location_3d_to_region_2d(region, rv3d, self.mouse_path[-1])
		beforePoint_2d = location_3d_to_region_2d(region, rv3d, self.mouse_path[-2])
		
		
		d = math.sqrt( math.pow(currentPoint[0]-lastPoint[0], 2) + math.pow(currentPoint[1]-lastPoint[1], 2))
		
		dX = (currentPoint_2d[0] - beforePoint_2d[0])
		dY = (currentPoint_2d[1] - beforePoint_2d[1])
		angle = math.atan2(dY, dX)
		
		# draw some text
		blf.position(font_id, beforePoint_2d[0] + dX/2, beforePoint_2d[1] + dY/2, 0)
		blf.size(font_id, 18, 72)
		blf.color(font_id, blue[0], blue[1], blue[2], blue[3])
		
		blf.enable(font_id, blf.ROTATION)
		blf.rotation(font_id, angle)
		
		blf.draw(font_id, str(round(d, 2)))
		
		blf.disable(font_id, blf.ROTATION)
		
	#
	# draw snap-infos
	#
	if self.snapped:
			region = context.region
			rv3d = context.region_data
			
			print("  self.mouse_path[-1]: ",str(self.mouse_path[-1]) )
			
			point_2d = location_3d_to_region_2d(region, rv3d, self.mouse_path[-1])
			print("  point_2d: ",str(point_2d))
			
			# just drawing a single point, we have to draw two of them
			coords = ((point_2d[0], point_2d[1]), (-10, -10))
			print("  coords: ",str(coords) )
			
			shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
			batch = batch_for_shader(shader, 'POINTS', {"pos": coords})
			#shader.bind()
			
			snaphandler = self.snaphandler
			
			if snaphandler.snap_Element == 'VERTEX':
				color = orange
			elif snaphandler.snap_Element == 'EDGE':
				color = pink
			elif snaphandler.snap_Element == 'EDGE_PERPENDICULAR':
				color = green
			elif snaphandler.snap_Element == 'EDGE_MIDPOINT':
				color = green
			elif snaphandler.snap_Element == 'INCREMENT':
				color = green
			else:
				color = white
			
			shader.uniform_float("color", color)
			batch.draw(shader)
		
		
		
	
	#
	# DEBUG Regions
	#
	'''
	colors = [blue, (1, 0,0, 1), (0, 1,0, 1), (0.5, 0.5, 0.5, 1), (0.7, 0.3, 0.7, 1), (0.3, 0.7, 0.3, 1)]
	
	uiRegion = None
	for index, region in enumerate(self.nonValidRegions):
		#print("  region: ",str(region.type))
		
		coords = [(region.x, region.y-20, 0), (region.x + region.width, region.y-20, 0), (region.x + region.width, region.y+region.height-20, 0), (region.x, region.y + region.height - 20, 0)]
		
		edges = [(0,1),(1,2),(2,3),(3,0)]
		shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
		batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=edges)
		shader.uniform_float("color", colors[index])
		batch.draw(shader)
	'''
	


def msgbus_callback(self, context):
	print("tool_settings changed!", self, context)
	self.updateSnapSettings(context)

#
# Modal Operator Class for creating a Rafter JUST Modal
# runs the whole time, until another Tool is selected
#
class SEBITEILE_OT_RAFTERADD(Operator):
	bl_idname = "mesh.sebiteile_rafteradd"
	bl_label = "Rafter"
	bl_description = "simple Rafter Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'INTERNAL'}
	
	firstclick = True
	
	# classvariable
	instance = None
	
	
	
	def __init__(self):
		print("Start")
		print("Start instance: "+str(SEBITEILE_OT_RAFTERADD.instance))

	# is called when the garbage collector happens to be collecting the objects
	def __del__(self):
		print("__del__")
		print("__del__ "+str(self))
		SEBITEILE_OT_RAFTERADD.instance = None
		return None
	
	@classmethod
	def poll(cls, context):
		print("::poll cls: "+str(cls))
		
		if SEBITEILE_OT_RAFTERADD.instance:
			print("  going to return False, already SEBITEILE_OT_RAFTERADD.instance "+str(SEBITEILE_OT_RAFTERADD.instance))
			return False
		
		print("  going to return True")
		return True
		
	@classmethod
	def get_instance(cls, context):
		print("::get_instance cls: "+str(self))
		return self
	
	# 
	# Draw (create UI interface)
	# 
	
	
	# 
	# Execute
	# 
	def execute(self, context):
		
		if bpy.context.mode == "OBJECT":
			
			ueber = properties.getValueOrDefault(context.scene.KIMPartAdd, 'ueber')
			angle = properties.getValueOrDefault(context.scene.KIMPartAdd, 'rafter_angle')
			
			initDic = {'ueber': ueber, 'rafter_angle': angle, 'path': self.mouse_path}
			
			print('initDic: '+str(initDic))
			
			self.report( {'INFO'}, 'ueber: %.2f  ' % (ueber) )
			
			rafter = Rafter(initDic)
			rafter.create_object(context)
			
			CtrlLineDrawHandler.install()
			
			#return {'FINISHED'}
		else:
			self.report({'WARNING'}, "Option only valid in Object mode")
			return {'CANCELLED'}
			
	def modal(self, context, event):
		print("::modal "+str((event.mouse_region_x, event.mouse_region_y)))
		print("  event.type: "+str(event.type))
		#global constraint # klappt nicht
		validCoord = True
		
		self.coord = (event.mouse_region_x, event.mouse_region_y) # mouse coordinates in Region WINDOW 
		self.coord2 = (event.mouse_x, event.mouse_y) # mouse coordinates in Area VIEW_3D
		region = context.region
		rv3d = context.space_data.region_3d
		
		# view vector of mouse-position
		vec = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, self.coord)
		
		# mouse-position in 3D view
		origin = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, self.coord)
		
		# 3D locatin on the Working Plane
		self.locPlane = intersectionLinePlane(mathutils.Vector((0,0,1)), mathutils.Vector((0,0,0)), origin, vec)
		
		# first check if the Tool is still active
		isactive = False
		for tool in context.workspace.tools:
			#print("  tool: "+str(tool.idname))
			if tool.idname == 'kim.rafter_tool':
				isactive = True
		
		print("  isactive: "+str(isactive))
		if not isactive:
			self.modal_quit(context)
			return {'FINISHED'}
		
		# is the Mouse in the TOOL_HEADER region ?
		# do not listen to clicks in the TOOL_HEADER
		if self.isValid(self.coord2, self.nonValidRegions ):
			print("  self.isValid: ")
			
			self.shift = event.shift
			
			# checking for mouse and keyboard events
			if event.type == 'MOUSEMOVE':
				print("  event.type: "+str(event.type))
				print("  SHIFT: "+str(event.shift))
				print("  len(self.mouse_path): "+str(len(self.mouse_path)))
				
				context.area.tag_redraw()
				
				
				
				if len(self.mouse_path) == 0:
					self.mouse_path.append(self.locPlane) # at least always one position
				elif len(self.mouse_path) == 1 and self.firstclick: # update coordinate
					self.mouse_path[0] = self.locPlane
					self.update(context)
				elif len(self.mouse_path) > 1: #update according to constraints
					self.update(context)
						
			elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':  # Confirm
					print("  event.type: "+str(event.type)+' value: '+str(event.value))
				
					if self.firstclick:
						print("  firstclick: "+str(len(self.mouse_path)))
						
						self.mouse_path.append(self.locPlane) # first entry
						self.screen_path.append(self.coord)
						
						self.firstclick = False # Reset
						
					elif self.e_pressed: # expand pathes
						print("  LEFTMOUSE and E ")
						self.mouse_path.append(self.locPlane)
						self.screen_path.append(self.coord)
						
						self.e_pressed = False # Reset
						print("  self.mouse_path: "+str(len(self.mouse_path)))
					
					else: # execute
						print("  not firstclick: ")
						print("  self.mouse_path: "+str(len(self.mouse_path)))
						
						result = self.execute(context)
						print("  execute result: "+str(result))
						
						#reset for next wall
						self.mouse_path = []
						self.screen_path = []
						self.firstclick = True # Reset
						self.e_pressed = False
						self.shift = False
						
						# changed behaviour: finish operator 
						#self.modal_quit(context)
						#return {'FINISHED'} # finish this peratr, needs t start a new ne, fr adding wall
				
			elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
				print("  'RIGHTMOUSE', 'ESC' ")
				
				self.mouse_path = []
				self.screen_path = []
				
				context.area.tag_redraw()
				
				#self.modal_quit(context)
				#return {'CANCELLED'} # finish this peratr, , needs t start a new ne, fr adding wall
			elif event.type == 'E':  # Expand
				print("  E")
				self.e_pressed = True
			#else:
				#print("  event.type: "+str(event.type)+' value: '+str(event.value))
		
		return {'PASS_THROUGH'}
	
	
	#
	# Invoke with modal_handler_add
	#
	def invoke(self, context, event):
		print("SEBITEILE_OT_RAFTERADD::invoke event.type: "+str(event.type) )
		print("self: "+str(self) )
		print("SEBITEILE_OT_RAFTERADD.instance: "+str(SEBITEILE_OT_RAFTERADD.instance) )
		#print("::value_update self keys: "+str(self.keys()))
		
		
		#
		# prevent starting a new modal Operator if there is already one running
		#
		if SEBITEILE_OT_RAFTERADD.instance:
			return {'CANCELLED'}
		else:
			SEBITEILE_OT_RAFTERADD.instance = self
		
		self.mouse_path = []
		self.screen_path = []
		self.e_pressed = False
		
		#properties.addListener(self)
		consprops = context.scene.KIMConstraintProperties
		consprops.listener = self
		
		#
		# register drawHandler
		#
		args = (self, context)
		self._handle = SpaceView3D.draw_handler_add(draw_callback, args, "WINDOW", "POST_VIEW")
		self._handle2 = SpaceView3D.draw_handler_add(draw_callback_px, args, "WINDOW", "POST_PIXEL")
		#self._handle3 = SpaceView3D.draw_handler_add(draw_callback_view, args, "WINDOW", "POST_VIEW")
		
		#
		# add as modal-Handler
		#
		self.modal_start(context)
		context.window_manager.modal_handler_add(self)
		
		#
		# get Regions to not listen to mouse-clicks
		#
		self.nonValidRegions = self.getNonValidRegions(context, event)
		
		#
		# reset Constraint-Properties to Standard Values
		#
		consprops = context.scene.KIMConstraintProperties
		consprops.property_unset('constraint')
		print("  consprops: "+str(consprops) )
		
		#
		# init Snaps
		#
		print(' snapElements: '+str(context.tool_settings.snap_elements))
		print(' snap_node_element: '+str(context.tool_settings.snap_node_element))
		print(' snap_target: '+str(context.tool_settings.snap_target))
		
		self.snaphandler = SnapHandler()
		self.snapped = False
		
		self.snaphandler.activate(context.tool_settings.snap_elements)
		self.bmCircle = createSnapCircle(0.2)
		
		#
		# Messagebus listening to Tool_Settings, changing in snap_elements
		#
		subscribe_to = bpy.context.tool_settings

		bpy.msgbus.subscribe_rna(
			key=subscribe_to,
			owner=bpy,
			args=(self, context),
			notify=msgbus_callback,
		)
		
		#
		# set Cursor
		#
		bpy.context.window.cursor_modal_set("DEFAULT")
		
		
		return {'RUNNING_MODAL'}
	
	def updateSnapSettings(self, context):
		print(' updateSnapSettings snapElements: '+str(context.tool_settings.snap_elements))
		print(' snap_node_element: '+str(context.tool_settings.snap_node_element))
		print(' snap_target: '+str(context.tool_settings.snap_target))
		print(' use_snap_grid_absolute: '+str(context.tool_settings.use_snap_grid_absolute))
		
		self.snaphandler.activate(context.tool_settings.snap_elements)
	
	def callSnaps(self, context):
		currentMousePosition = self.coord2
		bpy.ops.view3d.select(extend=False, deselect=True, toggle=False, center=False, enumerate=False, object=False, location=(currentMousePosition[0], currentMousePosition[1]))
		
		
		result = self.snaphandler.snap(self.mouse_path, context.active_object)
			
		return result
	
	#
	# main-update, wertet constraints, Shift-Key and Snaps aus und setzt aktuelle Location 
	#
	def update(self, context):
		print("update ---------")
		
		consprops = context.scene.KIMConstraintProperties
		
		
		
		if consprops.constraint == 'UNDEFINED': # no constraints just set to mouse-location
			self.mouse_path[-1] = self.locPlane # updates the position
			#self.screen_path[-1] = self.coord
			
			# lock to next Snap
			result = self.callSnaps(context)
			print('result '+str(result))
			if result:
				self.mouse_path[-1] = result
				self.snapped = True
			else:
				self.snapped = False
			
			# lock to next angle
			if self.shift and len(self.mouse_path) > 1:
				lastPoint = self.mouse_path[-2]
				currentPoint = self.mouse_path[-1]
				d = math.sqrt(math.pow(currentPoint.x-lastPoint.x, 2)+math.pow(currentPoint.y-lastPoint.y, 2))
				
				delta = self.calculateDeltaByQuadrant(currentPoint, lastPoint, d)
				
				self.mouse_path[-1] =  mathutils.Vector((lastPoint.x + delta[0], lastPoint.y + delta[1], lastPoint.z + delta[2]))
				
						
		elif consprops.constraint == 'DELTAVALUES': # delta constraints: do not set mouselocation
			lastPoint = self.mouse_path[-2]
			self.mouse_path[-1] = mathutils.Vector((lastPoint.x + consprops.dX, lastPoint.y + consprops.dY, lastPoint.z))
			print("::DELTAVALUES "+str(self.mouse_path[-1]))
								
		elif consprops.constraint == 'ANGLE': # angle constraint: calculate length and location by mouse-location
							print("angle constraint "+str(consprops.angle))
							lastSetPoint = self.mouse_path[0]
							
							# get Distance to last Point
							#d = math.sqrt(math.exp(lastTempPoint.x-lastSetPoint.x, 2)+math.exp(lastTempPoint.y-lastSetPoint.y,2))
							d = (self.locPlane - lastSetPoint).length
							print("angle constraint d: "+str(d))
							
							# angle
							dX = math.cos(math.radians(consprops.angle)) * d
							dY = math.sin(math.radians(consprops.angle)) * d
							
							self.mouse_path[-1] =  mathutils.Vector((lastSetPoint.x + dX, lastSetPoint.y + dY, lastSetPoint.z))
							
		elif consprops.constraint == 'LENGTH': # length constraint: calculate length by mouse-location
			print("  length constraint "+str(consprops.length))
			lastSetPoint = self.mouse_path[-2]
							
			dX = (self.locPlane.x - lastSetPoint.x)
			dY = (self.locPlane.y - lastSetPoint.y)
			d = (self.locPlane - lastSetPoint).length
			print("  d: "+str(d))
							
			factor = consprops.length / d
			print("  factor: "+str(factor))
							
			ndX = factor * dX
			ndY = factor * dY
			self.mouse_path[-1] = mathutils.Vector((lastSetPoint.x + ndX, lastSetPoint.y + ndY, lastSetPoint.z))
			
			# lock to next angle
			if self.shift:
				delta = self.calculateDeltaByQuadrant(self.locPlane, lastSetPoint, consprops.length)
				self.mouse_path[-1] =  mathutils.Vector((lastSetPoint.x + delta[0], lastSetPoint.y + delta[1], lastSetPoint.z + delta[2]))
							
		elif consprops.constraint == 'ANGLE_LENGTH': # length constraint: calculate length and location by mouse-location
							print("angle+length constraint")
							lastSetPoint = self.mouse_path[0]
							
							d = consprops.length
							print("angle+length constraint d: "+str(d))
							
							# angle
							dX = math.cos(math.radians(consprops.angle)) * d
							dY = math.sin(math.radians(consprops.angle)) * d
							
							self.mouse_path[-1] =  mathutils.Vector((lastSetPoint.x + dX, lastSetPoint.y + dY, lastSetPoint.z))
							
		
	def modal_start(self,context,):
		print("modal_start")
		return None

	def modal_quit(self,context,):
		print("modal_quit")
		
		# resetting fr pssible next instance
		SEBITEILE_OT_RAFTERADD.instance = None
		
		# remove draw-handlers
		bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
		bpy.types.SpaceView3D.draw_handler_remove(self._handle2, 'WINDOW')
		#bpy.types.SpaceView3D.draw_handler_remove(self._handle3, 'WINDOW')
		
		# clear MessageBus Listeners
		bpy.msgbus.clear_by_owner(bpy)
		
		# restore cursor
		bpy.context.window.cursor_modal_restore()
		
		return None
		
	
	def calculateDeltaByQuadrant(self, currentPoint, lastPoint, d):
		#d = math.sqrt(math.pow(currentPoint.x-lastPoint.x, 2)+math.pow(currentPoint.y-lastPoint.y, 2))
		#d = (self.locPlane - lastSetPoint).length
		dX = (currentPoint.x - lastPoint.x)
		dY = (currentPoint.y - lastPoint.y)
		
		angle = math.atan2(dY, dX)
		print("angle: "+str(math.degrees(angle)))
				
		if 45 > math.degrees(angle) > -45:
					# angle
			dXn = math.cos(math.radians(0)) * d
			dYn = math.sin(math.radians(0)) * d
		elif 135 > math.degrees(angle) > 45:
					# angle
			dXn = math.cos(math.radians(90)) * d
			dYn = math.sin(math.radians(90)) * d
		elif math.degrees(angle) > 135 or math.degrees(angle) < -135:
					# angle
			dXn = math.cos(math.radians(180)) * d
			dYn = math.sin(math.radians(180)) * d
		elif math.degrees(angle) > -135 and math.degrees(angle) < -45:
					# angle
			dXn = math.cos(math.radians(270)) * d
			dYn = math.sin(math.radians(270)) * d
		else:
			dXn = dX
			dYn = dY
					
		return (dXn, dYn, 0)
		
	def getNearestVertex(self):
		currentMousePosition = self.coord2
		bpy.ops.view3d.select(extend=False, deselect=False, toggle=False, center=False, enumerate=False, object=False, location=(currentMousePosition[0], currentMousePosition[1]))
	
	#
	# check if mouse-position is in Tool-Header
	#
	def getNonValidRegions(self, context, event):
		print("::getNonValidRegions : ")
		
		coord = (event.mouse_region_x, event.mouse_region_y)
		region = context.region
		self.my_area = context.area
		
		nonValidRegions =[]
		uiregion = None
		
		for r in self.my_area.regions:
			if r.type in ["TOOL_HEADER", "TOOLS", "UI", "HUD"]:
				nonValidRegions.append(ValidRegion(r))
			if r.type == "UI":
				uiregion = r
		
		# add a custom Navigation-Gizmo Region
		reg = ValidRegion(None, alignRegion = uiregion)
		reg.width = 80
		reg.height = 80
		reg.offset = [11,11]
		nonValidRegions.append(reg)
		
		# add a custom 3D-View Region
		reg = ValidRegion(None, alignRegion = uiregion)
		reg.width = 30
		reg.height = 120
		reg.offset = [8,91]
		nonValidRegions.append(reg)
		
		return nonValidRegions
		
		
	def isValid(self, mouseCoord, nonValidRegions):
		mouseX = mouseCoord[0]
		mouseY = mouseCoord[1]
		
		#first check if outside of area:
		if self.my_area.y + self.my_area.height < mouseY or mouseY < self.my_area.y or mouseX < self.my_area.x or mouseX > self.my_area.x + self.my_area.width:
				return False
		
		# second check if inside of non-valid regions:
		for region in nonValidRegions:
			if region.y + region.height > mouseY > region.y and mouseX > region.x and mouseX < region.x + region.width:
				return False
				
		return True




#
# Wrapper-Class for bpy.types.Region
#
class ValidRegion:

	region = None #bpy.types.Region
	type = 'CUSTOM'
	alignRegion = None # bpy.types.Region, this region is aligned to another one: example:Navigation Gizmo is always besides the UI-Panel
	alignment = 'RIGHT' # bisher nur RIGHT-TOP alignment, attribute wird nicht ausgewertet
	offset = [0,0] # offset to the alignRegion: x,y - Offset
	
	
	def __init__(self, region, alignRegion=None):
		self.region = region
		self.alignRegion = alignRegion
		self.alignment = 'RIGHT'
		
		if self.region:
			self.type = self.region.type
		elif self.alignRegion:
			self.type = self.alignRegion.type + "_ALIGNED"
		else:
			self.type = 'CUSTOM'
	
	#
	# wrapper for region.x oder aligned-Region.x+/-width oder constant x
	# 
	@property
	def x(self):
		if self.region:
			return self.region.x
		elif self.alignRegion:
			# gehe von RIGHT Alignment aus
			return self.alignRegion.x - self.width - self.offset[0] # x-offset
		else: # constant Region
			return self._x
			
	@x.setter
	def x(self, value):
		self._x = value
			
	@property
	def y(self):
		if self.region:
			return self.region.y
		elif self.alignRegion:
			# gehe von RIGHT Alignment aus
			return self.alignRegion.y + self.alignRegion.height - self.height - self.offset[1] # y-offset
		else: # constant Region
			return self._y
			
	@y.setter
	def y(self, value):
		self._y = value
	
	@property		
	def width(self):
		if self.region:
			return self.region.width
		else:
			return self._width
			
	@width.setter
	def width(self, value):
		self._width = value
			
	@property		
	def height(self):
		if self.region:
			return self.region.height
		else:
			return self._height
			
	@height.setter
	def height(self, value):
		self._height = value
	
	


		
class HeightItem(PropertyGroup):
	value: bpy.props.FloatProperty(name="height", default=2.4)		
		

#
# the mesh was changed by User Interaction
# change the Properties and fires a Update - Zyklus 
#
def mesh_update(edit_obj, scene):
	global lastcoords
	
	edit_mesh = edit_obj.data
	bm = bmesh.from_edit_mesh(edit_obj.data)
	verts = bm.verts
	
	print("::mesh_update len verts: "+str(len(verts)))
	print("::mesh_update lastcoords: "+str(lastcoords))
	
	mainobject = edit_obj.parent
	
	mp = mainobject.KIMPartProps
	
	if len(verts) != lastcoords: # first check, if a vertex is added or removed
		updateFromCtrlLine(mainobject, edit_obj)
		lastcoords = verts
	else: # second check: Coordinate of Vertices are changed
		for index, v  in enumerate(verts):
			if v != lastcoords[index]:
				print("::mesh_update v: "+str(v)+" lastcoords: "+str(lastcoords[index]))
				updateFromCtrlLine(mainobject, edit_obj)
				lastcoords = verts
				break
	
	
#
# updates just the mesh of the main-Object - no Ctrl-Line!
#
def updateFromCtrlLine(mainobject, ctrl_obj):
	print("::updateFromCtrlLine: "+str(mainobject.name))
	
	
	mp = mainobject.KIMPartProps
	print("::updateFromCtrlLine mp.type: "+str(mp.type))
	
	
	oldmesh = mainobject.data
	oldname = mainobject.data.name
			
	# and we create a new mesh
	tmp_mesh = bpy.data.meshes.new("temp")
	tmp_mesh.name = oldname
	
	# generate new mesh for Rafter
	ctrl_path = getVertsCo(ctrl_obj)
	
	generate_Rafter2(mp, tmp_mesh, ctrl_path)
		
	mainobject.data = tmp_mesh # ersetze mesh hier
	
	tmp_mesh.name = oldname
	

def show_enum_values(obj, prop_name):
	print([item.name for item in obj.bl_rna.properties[prop_name].enum_items])


	

		
	