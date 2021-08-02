bl_info = {
	"name" : "Set Vertex Color",
	"author" : "Stanislav Blinov",
	"version" : (1, 1, 0),
	"blender" : (2, 90, 0),
	"description" : "Set vertex color for selected vertices",
	"category" : "Mesh",}

import bpy, bmesh
from bpy.types import Operator
from bpy.props import FloatVectorProperty

## Constants
# Mapping from context.mode to object.mode_set
CONTEXT_MODE_TO_OBJECT_MODE_MAP = {
	"EDIT_MESH" : "EDIT",
	"POSE" : "POSE",
	"SCULPT" : "SCULPT",
	"PAINT_WEIGHT" : "WEIGHT_PAINT",
	"PAINT_VERTEX" : "VERTEX_PAINT",
	"PAINT_TEXTURE" : "TEXTURE_PAINT",
	"PARTICLE" : "PARTICLE_EDIT",
	"OBJECT" : "OBJECT"
}


## Operators
class MESH_xOT_SetVertexColor(Operator):
	bl_idname = "mesh.addon_set_vertex_color"
	bl_label = "Set Vertex Color..."
	bl_options = {'REGISTER', 'UNDO'}
	
	color : FloatVectorProperty(
		name = "Color",
		subtype = 'COLOR',
		min = 0.0,
		max = 1.0,
		size=4,
		default=(0,0,0,1)
	)
	
	@classmethod
	def poll(cls, context):
		return context.mode == 'EDIT_MESH'
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		bm = bmesh.from_edit_mesh(context.object.data)
		
		verts = [ v for v in bm.verts if v.select ]
		
		if verts:
			colors = bm.loops.layers.color.active
			if not colors:
				colors = bm.loops.layers.color.new("Col")
			
			for v in verts:
				for loop in v.link_loops:
					loop[colors] = self.color
			
			bmesh.update_edit_mesh(context.object.data)
			
		return {'FINISHED'}


class MESH_xOT_SetFaceColor(Operator):
	"""Sets selected faces color"""
	bl_idname = "mesh.addon_set_face_color"
	bl_label = "Set Face Color..."
	bl_options = {'REGISTER','UNDO'}
	
	color : FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0)
	
	@classmethod
	def poll(cls, context):
		return context.active_object and context.mode in CONTEXT_MODE_TO_OBJECT_MODE_MAP
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		# startup
		started_in_other_mode = False
		orig_mode = ""
		if context.mode != "PAINT_VERTEX":
			# check if we support this mode
			if not CONTEXT_MODE_TO_OBJECT_MODE_MAP.get(context.mode, None):
				self.report({"ERROR_INVALID_CONTEXT"}, "Please re-run in Object mode.")
				return {"CANCELLED"}
				
			started_in_other_mode = True
			orig_mode = context.mode
		
		# set face masking mode
		selected_mesh_objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
		for obj in selected_mesh_objs:
			if obj.type == "MESH":
				# Set masking to face mode
				obj.data.use_paint_mask = True
		
		# set face color
		context.tool_settings.vertex_paint.brush.color = self.color
		orig_active_obj = context.active_object
		for obj in selected_mesh_objs:
			# Change to obj mode to change active obj
			bpy.ops.object.mode_set(mode='OBJECT')
			context.view_layer.objects.active = obj
			# Change to vert paint mode to set face color
			bpy.ops.object.mode_set(mode='VERTEX_PAINT')
			bpy.ops.paint.vertex_color_set()
		
		context.view_layer.objects.active = orig_active_obj
		
		# go back to orig mode
		if started_in_other_mode:
			bpy.ops.object.mode_set(mode=CONTEXT_MODE_TO_OBJECT_MODE_MAP[orig_mode])
		
		return {'FINISHED'}


## Register
classes = (
	MESH_xOT_SetVertexColor,
	MESH_xOT_SetFaceColor
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	
def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	
if __name__ == "__main__":
	register()
