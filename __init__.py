# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------------------
# Author: Antonio Vazquez (antonioya)
# ----------------------------------------------------------

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
	"name": "sebiBauteile",
	"author": "sebi",
	"location": "View3D > Add Mesh / Sidebar > Create Tab",
	"version": (1, 2, 3),
	"blender": (3, 0, 0),
	"description": "Generate wooden Elements for Architecue",
	"doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/sebiBauteile.html",
	"category": "Add Mesh"
	}

import sys
import os

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
	import importlib
	importlib.reload(sebi_bauteile_maker)
	print("sebi: Reloaded multifiles")
else:
	from . import sebi_bauteile_maker
	from . import SimpleWall
	from . import KIMPartsTool
	from .properties import KIMPartAttributes

	print("sebi: Imported multifiles")


import bpy
from bpy.app.handlers import persistent

from bpy.props import (
		BoolProperty,
		FloatVectorProperty,
		IntProperty,
		FloatProperty,
		StringProperty,
		PointerProperty,
		EnumProperty,
		)
from bpy.types import (
		AddonPreferences,
		Menu,
		Scene,
		VIEW3D_MT_mesh_add,
		WindowManager,
		Object,
		)



# ----------------------------------------------------------
# Registration
# ----------------------------------------------------------


class SEBI_MT_CustomMenuAdd(Menu):
	bl_idname = "VIEW3D_MT_mesh_custom_menu_add"
	bl_label = "sebiBauteile"


	def draw(self, context):
		self.layout.operator_context = 'INVOKE_REGION_WIN'
		self.layout.operator("mesh.sebiteile_planks", text="Brett")
		self.layout.operator("mesh.sebiteile_pillar", text="Stütze")
		self.layout.operator("mesh.sebiteile_beam", text="Balken")
		self.layout.operator("mesh.sebiteile_rafter", text="Sparren")
		self.layout.operator("mesh.sebiteile_simplewallprops", text="simple Wall")

# --------------------------------------------------------------
# Register all operators and panels
# --------------------------------------------------------------

# Define menu
def SebiMenu_func(self, context):
	print("::SebiMenu_func "+str(context))
	layout = self.layout
	layout.separator()
	self.layout.menu("VIEW3D_MT_mesh_custom_menu_add", icon="GROUP")

@persistent
def on_depsgraph_update(scene):
	depsgraph = bpy.context.evaluated_depsgraph_get()
	edit_obj = bpy.context.edit_object
	
	for update in depsgraph.updates:
		
		if update.id.original == edit_obj and update.is_updated_geometry:
			print("::on_depsgraph_update edit_obj: "+str(edit_obj))
			
			print("::on_depsgraph_update parttype: "+str(edit_obj.KIMAttributes.parttype))
			print("::on_depsgraph_update objecttype: "+str(edit_obj.KIMAttributes.objecttype))
			
			if edit_obj.KIMAttributes.objecttype == KIMPartAttributes.CTRLLINE:
				if edit_obj.KIMAttributes.parttype == KIMPartAttributes.WOODENPART:
					sebi_bauteile_maker.mesh_update(edit_obj, scene)
				if edit_obj.KIMAttributes.parttype == KIMPartAttributes.WALL:
					SimpleWall.mesh_update(edit_obj, scene)
			
			
			
			
classes = (
	SEBI_MT_CustomMenuAdd,
	sebi_bauteile_maker.SEBITEILE_OT_PLANKS,
	sebi_bauteile_maker.SEBITEILE_PT_BauteileObjectPanel,
	sebi_bauteile_maker.SEBITEILE_OT_PILLAR,
	sebi_bauteile_maker.SEBITEILE_OT_BEAM,
	sebi_bauteile_maker.SEBITEILE_OT_RAFTER,
	SimpleWall.SEBITEILE_OT_SIMPLEWALL,
	SimpleWall.SEBITEILE_OT_SIMPLEWALLPROPS,
	SimpleWall.SEBITEILE_OT_SIMPLEWALLADD
	
)




def register():
	print("::register 1: ")
	
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

	VIEW3D_MT_mesh_add.append(SebiMenu_func)

	# Make blender call on_depsgraph_update after each
	# update of Blender's internal dependency graph
	bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
	
	print("::register 2: ")


	# Define properties
	# Register Properties
	bpy.utils.register_class(sebiBauteileProperties)
	bpy.types.Scene.sebiBauteile = bpy.props.PointerProperty(type=sebiBauteileProperties)
	
	# Register Properties
	bpy.utils.register_class(KIMPartAttributes)
	Object.KIMAttributes = PointerProperty(type=KIMPartAttributes)
	
	
	bpy.utils.register_class(SimpleWall.HeightItem)
	
	# Register Properties
	bpy.utils.register_class(SimpleWall.SimpleWallObjectProperties)
	Object.KIMSimpleWallProperties = PointerProperty(type=SimpleWall.SimpleWallObjectProperties)
	
	# Register Tool
	bpy.utils.register_tool(KIMPartsTool.KIMPartsTool, after={"builtin.scale_cage"}, separator=True, group=True)
	
	# Register Properties
	bpy.utils.register_class(SimpleWall.ConstraintProperties)
	bpy.types.Scene.KIMConstraintProperties = bpy.props.PointerProperty(type=SimpleWall.ConstraintProperties)
	
	# OpenGL flag
	wm = WindowManager
	# register internal property
	wm.sebi_run_opengl = BoolProperty(default=False)

class sebiBauteileProperties(bpy.types.PropertyGroup):
	sebi_showcustomsize_property = BoolProperty(
			name='Show custom Size Bool Property', 
			default = True
			)# create bool property for switching
	
	sebi_select_only = BoolProperty(
			name="Only selected",
			description="Apply auto holes only to selected objects",
			default=False,
			)
	

	sebi_merge = BoolProperty(
			name="Close walls",
			description="Close walls to create a full closed room",
			default=False,
			)

	sebi_text_color = FloatVectorProperty(
			name="Hint color",
			description="Color for the text and lines",
			default=(0.173, 0.545, 1.0, 1.0),
			min=0.1,
			max=1,
			subtype='COLOR',
			size=4,
			)
	sebi_walltext_color = FloatVectorProperty(
			name="Hint color",
			description="Color for the wall label",
			default=(1, 0.8, 0.1, 1.0),
			min=0.1,
			max=1,
			subtype='COLOR',
			size=4,
			)
	sebi_font_size = IntProperty(
			name="Text Size",
			description="Text size for hints",
			default=14, min=10, max=150,
			)
	sebi_wfont_size = IntProperty(
			name="Text Size",
			description="Text size for wall labels",
			default=16, min=10, max=150,
			)
	sebi_hint_space = FloatProperty(
			name='Separation', min=0, max=5, default=0.1,
			precision=2,
			description='Distance from object to display hint',
			)
	sebi_gl_measure = BoolProperty(
			name="Measures",
			description="Display measures",
			default=True,
			)
	sebi_gl_name = BoolProperty(
			name="Names",
			description="Display names",
			default=True,
			)
	sebi_gl_ghost = BoolProperty(
			name="All",
			description="Display measures for all objects,"
			" not only selected",
			default=True,
			)
			


def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)

	VIEW3D_MT_mesh_add.remove(SebiMenu_func)

	# Remove properties
	del Scene.sebiBauteile
	
	bpy.utils.unregister_tool(KIMPartsTool.KIMPartsTool)
	
	# remove OpenGL data
	#achm_main_panel.ARCHIMESH_OT_HintDisplay.handle_remove(achm_main_panel.ARCHIMESH_OT_HintDisplay, bpy.context)
	
	#wm = bpy.context.window_manager
	#p = 'archimesh_run_opengl'
	#if p in wm:
	#	del wm[p]


if __name__ == '__main__':
	register()
