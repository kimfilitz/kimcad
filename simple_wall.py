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
from .polygons import intersectionLinePlane
from .properties import KIMPartAttributes
from .snap import VertexSnap, EdgeSnap, SnapHandler
from .snap import createSnapCircle

lastcoords = []

#
# Factory for creating Simple Walls
#
class SimpleWall:
	type = 'SimpleWall'

	def __init__(self, initValues):
		
		self.initDic = initValues
		
		
		
	
	#
	# create main object and mesh
	#	
	def create_object(self, context):

		print("::create_object context: "+str(context))
		print("::create_object self: "+str(self))
		print("::create_object width: "+str(self.initDic.get('width')))
		print("::create_object width: "+str(self.initDic.get('path')))
		
		width = self.initDic.get('width')
		path = self.initDic.get('path')
		
	
		# deselect all objects
		for o in bpy.data.objects:
			o.select_set(False)
		  
		#
		# we create main object and mesh
		#
		mainmesh = bpy.data.meshes.new(self.type)
		
		mainobject = bpy.data.objects.new(self.type, mainmesh)
		#mainobject.location = bpy.context.scene.cursor.location # take cursor location
		mainobject.location = path[0]
		bpy.context.collection.objects.link(mainobject)
		
		#mainobject.SimpleWallProperties.add() # only with CollectionProperty
		
		#print("::create_object mainobject.SimpleWallProperties: "+str(mainobject.KIMSimpleWallProperties))
		
		#mainobject["sebi_bauteile.mainobject"] = True
		
		ma = mainobject.KIMAttributes
		ma.parttype = KIMPartAttributes.WALL
		ma.objecttype = KIMPartAttributes.MAINOBJECT
		
		# we select, and activate, main object
		mainobject.select_set(True)
		bpy.context.view_layer.objects.active = mainobject
	
		# we shape the main object and create other objects as children
		# set Standard -Values
		mp = mainobject.KIMSimpleWallProperties
		mp.update = False #prevent updating before object creation
		
		mp.type = self.type
		mp.width = width
		
		# generate Mesh and Sub-Objects
		#generate_Geometry(mainobject, mainmesh)
		
		#
		# generate sub-object for ctrl-Line
		#
		ctrlmesh = bpy.data.meshes.new("ctrl-Line")
		
		ctrl_o = bpy.data.objects.new("ctrl-Line", ctrlmesh)
		bpy.context.collection.objects.link(ctrl_o)
		
		# configure Collection-Property to detect Controller
		ma = ctrl_o.KIMAttributes
		ma.parttype = KIMPartAttributes.WALL
		ma.objecttype = KIMPartAttributes.CTRLLINE
			
		# create Mesh for control-line
		#self.generate_CtrlLine(ctrl_o, mp, ctrlmesh)
		self.generate_CtrlLine2(ctrl_o, mp, ctrlmesh, path)
			
		
		#ctrl_o["sebi_bauteile.ctrl_line"] = True
		
		#set_normals(ctrl_o)
		ctrl_o.parent = mainobject
		ctrl_o.location.x = 0 # relative to parent
		ctrl_o.location.y = 0
		ctrl_o.location.z = 0
		ctrl_o.lock_location = (True, True, True)
		ctrl_o.lock_rotation = (True, True, True)
		ctrl_o.lock_scale = (True, True, True)
		ctrl_o.display_type = 'WIRE'
		ctrl_o.hide_viewport = False
		ctrl_o.hide_render = True
			
		ctrl_o.data.vertices[0].hide = True
		
		# generate Mesh for simple Wall
		generate_simpleWallMesh(mainobject, mp, mainmesh, ctrl_o)
		
		# at the end, all further changes should be updated
		mp.update = True
		
		
	#
	#
	#
	def generate_CtrlLine(self, mainobject, mp, tmp_mesh):
		global lastcoords
		
		vertices = []
		
		sLength = mp.length
		
		vertices.extend([(0, 0, 0), 
						 (sLength, 0, 0)
						 ])
						 
		tmp_mesh.from_pydata(vertices, [(0,1)], [])
		
		lastcoords = [(0, 0, 0), (sLength, 0, 0)]
		
	def generate_CtrlLine2(self, mainobject, mp, tmp_mesh, path):
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
# Operator Class for creating a Simple-Wall
#
# Invoke with Property Dialog asking for width of the wall
#
class SEBITEILE_OT_SIMPLEWALLPROPS(Operator):
	bl_idname = "mesh.sebiteile_simplewallprops"
	bl_label = "simple Wall"
	bl_description = "simple Wall Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
	bl_property = "width"
	
	width: FloatProperty(name="Width", default = 0.2)
	
	
	def __init__(self):
		print("Start")

	def __del__(self):
		"""called when the operator has finished"""
		print("__del__")
			
		return None
	
	@classmethod
	def poll(cls, context):
		return True
	
	# 
	# Draw (create UI interface)
	# 
	def draw(self, context):
		print("SEBITEILE_OT_SIMPLEWALL::draw context: "+str(context))
		
		row = self.layout
		row.prop(self, 'width', text="Breite")
	
	# 
	# Execute
	# 
	def execute(self, context):
		print("SEBITEILE_OT_SIMPLEWALL::execute as_keywords(): "+str(self.as_keywords() ) )
		
		self.report(
			{'INFO'}, 'F: %.2f  ' %
			(self.width)
		)
		
		if bpy.context.mode == "OBJECT":
		
			wall = SimpleWall(self.as_keywords())
			wall.create_object(context)
			
			#DecorationsHandler.install(context)
			
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
	#
	# Invoke with Property Dialog
	#
	def invoke(self, context, event):
		print("SEBITEILE_OT_SIMPLEWALLPROPS::invoke event.type: "+str(event.type) )
		
		wm = context.window_manager
		return wm.invoke_props_popup(self,event)

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
	
		
def value_update(self, context):
		print("::value_update "+str(context)+' '+str(self))
		print("::value_update id_data "+str(self.id_data)) 
		self.constraint = 'DELTAVALUES'
		
		# using class-Variable
		cls = SEBITEILE_OT_SIMPLEWALLADD.instance
		#print('cls '+str(cls))
		
		# using class-method
		poll = bpy.ops.mesh.sebiteile_simplewalladd.poll()
		#print('poll '+str(poll))
		
		#print('bpy.ops.mesh.sebiteile_simplewalladd : '+str(bpy.ops.mesh.sebiteile_simplewalladd)) # a function
		
		cls.update(context)
		
		
def angle_update(self, context):
		print("::angle_update ")
		if self.angle_length:
			self.constraint = 'ANGLE_LENGTH'
		else:
			self.constraint = 'ANGLE'
		SEBITEILE_OT_SIMPLEWALLADD.instance.update(context)
		
def length_update(self, context):
		print("::length_update ")
		if self.angle_length:
			self.constraint = 'ANGLE_LENGTH'
		else:
			self.constraint = 'LENGTH'
		SEBITEILE_OT_SIMPLEWALLADD.instance.update(context)
		
def angle_length_update(self, context):
	self.constraint = 'ANGLE_LENGTH'
	SEBITEILE_OT_SIMPLEWALLADD.instance.update(context)
	
	
def msgbus_callback(self, context):
	print("tool_settings changed!", self, context)
	self.updateSnapSettings(context)

class ConstraintProperties(bpy.types.PropertyGroup):
	dX: FloatProperty(name="dX", default = 0.2, update=value_update)
	dY: FloatProperty(name="dY", default = 0.2, update=value_update)
	
	angle: FloatProperty(name="angle", default = 45, update=angle_update)
	length: FloatProperty(name="length", default = 0.2, update=length_update)
	
	angle_length: BoolProperty(name="angle_length", default = False, update=angle_length_update)
	
	width: FloatProperty(name="Width", default = 0.2)
	
	constraint: StringProperty(name="constraint", default = 'UNDEFINED')



#
# Modal Operator Class for creating a Simple-Wall JUST Modal
# runs the whole time, until another Tool is selected
#
class SEBITEILE_OT_SIMPLEWALLADD(Operator):
	bl_idname = "mesh.sebiteile_simplewalladd"
	bl_label = "simple Wall"
	bl_description = "simple Wall Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'INTERNAL'}
	
	firstclick = True
	
	toolHeaderRegion = None
	
	# classvariable
	instance = None
	
	
	def cb_set(self, value):
		print('cb_set() self: ', self)
		print('cb_set() my_prop, value: ', self.constraint, self.dX, value)
		# Do not do this: self.my_prop = value, because it will cause
		# recursive calling of this callback function
		#values[self.name] = value
		self.constraint = 'DELTAVALUES'
		constraint = 'DELTAVALUES'
		print('cb_set() constraint: ', constraint)
		
		return None
	
	def value_update(self, context):
		print("::value_update "+str(context)+' '+str(self))
		print("::value_update id_data "+str(self.id_data)) 
		self.constraint = 'DELTAVALUES'
		print("::value_update constraint: "+str(self.constraint))
		
		
	def msgbus_callback(self, *args):
		print("tool_settings changed!", args)
		
		
	
	#
	# do not work with a update-function:
	# the 'self' in the update-function does not point to this Operator class
	# maybe instead to a RNA-Struct with the same name
	# it is not possible to access variables in this class from the update-function
	# and it is not possible to acess the current value of these Properties from within this class over self.
	# for example: dX is updated, the update-function is called, which sets the constraint Property over self.constraint=..., 
	# but: from within this class, in the modal-function, i cannot get the correct value over self.constraint
	# the 'selfs' in the update-function and in this class are pointing to differrent bpy_structs
	# the same counts for 'set'-function
	#
	# I think it has something to do that this class is instatiated through a WorkSpaceTool:
	# first trough the keymap and second as props for the UI
	# is there a way to use only one Instance for both Usages (bl_keymap and tool.operator_properties)?
	#
	'''
	width: FloatProperty(name="Width", default = 0.2)
	
	dX: FloatProperty(name="dX", default = 0.2, update=value_update)
	dY: FloatProperty(name="dY", default = 0.2, update=value_update)
	
	angle: FloatProperty(name="angle", default = 45, update=angle_update)
	length: FloatProperty(name="length", default = 0.2, update=length_update)
	
	constraint: StringProperty(name="constraint", default = 'UNDEFINED')
	'''
	
	def __init__(self):
		print("Start")
		print("Start instance: "+str(SEBITEILE_OT_SIMPLEWALLADD.instance))

	# is called when the garbage collector happens to be collecting the objects
	def __del__(self):
		print("__del__")
		print("__del__ "+str(self))
		SEBITEILE_OT_SIMPLEWALLADD.instance = None
		return None
	
	@classmethod
	def poll(cls, context):
		print("::poll cls: "+str(cls))
		
		#
		# Idee mit opsregistry klappt nicht, Operatoren werden dort meist nach Beenden hinzugefügt
		#
		#opsregistry = context.window_manager.operators
		#c_classname = 'MESH_OT_sebiteile_simplewalladd'
		
		# only one instance
		#if c_classname in opsregistry.keys():
		#	print("::poll ging t return False (c_classname in opsregistry.keys())")
		#	return False
			
		if SEBITEILE_OT_SIMPLEWALLADD.instance:
			print("  going to return False, already SEBITEILE_OT_SIMPLEWALLADD.instance "+str(SEBITEILE_OT_SIMPLEWALLADD.instance))
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
		print("SEBITEILE_OT_SIMPLEWALL::execute as_keywords(): "+str(self.as_keywords() ) )
		
		
		
		if bpy.context.mode == "OBJECT":
			
			props = context.scene.KIMConstraintProperties
			print(props.items())
			print(props.keys())
			print(props.values())
			
			items = [item for item in props.items()]
			print(items)
			
			keys = [item for item in props.keys()]
			print(keys)
			
			
			
			set = props.is_property_set('width')
			print(set)
			
			if not set:
				prop = context.scene.KIMConstraintProperties.bl_rna.properties['width']
				print(prop)
				width = prop.default
				print(width)
			else:
				width = props.get('width')
				print(width)
			
			
			initDic = {'width': width, 'path': self.mouse_path}
			
			self.report( {'INFO'}, 'width: %.2f  ' % (width) )
			
			wall = SimpleWall(initDic)
			wall.create_object(context)
			
			#DecorationsHandler.install(context)
			
			#return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
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
			if tool.idname == 'kim.parts_tool':
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
		print("SEBITEILE_OT_SIMPLEWALLADD::invoke event.type: "+str(event.type) )
		print("self: "+str(self) )
		print("SEBITEILE_OT_SIMPLEWALLADD.instance: "+str(SEBITEILE_OT_SIMPLEWALLADD.instance) )
		#print("::value_update self keys: "+str(self.keys()))
		
		print("RNA subclass: "+str(Operator.bl_rna_get_subclass_py('mesh.sebiteile_simplewalladd')))
		
		#
		# prevent starting a new modal Operator if there is already one running
		#
		if SEBITEILE_OT_SIMPLEWALLADD.instance:
			return {'CANCELLED'}
		else:
			SEBITEILE_OT_SIMPLEWALLADD.instance = self
		
		self.mouse_path = []
		self.screen_path = []
		self.e_pressed = False
		
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
		SEBITEILE_OT_SIMPLEWALLADD.instance = None
		
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
	
	

#
# Update main mesh and children objects
#
def update_object(self, context):
	
	print("::update_object ")
	
	o = context.active_object
	
	mattr = o.KIMAttributes
	
	print("::update_object "+str(mattr.objecttype))
	
	if mattr.objecttype == "1":

		mp = o.KIMSimpleWallProperties
		
		if mp.update:
			
			oldmesh = o.data
			oldname = o.data.name
			
			# Now we select that object to not delete it.
			o.select_set(True)
			bpy.context.view_layer.objects.active = o
			
			# and we create a new mesh
			tmp_mesh = bpy.data.meshes.new("temp")
			
			print("::update_object width: "+str(mp.width)+", "+str(mp.height)+", "+str(mp.depth))
			
			
			o.data = tmp_mesh
			
			# Finally we create all that again (except main object),
			generate_simpleWallMesh(o, mp, tmp_mesh, None)
			
			
			# Remove data (mesh of active object),
			#bpy.data.meshes.remove(oldmesh)
			tmp_mesh.name = oldname
			# and select, and activate, the main object
			o.select_set(True)
			bpy.context.view_layer.objects.active = o
	
	elif mattr.objecttype == "2":
		mainobject = o.parent
		updateFromCtrlLine(mainobject, o)
		
class HeightItem(PropertyGroup):
	value: bpy.props.FloatProperty(name="height", default=2.4)		
		
#
# Define property group class to create or modify
#
class SimpleWallObjectProperties(PropertyGroup):
	
	update: BoolProperty(
			name="should update",
			description="update Objects when true",
			default=False,
			)
			
	type: StringProperty(
			name='Type',
			default="SimpleWall",
			description='Type of Part',
			)
	
	width: FloatProperty(
			name='Width',
			min=0.01, max=0.20,
			default=0.15, precision=3,
			description='Part width',
			update=update_object,
			)
	
	height: FloatProperty(
			name='Height',
			min=0.01, max=6.00,
			default=2.40, precision=3,
			description='overall Wall height',
			update=update_object,
			)
			
	heights: EnumProperty(
			items=(
				('1', "2.40", ""),
			),
			name="heights",
			default='1',
			description="Definiert Höhen dieser Wand",
			update=update_object,
			)
			
	heightsCollection: CollectionProperty(type=HeightItem)
			
	length: FloatProperty(
			name='Length',
			min=0.1, max=6,
			default=2.0, precision=3,
			description='Part length',
			update=update_object,
			)
			
	standards: EnumProperty(
			items=(
				('1', "0.115", "MW 11.5"),
				('2', "0.24", "MW 24"),
			),
			name="standards",
			default='1',
			description="Definiert Breite und Art dieser Wand",
			update=update_object,
			)
	
	# Materials
	crt_mat: BoolProperty(
			name="Create default Cycles materials",
			description="Create default materials for Cycles render",
			default=True,
			update=update_object,
			)
	
	# opengl internal data
	glpoint_a: FloatVectorProperty(
			name="glpointa",
			description="Hidden property for opengl",
			default=(0, 0, 0),
			)
	glpoint_b: FloatVectorProperty(
			name="glpointb",
			description="Hidden property for opengl",
			default=(0, 0, 0),
			)
	glpoint_c: FloatVectorProperty(
			name="glpointc",
			description="Hidden property for opengl",
			default=(0, 0, 0),
			)
			




#
# the mesh was changed by User Interaction
# change the wall properties and fires a Update - Zyklus 
#


def mesh_update(edit_obj, scene):
	global lastcoords
	
	edit_mesh = edit_obj.data
	bm = bmesh.from_edit_mesh(edit_obj.data)
	verts = bm.verts
	
	print("::mesh_update len verts: "+str(len(verts)))
	print("::mesh_update lastcoords: "+str(lastcoords))
	
	mainobject = edit_obj.parent
	
	mp = mainobject.KIMSimpleWallProperties
	
	if len(verts) != lastcoords:
		updateFromCtrlLine(mainobject, edit_obj)
		lastcoords = verts
	else:
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
	
	
	mp = mainobject.KIMSimpleWallProperties
	print("::updateFromCtrlLine mp.type: "+str(mp.type))
	
	
	oldmesh = mainobject.data
	oldname = mainobject.data.name
			
	# and we create a new mesh
	tmp_mesh = bpy.data.meshes.new("temp")
		
		
	bm = bmesh.new()
	bm = bmesh.from_edit_mesh(ctrl_obj.data)
	endVertexCo = bm.verts[1].co
	print("::updateFromCtrlLine endVertexCo: " +str(endVertexCo))
	
	# generate mesh for Wall
	generate_simpleWallMesh(mainobject, mp, tmp_mesh, ctrl_obj)
		
	mainobject.data = tmp_mesh # ersetze mesh hier
	
	tmp_mesh.name = oldname
	

def show_enum_values(obj, prop_name):
	print([item.name for item in obj.bl_rna.properties[prop_name].enum_items])

def generate_simpleWallMesh(mainobject, mp, tmp_mesh, ctrl_o):
	myvertex = []
	myfaces = []
	v = 0
	
	print("::generate_simpleWallMesh ")
	print("::generate_simpleWallMesh mode: "+str(bpy.context.object.mode))
	bm = bmesh.new()
	
	current_mode = ctrl_o.mode
	if current_mode == 'OBJECT':
		bm.from_mesh(ctrl_o.data)
		bm.verts.ensure_lookup_table()
	elif current_mode == 'EDIT':
		bm = bmesh.from_edit_mesh(ctrl_o.data)
	
	v = len(bm.verts)
	
	sWidth = mp.width
	sLength = mp.length
	sHeight = mp.height
	
	print("::generate_simpleWallMesh %f %f %f " % (sWidth, sHeight, sLength))
	
	
	
	endVertexCo = bm.verts[1].co
	print("::generate_simpleWallMesh endVertexCo: " +str(endVertexCo))
	
	# generating coordinate List from the cotrl-Line
	vertsCosList = [item.co for item in bm.verts]
	print("::generate_simpleWallMesh vertsCosList: " +str(vertsCosList))
	
	newPoints = polygons.offset(sWidth/2, vertsCosList)
	myvertex.extend(newPoints)
	
	newPoints2 = polygons.offset(-sWidth/2, vertsCosList)
	
	print("::generate_simpleWallMesh newPoints -offset: " +str(newPoints))
	
	myvertex.extend(newPoints2[::-1]) # reverse order
	
	# Höhen
	show_enum_values(mainobject.KIMSimpleWallProperties, 'heights')
	
	heightvertices = []
	for vertex in myvertex:
		newvertex = mathutils.Vector((vertex.x, vertex.y, vertex.z + sHeight))
		heightvertices.append(newvertex)
		
	myvertex.extend(heightvertices)
	
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	#myvertex.extend([(0, -sWidth/2, 0), 
	#				(endVertexCo.x, -sWidth/2, 0),
	#				(endVertexCo.x, sWidth/2, 0),
	#				(0, sWidth/2, 0)])
	bottomface = []
	for index in range(0, 2*v):
		bottomface.append(index)
							 
	tuple1 = tuple(bottomface)						 
	myfaces = [tuple1]
	
	topface = []
	for index in range(2*v, 2*2*v):
		topface.append(index)
	tuple2 = tuple(topface)						 
	myfaces.extend([tuple2])
	
	#side-faces
	for index in range(1,v):
		face = [(index-1, index, index+2*v, index+2*v-1)]
		myfaces.extend(face)
		face = [(index+v-1, index+v, index+3*v, index+3*v-1)]
		myfaces.extend(face)
		
	#end-faces
	face = [(v-1, v, 3*v, 3*v-1)]
	myfaces.extend(face)
	face = [(2*v-1, 0, 2*v, 4*v-1)]
	myfaces.extend(face)
	
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)
	

		
	