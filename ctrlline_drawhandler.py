import bpy, bmesh
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import IntProperty, FloatProperty
from bpy.types import SpaceView3D

from .properties import KIMPartAttributes 

class CtrlLineDrawHandler:
	installed = None

	@classmethod
	def install(cls):
		if cls.installed:
			cls.uninstall()
		handler = cls()
		cls.installed = SpaceView3D.draw_handler_add(handler, (), "WINDOW", "POST_VIEW")

	@classmethod
	def uninstall(cls):
		try:
			SpaceView3D.draw_handler_remove(cls.installed, "WINDOW")
		except ValueError:
			pass
		cls.installed = None

	def __call__(self):
		
		object = bpy.context.object
		objects = bpy.context.visible_objects
		active_object = bpy.context.active_object
		
		gpu.state.point_size_set(4.0)
		
		bgl.glEnable(bgl.GL_BLEND)
		bgl.glLineWidth(1)
		bgl.glPointSize(6)
		
		viewport = gpu.state.viewport_get()

		
		print("DecorationsHandler::__call__ objs: "+str(len(bpy.context.visible_objects)))
		print("DecorationsHandler:: viewport: "+str(gpu.state.viewport_get()))
		
		for obj in objects:
			
			
			ma = obj.KIMAttributes
			
			#draw only ctrl-lines
			if ma.objecttype == KIMPartAttributes.CTRLLINE: 
				
	
				white = (1, 1, 1, 1)
				white_t = (1, 1, 1, 0.1)
				green = (0.545, 0.863, 0, 1)
				red = (1, 0.2, 0.322, 1)
				red_t = (1, 0.2, 0.322, 0.1)
				blue = (0.157, 0.565, 1, 1)
				blue_t = (0.157, 0.565, 1, 0.1)
				grey = (0.2, 0.2, 0.2, 1)
	
				self.shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
				gpu.state.blend_set('ALPHA')
				self.shader.uniform_float("lineWidth", (2.0))
				self.shader.uniform_float("viewportSize", (viewport[2], viewport[3]))
	
				verts = []
				selected_edges = []
				unselected_edges = []
				selected_vertices = []
				unselected_vertices = []
	
				if obj.mode == "EDIT":
					bm = bmesh.from_edit_mesh(obj.data)
	
					for vertex in bm.verts:
						co = tuple(obj.matrix_world @ vertex.co)
						verts.append(co)
						if vertex.hide:
							continue
						if vertex.select:
							selected_vertices.append(co)
						else:
							unselected_vertices.append(co)
	
					for edge in bm.edges:
						edge_indices = [v.index for v in edge.verts]
						if edge.hide:
							continue
						if edge.select:
							selected_edges.append(edge_indices)
						else:
							unselected_edges.append(edge_indices)
	
					batch = batch_for_shader(self.shader, "LINES", {"pos": verts}, indices=unselected_edges)
					self.shader.bind()
					self.shader.uniform_float("color", blue)
					batch.draw(self.shader)
	
					batch = batch_for_shader(self.shader, "LINES", {"pos": verts}, indices=selected_edges)
					self.shader.uniform_float("color", green)
					batch.draw(self.shader)
					
					
					shaderPoints = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
					
					batch = batch_for_shader(shaderPoints, "POINTS", {"pos": unselected_vertices})
					shaderPoints.uniform_float("color", blue)
					batch.draw(shaderPoints)
	
					batch = batch_for_shader(shaderPoints, "POINTS", {"pos": selected_vertices})
					shaderPoints.uniform_float("color", white)
					batch.draw(shaderPoints)
				else:
					bm = bmesh.new()
					bm.from_mesh(obj.data)
	
					verts = [tuple(obj.matrix_world @ v.co) for v in bm.verts]
					edges = [tuple([v.index for v in e.verts]) for e in bm.edges]
					
					color = blue
					
					if obj == active_object:
						color = green
						
					batch = batch_for_shader(self.shader, "LINES", {"pos": verts}, indices=edges)
					self.shader.bind()
					self.shader.uniform_float("color", color)
					batch.draw(self.shader)
					
				
	
				if obj.mode != "EDIT":
					bm.free()

 
	