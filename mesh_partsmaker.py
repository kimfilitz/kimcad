# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------------------
# Author: Kim Filitz
#
# ----------------------------------------------------------
import bpy, bmesh
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from math import pi, radians, sin, cos, tan
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.types import SpaceView3D
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty

from . import properties
from .ctrlline_drawhandler import CtrlLineDrawHandler
from .properties import KIMPartAttributes

from . import rafter

# 
# Define operator class to create object
# 
class SEBITEILE_OT_PLANKS(Operator):
	bl_idname = "mesh.sebiteile_planks"
	bl_label = "Planks"
	bl_description = "Planks Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'UNDO'}

	# -----------------------------------------------------
	# Draw (create UI interface)
	# -----------------------------------------------------

	def draw(self, context):
		print("SEBITEILE_OT_PLANKS::draw context: "+str(context))
		layout = self.layout
		row = layout.row()
		row.label(text="Use Properties panel (N) to define parms", icon='INFO')

	# -----------------------------------------------------
	# Execute
	# -----------------------------------------------------
	def execute(self, context):
		print("SEBITEILE_OT_PLANKS::execute context: "+str(context))
		if bpy.context.mode == "OBJECT":
			create_object(self, context, "Plank")
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
			
class SEBITEILE_OT_PILLAR(Operator):
	bl_idname = "mesh.sebiteile_pillar"
	bl_label = "Pillar"
	bl_description = "Pillar Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'UNDO'}

	# -----------------------------------------------------
	# Draw (create UI interface)
	# -----------------------------------------------------

	def draw(self, context):
		print("SEBITEILE_OT_PILLAR::draw context: "+str(context))
		layout = self.layout
		row = layout.row()
		row.label(text="Use Properties panel (N) to define parms", icon='INFO')

	# -----------------------------------------------------
	# Execute
	# -----------------------------------------------------
	def execute(self, context):
		print("SEBITEILE_OT_PILLAR::execute context: "+str(context))
		if bpy.context.mode == "OBJECT":
			create_object(self, context, "Pillar")
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
class SEBITEILE_OT_BEAM(Operator):
	bl_idname = "mesh.sebiteile_beam"
	bl_label = "Balken"
	bl_description = "Beam Generator"
	bl_category = 'View'
	bl_options = {'REGISTER', 'UNDO'}

	# -----------------------------------------------------
	# Draw (create UI interface)
	# -----------------------------------------------------

	def draw(self, context):
		print("SEBITEILE_OT_BEAM::draw context: "+str(context))
		layout = self.layout
		row = layout.row()
		row.label(text="Use Properties panel (N) to define parms", icon='INFO')

	# -----------------------------------------------------
	# Execute
	# -----------------------------------------------------
	def execute(self, context):
		print("SEBITEILE_OT_BEAM::execute context: "+str(context))
		if bpy.context.mode == "OBJECT":
			create_object(self, context, "Beam")
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
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
			create_rafter_object(self, context, self.as_keywords())
			
			CtrlLineDrawHandler.install()
			
			return {'FINISHED'}
		else:
			self.report({'WARNING'}, "sebiteile: Option only valid in Object mode")
			return {'CANCELLED'}
			
			
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

# ------------------------------------------------------------------------------
#
# Create main object. The other objects will be children of this.
#
# ------------------------------------------------------------------------------
def create_object(self, context, type):


	# deselect all objects
	for o in bpy.data.objects:
		o.select_set(False)

	# we create main object and mesh
	mainmesh = bpy.data.meshes.new(type)
	
	mainobject = bpy.data.objects.new(type, mainmesh)
	mainobject.location = bpy.context.scene.cursor.location
	bpy.context.collection.objects.link(mainobject)
	

	# we select, and activate, main object
	mainobject.select_set(True)
	bpy.context.view_layer.objects.active = mainobject

	# we shape the main object and create other objects as children
	# set Standard -Values
	mp = mainobject.KIMPartProps
	
	if type == "Plank":
		mp.type = "Plank"
		mp.initialstandard = "2"
	elif type == "Beam":
		mp.type = "Beam"
		mp.initialstandard = "6"
	elif type == "Pillar":
		mp.type = "Pillar"
		mp.initialstandard = "11"
		
	generate_Geometry(mainobject, mainmesh)

def create_rafter_object(self, context, keyDic):

	print("::create_rafter_object context: "+str(context))
	print("::create_rafter_object self: "+str(self))
	print("::create_rafter_object angle: "+str(keyDic.get('angle')))
	print("::create_rafter_object type: "+str(keyDic.get('type')))
	print("::create_rafter_object ueber: "+str(keyDic.get('ueber')))
	
	type = keyDic.get('type')
	angle = keyDic.get('angle')
	ueber = keyDic.get('ueber')
	
	

	# deselect all objects
	for o in bpy.data.objects:
		o.select_set(False)
	
	#
	# we create main object and mesh
	#
	mainmesh = bpy.data.meshes.new(type)
	
	mainobject = bpy.data.objects.new(type, mainmesh)
	mainobject.location = bpy.context.scene.cursor.location # take cursor location
	bpy.context.collection.objects.link(mainobject)
	
	
	
	
	#mainobject["sebi_bauteile.mainobject"] = True

	# we select, and activate, main object
	mainobject.select_set(True)
	bpy.context.view_layer.objects.active = mainobject
	
	ma = mainobject.KIMAttributes
	ma.parttype = KIMPartAttributes.WOODENPART
	ma.objecttype = KIMPartAttributes.MAINOBJECT
	
	# we shape the main object and create other objects as children
	# set Standard -Values
	mp = mainobject.KIMPartProps
	mp.update = False #prevent updating before object creation
	
	mp.type = type
	mp.standards = "6"
	mp.rafter_angle = angle
	mp.ueber = ueber
	
	# generate mesh
	generate_Geometry(mainobject, mainmesh)
	
	# at the end, all further changes should be updated
	mp.update = True
	


# ------------------------------------------------------------------------------
#
# Update main mesh and children objects
#
# ------------------------------------------------------------------------------
def update_object(self, context):
	
	
	o = bpy.context.active_object
	
	ma = o.KIMAttributes
	
	if ma.objecttype == KIMPartAttributes.MAINOBJECT: # main Object changed (through Property update)

		mp = o.KIMPartProps
		
		if mp.update:
		
			print("::update_object standards: "+str(mp.standards))
		
			if mp.standards == '1':
				 context.scene.sebi_showcustomsize_property = True
			else:
				 context.scene.sebi_showcustomsize_property = False
		
			# When we update, the active object is the main object
			
			
			oldmesh = o.data
			oldname = o.data.name
			
			# Now we select that object to not delete it.
			o.select_set(True)
			bpy.context.view_layer.objects.active = o
			
			# and we create a new mesh
			tmp_mesh = bpy.data.meshes.new("temp")
			
			print("::update_object width: "+str(mp.width)+", "+str(mp.height)+", "+str(mp.depth))
			
			
			o.data = tmp_mesh # ersetze mesh hier, damit extrude funktioniert (extrude greift auf aktives Objekt mesh zu)
			
			# Finally we create all that again (except main object),
			generate_Geometry(o, tmp_mesh, True)
			
			
			# Remove data (mesh of active object),
			#bpy.data.meshes.remove(oldmesh)
			tmp_mesh.name = oldname
			# and select, and activate, the main object
			o.select_set(True)
			bpy.context.view_layer.objects.active = o
	
	elif ma.objecttype == KIMPartAttributes.CTRLLINE: # ctrl-Line changed
		mainobject = o.parent
		updateFromCtrlLine(mainobject, o)

lastx = 0
lastcoord = []

def mesh_update(edit_obj, scene):
	global lastx
	
	edit_mesh = edit_obj.data
	bm = bmesh.from_edit_mesh(edit_obj.data)
	verts = bm.verts
	
	print("::mesh_update second vertex: "+str(verts[1].co	))
	
	mainobject = edit_obj.parent
	
	mp = mainobject.KIMPartProps
	print("::mesh_update width: "+str(mp.width)+", "+str(mp.height)+", "+str(mp.depth))
	print("::mesh_update verts[1].co.x: "+str(verts[1].co.x))
	
	if verts[1].co.x != lastx:
		print("::mesh_update verts[1].co.x: UN-gleich mit global "+str(lastx))
		mp.depth = verts[1].co.x
		lastx = verts[1].co.x
	else:
		print("::mesh_update verts[1].co.x: gleich mit global "+str(verts[1].co.x))
	
	
	
def updateFromCtrlLine(mainobject, edit_obj):
	print("::updateFromCtrlLine: "+str(mainobject.name))
	
	# updates just the mesh of the main-Object - no Ctrl-Line!
	mp = mainobject.KIMPartProps
	print("::updateFromCtrlLine mp.type: "+str(mp.type))
	if mp.type == "Rafter":
	
		oldmesh = mainobject.data
		oldname = mainobject.data.name
			
		# Now we select that object to not delete it.
		#o.select_set(True)
		#bpy.context.view_layer.objects.active = o
			
		# and we create a new mesh
		tmp_mesh = bpy.data.meshes.new("temp")
		
		# generate mesh for rafter
		generate_Rafter(mainobject, mp, tmp_mesh)
		
		mainobject.data = tmp_mesh # ersetze mesh hier
	
		tmp_mesh.name = oldname
	

# 
# Generate all objects
# For main, it only shapes mesh and creates modifiers (the modifier, only the first time).
# And, for the others, it creates object and mesh.
# 

def generate_Geometry(mainobject, tmp_mesh, update=False):
	
	mp = mainobject.KIMPartProps
	
	print("::generate_Geometry "+str(mp.type))
	print("::generate_Geometry width: "+str(mp.width)+", length: "+str(mp.depth))
	
	if mp.type == "Plank":
		generate_Plank(mainobject, mp, tmp_mesh)
	elif mp.type == "Beam":
		generate_Beam(mainobject, mp, tmp_mesh)
	elif mp.type == "Pillar":
		generate_Pillar(mainobject, mp, tmp_mesh)
	elif mp.type == "Rafter":
		
		# generate mesh for rafter
		generate_Rafter(mainobject, mp, tmp_mesh)
		
		#
		# generate sub-object for ctrl-Line
		#
		ctrlmesh = bpy.data.meshes.new("ctrl-Line")
	
		ctrl_o = bpy.data.objects.new("ctrl-Line", ctrlmesh)
		bpy.context.collection.objects.link(ctrl_o)
		
		# create control-line
		generate_CtrlLine(ctrl_o, mp, ctrlmesh)
		
		# Add custom property to detect Controller
		# ctrl_o["sebi_bauteile.ctrl_line"] = True
		
		ma = ctrl_o.KIMAttributes
		ma.parttype = KIMPartAttributes.WOODENPART
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
		
	
	# deactivate others
	for o in bpy.data.objects:
		if o.select_get() is True and o.name != mainobject.name:
			o.select_set(False)

	return

'''
# ------------------------------------------------------------------
# Define property group class to create or modify
# ------------------------------------------------------------------
class KIMPartProperties(PropertyGroup):
	update: BoolProperty(
			name="should update",
			description="update Objects when true",
			default=False,
			)
	type: StringProperty(
			name='Type',
			default="Beam",
			description='Type of Part',
			)
	
	width: FloatProperty(
			name='Width',
			min=0.01, max=0.20,
			default=0.15, precision=3,
			description='Part width',
			update=update_object,
			)
	depth: FloatProperty(
			name='Depth',
			min=0.1, max=6,
			default=2.0, precision=3,
			description='Part Length',
			update=update_object,
			)
	height: FloatProperty(
			name='Height',
			min=0.01, max=0.30,
			default=0.025, precision=3,
			description='Part height',
			update=update_object,
			)
	rafter_angle: FloatProperty(
			name='Angle',
			min=0.0, max=90.0,
			default=45, precision=3,
			description='Angle of Roof',
			update=update_object,
			)
	ueber: FloatProperty(
			name='ueber',
			min=0.0, max=90.0,
			default=0.5, precision=3,
			description='Überstand',
			update=update_object,
			)
	r: FloatProperty(
			name='Rotation', min=0, max=360, default=0, precision=1,
			description='Part rotation',
			update=update_object,
			)
	standards: EnumProperty(
			items=(
				('1', "custom", ""),
				('2', "25x100", ""),
				('3', "25x150", ""),
				('4', "30x75", ""),
				('5', "30x125", ""),
				('6', "60x100", ""),
				('7', "60x125", ""),
				('8', "60x150", ""),
				('9', "60x175", ""),
				('10', "60x200", ""),
				('11', "60x225", ""),
				('12', "120x120", "")),
			name="standards",
			default='2',
			description="Defines Standard-Größen für Vollholz",
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

# Register
bpy.utils.register_class(KIMPartProperties)
Object.KIMPartProps = PointerProperty(type=KIMPartProperties)

'''


# ------------------------------------------------------------------
# Define panel class to modify object
# ------------------------------------------------------------------
class SEBITEILE_PT_BauteileObjectPanel(Panel):
	bl_idname = "OBJECT_PT_BauteileObjectPanel"
	bl_label = "Holzbauteile"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Create'

	# 
	# Verify if visible
	# 
	@classmethod
	def poll(cls, context):
		o = context.object
		if o is None:
			return False
		if 'KIMPartProps' not in o:
			return False
		else:
			return True

	# 
	# Draw (create UI interface)
	# 
	def draw(self, context):
		o = context.object
		
		
		print("SEBITEILE_PT_BauteileObjectPanel::draw "+str(o))
		
		try:
			if 'KIMPartProps' not in o:
				return
		except:
			return

		layout = self.layout
		if bpy.context.mode == 'EDIT_MESH':
			layout.label(text='Warning: Operator does not work in edit mode.', icon='ERROR')
		else:
			myobjdat = o.KIMPartProps
			space = bpy.context.space_data
			print("SEBITEILE_PT_BauteileObjectPanel myobjdat: "+str(myobjdat))
			
			if myobjdat.type == 'Rafter':
				properties.listener = rafter
				# AttributeError: Writing to ID classes in this context is not allowed: Rafter.001, Object datablock, error setting KIMPartProperties.listener
				#myobjdat.listener = rafter
				
				#setattr(myobjdat, 'listener', rafter)
				# AttributeError: Writing to ID classes in this context is not allowed: Rafter.001, Object datablock, error setting KIMPartProperties.listener

			else:
				properties.listener = __import__(__name__) # set current module as listener to property change
			
			print("SEBITEILE_PT_BauteileObjectPanel myobjdat "+str(myobjdat))
			print("SEBITEILE_PT_BauteileObjectPanel myobjdat.listener "+str(myobjdat.listener))
			print("SEBITEILE_PT_BauteileObjectPanel properties.listener "+str(properties.listener))
				
			if not space.local_view:
				# Imperial units warning
				if bpy.context.scene.unit_settings.system == "IMPERIAL":
					row = layout.row()
					row.label(text="Warning: Imperial units not supported", icon='COLOR_RED')

				box = layout.box()
				box.label(text="Dimensions", icon='MESH_DATA')
				row = box.row()
				row.prop(myobjdat, 'standards')
				
				row = box.row()
				row.label(text="custom size")
				
				row = box.row()
				print("SEBITEILE_PT_BauteileObjectPanel  sebiBauteile: "+str(bpy.context.scene.sebiBauteile))
				print("SEBITEILE_PT_BauteileObjectPanel sebi_showcustomsize_property: "+str(bpy.context.scene.sebiBauteile.sebi_showcustomsize_property))
				
				row.enabled = bpy.context.scene.sebiBauteile.sebi_showcustomsize_property
				
				row.prop(myobjdat, 'width')
				row.prop(myobjdat, 'height')
				
				box = layout.box()
				box.label(text="Rafter", icon='DRIVER_DISTANCE')
				row = box.row()
				row.prop(myobjdat, 'ueber', text="Overhang" )
				row.prop(myobjdat, 'rafter_angle', text="Angle" )
				
				row = box.row()
				row.label(text="define Overhang")
				row = box.row()
				row.prop(myobjdat, 'overhang_style', expand=True)
				
			else:
				row = layout.row()
				row.label(text="Warning: Operator does not work in local view mode", icon='ERROR')
				
	def invoke(self, context, event):
		print("SEBITEILE_PT_BauteileObjectPanel  invole: "+str(bpy.context.scene.sebiBauteile))


def getSizeOfElement(mp, identifier):
	
		match identifier:
			case '1': return mp.width, mp.height, mp.depth
			case '2': return 0.1, 0.025, 2
			case '3': return 0.15, 0.025, 2
			case '4': return 0.075, 0.03, 2
			case '5': return 0.125, 0.03, 2
			case '6': return 0.06, 0.100, mp.depth
			case '7': return 0.06,0.125, mp.depth
			case '8': return 0.06, 0.150, mp.depth
			case '9': return 0.06, 0.175, mp.depth
			case '10': return 0.06, 0.200, mp.depth
			case '11': return 0.06, 0.225, mp.depth
			case '12': return 0.12, 0.12, mp.depth
			case _: return mp.width, mp.height, mp.depth
			
def getSize(mp):
	
	return getSizeOfElement(mp, mp.standards)
	


def generate_Plank(mainobject, mp, tmp_mesh):
	myvertex = []
	myfaces = []
	v = 0
	
	print("::generate_Plank ")
	
	sWidth, sHeight, sLength = getSize(mp)
	print("::generate_Plank %f %f %f " % (sWidth, sHeight, sLength))
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	myvertex.extend([(-sWidth/2, 0, -sHeight/2), (sWidth/2, 0, -sHeight/2),
							 (sWidth/2, 0, sHeight/2),
							 (-sWidth/2, 0, sHeight/2)])
							 
	myfaces = [(0, 1, 2, 3)]
	v = len(myvertex)
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)
	
	extrude(tmp_mesh, mainobject, sLength)
	
def generate_Beam(mainobject, mp, tmp_mesh):
	
	myvertex = []
	myfaces = []
	v = 0
	
	sWidth, sHeight, sLength = getSize(mp)
	print("::generate_Beam %f %f %f " % (sWidth, sHeight, sLength))
	
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	myvertex.extend([(-sWidth/2, 0, -sHeight/2), (sWidth/2, 0, -sHeight/2),
							 (sWidth/2, 0, sHeight/2),
							 (-sWidth/2, 0, sHeight/2)])
							 
	myfaces = [(0, 1, 2, 3)]
	v = len(myvertex)
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)
	
	extrude(tmp_mesh, mainobject, sLength)
	
def generate_Pillar(mainobject, mp, tmp_mesh):
	print("::generate_Beam ")
	
	myvertex = []
	myfaces = []
	v = 0
	
	sWidth, sHeight, sLength = getSize(mp)
	
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	myvertex.extend([(-sWidth/2, -sHeight/2, 0), (sWidth/2, -sHeight/2, 0),
							 (sWidth/2, sHeight/2, 0),
							 (-sWidth/2, sHeight/2, 0)])
							 
	myfaces = [(0, 1, 2, 3)]
	v = len(myvertex)
	
	tmp_mesh.from_pydata(myvertex, [], myfaces)
	tmp_mesh.update(calc_edges=True)
	
	extrude(tmp_mesh, mainobject, sLength)
	
#
# generates a Rafter mesh, with the properties of mp, updates tmp_mesh
#
def generate_Rafter(mainobject, mp, tmp_mesh):
	
	myvertex = []
	myfaces = []
	v = 0
	
	print("::generate_Rafter  mp.rafter_angle: "+str(mp.rafter_angle))
	
	#sLength ist die Spannweite, nicht die gesmatlänge des Sparrens
	sWidth, sHeight, sLength = getSize(mp)
	angle = mp.rafter_angle 
	
	ueber = mp.ueber
	
	deltaXHeight = sin(radians(angle))*sHeight
	deltaZHeight = cos(radians(angle))*sHeight
	
	
	deltaZHeightFirst = sHeight/cos(radians(angle))
	
	#sX = 0.1
	#sY = 0.2
	# in x-z Ebene counter-clockwise
	myvertex.extend([(0, +sWidth/2, 0), 
					 (sLength, +sWidth/2, tan(radians(angle))*sLength ),
					 (sLength, +sWidth/2, tan(radians(angle))*sLength + deltaZHeightFirst),
					 (-ueber - deltaXHeight, +sWidth/2, -(tan(radians(angle))*ueber) + deltaZHeight ),
					 (-ueber, +sWidth/2, -(tan(radians(angle))*ueber) )
					 ])
	myfaces = [(0, 1, 2, 3, 4)]
					 
	myvertex.extend([(0, -sWidth/2, 0), 
					 (sLength, -sWidth/2, tan(radians(angle))*sLength ),
					 (sLength, -sWidth/2, tan(radians(angle))*sLength + deltaZHeightFirst),
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
	
	# extrude(tmp_mesh, mainobject, sLength)

def generate_CtrlLine(object, mp, tmp_mesh):
	vertices = []
	
	#sLength ist die Spannweite, nicht die gesmatlänge des Sparrens
	sWidth, sHeight, sLength = getSize(mp)
	
	vertices.extend([(0, 0, 0), 
					 (sLength, 0, 0)
					 ])
					 
	tmp_mesh.from_pydata(vertices, [(0,1)], [])
	#tmp_mesh.update(calc_edges=True)
	
	
					 
	
def extrude(mesh, mainobject, extrude):
	# Go to edit mode, face selection mode and select all faces
	#scene = bpy.context.scene
	#scene.objects.active = mainobject
	print("::extrude "+str(extrude))
	
	bpy.ops.object.mode_set( mode = 'EDIT' )	 # Toggle edit mode
	bpy.ops.mesh.select_mode( type = 'FACE' )	# Change to face selection
	bpy.ops.mesh.select_all( action = 'SELECT' ) # Select all faces
	
	
	print("::extrude bpy.context.object.data: "+str(bpy.context.object.data))
	
	# Create Bmesh
	bm = bmesh.new()
	bm = bmesh.from_edit_mesh( bpy.context.object.data )
	
	print("::extrude bm: "+str(bm))
	
	# Extude Bmesh
	for f in bm.faces:
		face = f.normal
	r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
	verts = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
	
	TranslateDirection = face * extrude # Extrude Strength/Length
	
	print("::extrude TranslateDirection: "+str(TranslateDirection))
	
	bmesh.ops.translate(bm, vec = TranslateDirection, verts=verts)

	# Update & Destroy Bmesh
	bmesh.update_edit_mesh(bpy.context.object.data) # Write the bmesh back to the mesh
	bm.free()  # free and prevent further access

	# Flip normals
	bpy.ops.mesh.select_all( action = 'SELECT' )
	bpy.ops.mesh.flip_normals() 

	# At end recalculate UV
	bpy.ops.mesh.select_all( action = 'SELECT' )
	bpy.ops.uv.smart_project()

	# Switch back to Object at end
	bpy.ops.object.mode_set( mode = 'OBJECT' )







