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
from .properties import KIMPartAttributes
from .snap import SnapHandler
from .snap import createSnapCircle


class ConstraintHandler:


	def __init__(self):
		print('::ConstraintHandler __init__: '+)

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