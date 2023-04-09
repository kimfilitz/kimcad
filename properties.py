import bpy
from bpy.props import (
		BoolProperty,
		FloatVectorProperty,
		IntProperty,
		FloatProperty,
		StringProperty,
		PointerProperty,
		EnumProperty,
		)


class KIMPartAttributes(bpy.types.PropertyGroup):
	
	UNDEFINED = 'UNDEFINED'
	WALL = 'WALL'
	WOODENPART = 'PART'
	
	MAINOBJECT = 'MAINOBJECT'
	CTRLLINE = 'CTRL-LINE'
	
	parttype: StringProperty(
			name="parttype",
			default='UNDEFINED',
			description="Defines the Type of this Object",
			)
	objecttype: StringProperty(
			name="objecttype",
			default='UNDEFINED',
			description="Defines the Type of this Object",
			)