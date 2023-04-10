import os
import bpy
from bpy.types import WorkSpaceTool
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty



class KIMPartsTool(WorkSpaceTool):
	bl_space_type = 'VIEW_3D'
	bl_context_mode = 'OBJECT'

	# The prefix of the idname should be your add-on name.
	bl_idname = "kim.parts_tool"
	bl_label = "add Simple Wall"
	bl_description = (
		"adds a simple Wall"
	)
	bl_icon = os.path.join(os.path.dirname(__file__), "ops.mesh.sebiteile_simplewalladd")
	bl_widget = None
	bl_keymap = (
		("mesh.sebiteile_simplewalladd", {"type": 'MOUSEMOVE', "value": 'ANY'}, {"properties": []}), # start Operator instantly
		#("mesh.sebiteile_simplewalladd", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": []}), # start modal operator only with LeftMouseClick
		 
	)
	
	def __init__(self):
		print("Start")

	# called when the operator has finished
	def __del__(self):
		print("__del__")
		return None
	
	@classmethod
	def poll(cls, context):
		print("KIMPartsTool::poll cls: "+str(cls))
		return True
		
	def install(cls):
		print("KIMPartsTool::install cls: "+str(cls))

	@classmethod
	def uninstall(cls):
		print("KIMPartsTool::install cls: "+str(cls))

	def draw_settings(context, layout, tool):
	
		print("::draw_settings tool: "+str(tool))
	
		#props = tool.operator_properties("mesh.sebiteile_simplewalladd")
		#props = layout.operator('mesh.sebiteile_simplewalladd')
		props = context.scene.KIMConstraintProperties
		
		layout.activate_init = True
		#row = cls.layout.row(align=True)
		layout.prop(props, 'width', text="Breite")
		layout.active_default = True
		layout.prop(props, 'dX', text="dX")
		layout.prop(props, 'dY', text="dY")
		layout.prop(props, "angle", text="angle")
		layout.prop(props, "angle_length", text="+")
		layout.prop(props, "length", text="length")
		
