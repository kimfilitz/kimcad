import bpy
from bpy.types import PropertyGroup, Object
from bpy.props import (
		BoolProperty,
		FloatVectorProperty,
		IntProperty,
		FloatProperty,
		StringProperty,
		PointerProperty,
		EnumProperty,
		)

# class Listener
listener = None


	
def getValueOrDefault(props, identifier):
	# get Default-Value for ueber if not set
			set = props.is_property_set(identifier)
			print(set)
			
			if not set:
				prop = props.bl_rna.properties[identifier]
				print('prop: '+str(prop))
				value = prop.default
			else:
				value = props.get(identifier)
				
			return value

class KIMPartAttributes(bpy.types.PropertyGroup):
	
	UNDEFINED = 'UNDEFINED'
	WALL = 'WALL'
	WOODENPART = 'PART'
	RAFTER = 'RAFTER'
	
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
			
			
def value_update(self, context):
	print("::value_update "+str(context)+' '+str(self))
	print("::value_update id_data "+str(self.id_data)) 
	self.constraint = 'DELTAVALUES'
		
	self.listener.update(context)
		
		
def angle_update(self, context):
	print("::angle_update ")
	if self.angle_length:
		self.constraint = 'ANGLE_LENGTH'
	else:
		self.constraint = 'ANGLE'
	self.listener.update(context)
		
def length_update(self, context):
	print("::length_update ")
	if self.angle_length:
		self.constraint = 'ANGLE_LENGTH'
	else:
		self.constraint = 'LENGTH'
	self.listener.update(context)
		
def angle_length_update(self, context):
	self.constraint = 'ANGLE_LENGTH'
	self.listener.update(context)
	
	
# 
# Define property group for Drawing Constraints
#
class ConstraintProperties(bpy.types.PropertyGroup):

	listener = None

	dX: FloatProperty(name="dX", default = 0.2, update=value_update)
	dY: FloatProperty(name="dY", default = 0.2, update=value_update)
	
	angle: FloatProperty(name="angle", default = 45, update=angle_update)
	length: FloatProperty(name="length", default = 0.2, update=length_update)
	
	angle_length: BoolProperty(name="angle_length", default = False, update=angle_length_update)
	
	constraint: StringProperty(name="constraint", default = 'UNDEFINED')
	





def update_object(self, context):
	global listener
	print("::update_object self "+str(self))
	print("::update_object self.listener "+str(self.listener))
	print("::update_object global listener "+str(listener))
	
	if self.listener:
		self.listener.update_object(context)
	
	if listener:
		listener.update_object(context)
	
# 
# Define property group class to create or modify
# 
class KIMPartProperties(PropertyGroup):

	listener = None

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
			name='Overhang',
			min=0.0, max=90.0,
			default=0.5, precision=3,
			description='Overhang',
			update=update_object,
			)
	right_angled: BoolProperty(
			name="right-angled",
			description="Rafter cut right-angled?",
			default=False,
			update=update_object,
			)
	level_cut: BoolProperty(
			name="level-cut",
			description="Rafter with level cut?",
			default=False,
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
	overhang_style: EnumProperty(
		items=[
			('tail_cut', 'tail cut', 'Rafter cut right-angled', '', 0),
			('level_cut', 'level cut', 'level and plumb cut', '', 1),
			('plumb_cut', 'plumb cut', 'plumb cut', '', 2),
		],
		default='tail_cut',
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
			
	def getSizeOfElement(self, identifier):
	
		match identifier:
			case '1': return self.width, self.height
			case '2': return 0.1, 0.025
			case '3': return 0.15, 0.025
			case '4': return 0.075, 0.03
			case '5': return 0.125, 0.03
			case '6': return 0.06, 0.100
			case '7': return 0.06, 0.125
			case '8': return 0.06, 0.150
			case '9': return 0.06, 0.175
			case '10': return 0.06, 0.200
			case '11': return 0.06, 0.225
			case '12': return 0.12, 0.12
			case _: return self.width, self.height
			
	def getSize(self):
		return self.getSizeOfElement(self.standards)

# Register
bpy.utils.register_class(KIMPartProperties)
Object.KIMPartProps = PointerProperty(type=KIMPartProperties)


	
