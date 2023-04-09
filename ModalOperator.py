import bpy
from bpy.props import IntProperty, FloatProperty
import bgl, bmesh, mathutils
from mathutils import Vector


class ModalOperator(bpy.types.Operator):
    """Move an object with the mouse, example"""
    bl_idname = "object.modal_operator"
    bl_label = "Simple Modal Operator"

    first_mouse_x = IntProperty()
    first_value = FloatProperty()
    
    locationList = []

    def modal(self, context, event):
        print(event.type)
        if event.type == 'LEFTMOUSE':
            #context.object.location = bpy.context.scene.cursor.location
            worldLocation = mouse_coords_to_3D_view(event.mouse_x, event.mouse_y)
            
            print(worldLocation)
            
            self.locationList.append(worldLocation)
            
            print(self.locationList)

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
        #return {'RUNNING_MODAL'}
        

    def invoke(self, context, event):
        if context.object:
            self.first_mouse_x = event.mouse_x
            self.first_value = context.object.location.x

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}
        
        
"""Functions for the mouse_coords_to_3D_view"""
def get_viewport():
    view = bgl.Buffer(bgl.GL_INT, 4)
    bgl.glGetIntegerv(bgl.GL_VIEWPORT, view)
    return view


def get_modelview_matrix():
    model_matrix = bgl.Buffer(bgl.GL_DOUBLE, [4, 4])
    bgl.glGetDoublev(bgl.GL_MODELVIEW_MATRIX, model_matrix)
    return model_matrix


def get_projection_matrix():
    proj_matrix = bgl.Buffer(bgl.GL_DOUBLE, [4, 4])
    bgl.glGetDoublev(bgl.GL_PROJECTION_MATRIX, proj_matrix)
    return proj_matrix


def get_depth(x, y):
    depth = bgl.Buffer(bgl.GL_FLOAT, [0.0])
    bgl.glReadPixels(x, y, 1, 1, bgl.GL_DEPTH_COMPONENT, bgl.GL_FLOAT, depth)
    return depth


"""Function mouse_coords_to_3D_view"""


def mouse_coords_to_3D_view(x, y):    
    depth = get_depth(x, y)
    #if (depth[0] != 1.0):
    world_x = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    world_y = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    world_z = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    view1 = get_viewport()
    model = get_modelview_matrix()
    proj = get_projection_matrix ()   
    bgl.gluUnProject(x, y, depth[0], 
                     model, proj,
                     view1,
                     world_x, world_y, world_z)
    return (world_x[0], world_y[0], world_z[0])


def coords_3D_to_2D(x, y, z):
    world_x = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    world_y = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    world_z = bgl.Buffer(bgl.GL_DOUBLE, 1, [0.0])
    view3 = get_viewport()
    model1 = get_modelview_matrix()
    proj1 = get_projection_matrix () 
    bgl.gluProject(x, y, z, model1, proj1, view3, world_x, world_y, world_z)
    return (world_x[0], world_y[0], world_z[0])


def register():
    bpy.utils.register_class(ModalOperator)


def unregister():
    bpy.utils.unregister_class(ModalOperator)


if __name__ == "__main__":
    register()
    print("__main__")
    # test call
    bpy.ops.object.modal_operator('INVOKE_DEFAULT')