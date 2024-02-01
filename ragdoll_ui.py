
import bpy
import sys
sys.path.append("/home/schnollie/Work/bpy/ragdoll_tools")
from ragdoll_aux import rb_constraint_collection_set, load_text, config_create

from ragdoll import rag_doll_create, rag_doll_remove, rag_doll_update, wiggle_const_update
from ragdoll import force_update_drivers, wiggle_spring_drivers_add, wiggle_spring_drivers_remove
from bpy_extras.io_utils import ImportHelper, ExportHelper
import os


class OBJECT_OT_TextBrowseImport(bpy.types.Operator, ImportHelper): 
    bl_idname = "text.import_filebrowser" 
    bl_label = "Open the file browser to open config" 
    filter_glob: bpy.props.StringProperty( 
        default='*.json;', 
        options={'HIDDEN'} 
        ) 
    
    def execute(self, context): 
        load_text(context, self.filepath, None)
        context.view_layer.update()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    

class OBJECT_OT_RagdollJsonAdd(bpy.types.Operator): 
    bl_idname = "text.json_create" 
    bl_label = "New Text"
    bl_options = {'UNDO'}
      
    def execute(self, context): 
        config = config_create(context.object)
        load_text(context, None, config)
        return {'FINISHED'}
    

class OBJECT_OT_AddRigidBodyConstraints(bpy.types.Operator):
    """Creates an Operator to add Rigid Body Constraint Group"""
    bl_idname = "scene.rbconstraints"
    bl_label = "Add Rigid Body Constraints"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        rb_constraint_collection_set('RigidBodyConstraints')
        bpy.context.view_layer.update()
        return {'FINISHED'}


class OBJECT_OT_AddRagDoll(bpy.types.Operator):
    """Creates Ragdoll objects for selected Armature"""
    bl_idname = "armature.ragdoll_add"
    bl_label = "Add Ragdoll"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # main(context.object.data.ragdoll_config)
        rag_doll_create(context.object)
        
        return {'FINISHED'}


class OBJECT_OT_RemoveRagDoll(bpy.types.Operator):
    """Removes Ragdoll from selected Armature"""
    bl_idname = "armature.ragdoll_remove"
    bl_label = "Remove Ragdoll"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        rag_doll_remove(context.object)
        
        return {'FINISHED'}


class OBJECT_OT_UpdateRagDoll(bpy.types.Operator):
    """Update selected Armature's RagDoll"""
    bl_idname = "armature.ragdoll_update"
    bl_label = "Update Ragdoll"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        rag_doll_update(context)
        return {'FINISHED'}


class OBJECT_OT_UpdateDrivers(bpy.types.Operator):
    """Update all armatures Drivers"""
    bl_idname = "armature.update_drivers"
    bl_label = "Update Drivers"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        force_update_drivers(context)
        return {'FINISHED'}


class OBJECT_OT_UpdateWiggles(bpy.types.Operator):
    """Update selected Armature's RagDoll"""
    bl_idname = "armature.wiggle_update"
    bl_label = "Update Wiggles"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        wiggle_update(context)
        return {'FINISHED'}

class OBJECT_OT_AddWiggleDrivers(bpy.types.Operator):
    """Add drivers to wiggle constraints"""
    bl_idname = "armature.wiggle_drivers_add"
    bl_label = "Add Drivers"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        wiggle_spring_drivers_add(context.object)
        context.object.data.ragdoll.wiggle_drivers = True
        print("Info: Added Drivers to Rigid Body Constraints' Spring Settings.")
        return {'FINISHED'}

class OBJECT_OT_RemoveWiggleDrivers(bpy.types.Operator):
    """Add drivers to wiggle constraints"""
    bl_idname = "armature.wiggle_drivers_remove"
    bl_label = "Add Drivers"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        wiggle_spring_drivers_remove(context.object)
        context.object.data.ragdoll.wiggle_drivers = False
        
        print("Info: Removed Drivers from Rigid Body Constraints' Spring Settings.")
        return {'FINISHED'}


class OBJECT_PT_RagDollCollections(bpy.types.Panel):
    """Subpanel to Ragdoll"""
    bl_label = "Collections"
    bl_idname = "OBJECT_PT_ragdollcollections"
    bl_parent_id = "OBJECT_PT_ragdoll"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

    def draw(self, context):
        if context.scene.rigidbody_world and context.scene.rigidbody_world.constraints:         
            layout = self.layout
            row = layout.row()
            split = row.split(factor=0.25)
            col_0 = split.column()
            col_1 = split.column()
            col_0.label(text="Geometry")
            col_1.prop(context.object.data.ragdoll,"rigid_bodies", text="")

            row = layout.row()
            split = row.split(factor=0.25)
            col_2 = split.column()
            col_3 = split.column()
            col_2.label(text="Constraints")
            col_3.prop(context.object.data.ragdoll,"constraints", text="")
            
            row = layout.row()
            split = row.split(factor=0.25)
            col_4 = split.column()
            col_5 = split.column()
            col_4.label(text="Connectors")
            col_5.prop(context.object.data.ragdoll,"connectors", text="")
        

class OBJECT_PT_RagDollSuffixes(bpy.types.Panel):
    """Naming Suffixes for Ragdoll"""
    bl_label = "Postifxes"
    bl_idname = "OBJECT_PT_ragdollsuffixes"
    bl_parent_id = "OBJECT_PT_ragdoll"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        if context.scene.rigidbody_world and context.scene.rigidbody_world.constraints:

            layout = self.layout
            row = layout.row()
            
            split = row.split(factor=0.25)
            col_0 = split.column()
            col_1 = split.column()
            col_0.label(text="Control Rig")
            col_1.prop(context.object.data.ragdoll,"ctrl_rig_suffix", text="")
            
            row = layout.row()
            split = row.split(factor=0.25)
            col_2 = split.column()
            col_3 = split.column()
            col_2.label(text="Geometry")
            col_3.prop(context.object.data.ragdoll,"rb_suffix", text="")
            
            row = layout.row()
            split = row.split(factor=0.25)
            col_4 = split.column()
            col_5 = split.column()
            col_4.label(text="Constraints")
            col_5.prop(context.object.data.ragdoll,"const_suffix", text="")

            row = layout.row()
            split = row.split(factor=0.25)
            col_6 = split.column()
            col_7 = split.column()
            col_6.label(text="Connectors")
            col_7.prop(context.object.data.ragdoll,"connect_suffix", text="")


class OBJECT_PT_RagDoll(bpy.types.Panel):
    """Creates a Panel in the Object Data properties window"""
    bl_label = "Ragdoll"
    bl_idname = "OBJECT_PT_ragdoll"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

    def draw(self, context):
        obj = context.object
        if obj.type == 'ARMATURE':
            layout = self.layout

            if not context.scene.rigidbody_world:
                box = layout.box()
                row = box.row()
                row.label(text="Please add rigid body world first.", icon="ERROR")
                row = box.row()
                row.operator("rigidbody.world_add")
                
            elif not context.scene.rigidbody_world.constraints:
                box = layout.box()
                row = box.row()
                row.label(text="Please add rigid body constraints first.", icon="ERROR")
                row = box.row()
                row.operator("scene.rbconstraints")

            else:
                if context.object.type == 'ARMATURE' and context.object.data.ragdoll != None:
                    if context.scene.rigidbody_world and context.scene.rigidbody_world.constraints: 
                        layout = self.layout        

                        #-------- Config --------
                        config_box = layout.box()
                        config_header_row = config_box.row()
                        config_header_row.label(text="Configuration")
                        row = config_box.row()
                        split = row.split(factor=0.33)
                        col_0 = split.column()
                        col_1 = split.column()

                        row = config_box.row()
                        split = row.split(factor=0.33)
                        col_0 = split.column(align=True)
                        col_1 = split.column()
                        config_label_row = col_0.row()
                        config_text_row = col_1.row()
                        
                        if context.object.data.ragdoll.config and context.object.data.ragdoll.config.is_dirty:
                            if os.path.exists(context.object.data.ragdoll.config.filepath):
                                config_label_row.label(text="Text: External, modified")
                            else:
                                config_label_row.label(text="Text: Internal")

                        else:
                            config_label_row.label(text="Text: External")
                        
                        if context.object.data.ragdoll.type == 'CONTROL' or not context.object.data.ragdoll.control_rig:
                            config_text_row.prop(context.object.data.ragdoll,"config", text="")
                        else:
                            config_text_row.prop(context.object.data.ragdoll.control_rig.data.ragdoll,"config", text="")

                        config_text_row.operator("text.import_filebrowser", text="", icon='FILEBROWSER')
                        config_text_row.operator("text.json_create", text="", icon='FILE_NEW')

                        text_ops_row = col_1.row()
                        if context.object.data.ragdoll.initialized == False:
                            text_ops_row.operator("armature.ragdoll_add", text="Create Ragdoll")
                        else:
                            split = text_ops_row.split(factor=0.33)
                            update_rd_row = split.column().row()
                            update_drivers_row = split.column().row()
                            delete_ragdoll_row = split.column().row()

                            update_rd_row.operator("armature.ragdoll_update", text="Update Ragdoll")
                            update_drivers_row.operator("armature.update_drivers", text="Update Drivers")
                            delete_ragdoll_row.operator("armature.ragdoll_remove", text="Remove Ragdoll")

                        #-------- Geometry --------
                        geo_box = layout.box()
                        row = geo_box.row()
                        row.label(text="Geometry")
                        row = geo_box.row()
                        row.prop(context.object.data.ragdoll, "rb_bone_width_relative", text="Relative Bone Width")
                        row = geo_box.row()
                        row.prop(context.object.data.ragdoll, "rb_bone_width_min", text="Minimum Width")
                        # row.enabled = False

                        row = geo_box.row()
                        row.prop(context.object.data.ragdoll, "rb_bone_width_max", text="Maximum Width")
                        # row.enabled = False

                        if context.object.data.ragdoll.initialized == True:
                            #-------- Animation --------
                            animated_box = layout.box()
                            row = animated_box.row()
                            row.label(text="Animation")
                            split = animated_box.split(factor=0.33)
                            col_1 = split.column()
                            col_2 = split.column()
                            kinematic_row = col_1.row()
                            kinematic_row.prop(context.object.data.ragdoll, "kinematic", text="Animated")
                            anim_override_row = col_2.row()
                            anim_override_row.prop(context.object.data.ragdoll, "simulation_influence", text="Override")

                            #-------- Wiggle --------
                            wiggle_box = layout.box()
                            wiggle_label_row = wiggle_box.row()
                            wiggle_label_row.label(text="Wiggle")
                            wiggle_checkbox_row = wiggle_box.row()
                            wiggle_checkbox_row.prop(context.object.data.ragdoll, "wiggle", text="Use")
                            
                            #------------------------ Constraint Limits ------------------------
                            wiggle_limit_row = wiggle_box.row()
                            split = wiggle_limit_row.split(factor=0.33)
                            wiggle_limit_col_0 = split.column()
                            wiggle_limit_col_1 = split.column()
                            
                            wiggle_restric_lin_row = wiggle_limit_col_0.row()
                            wiggle_restric_lin_row.prop(context.object.data.ragdoll, "wiggle_restrict_linear", text="Limit Linear")

                            wiggle_restric_ang_row = wiggle_limit_col_0.row()
                            wiggle_restric_ang_row.prop(context.object.data.ragdoll, "wiggle_restrict_angular", text="Limit Angular")

                            wiggle_limits_row = wiggle_limit_col_1.row()
                            wiggle_limit_lin_row = wiggle_limits_row.row()
                            wiggle_limit_lin_row.prop(context.object.data.ragdoll, "wiggle_distance", text="Distance")

                            wiggle_limits_row = wiggle_limit_col_1.row()
                            wiggle_limit_ang_row = wiggle_limits_row.row()
                            wiggle_limit_ang_row.prop(context.object.data.ragdoll, "wiggle_rotation", text="Rotation")
                            
                            #------------------------ Constraint Springs ------------------------
                            wiggle_spring_row = wiggle_box.row()
                            split = wiggle_spring_row.split(factor=0.33)
                            wiggle_spring_col_0 = split.column()
                            wiggle_spring_col_1 = split.column()
                            wiggle_spring_row_left_0 = wiggle_spring_col_0.row()
                            wiggle_spring_row_right_0 = wiggle_spring_col_1.row()
                            wiggle_spring_row_left_0.prop(context.object.data.ragdoll, "wiggle_use_springs", text="Springs")
                            wiggle_spring_row_right_0.prop(context.object.data.ragdoll, "wiggle_stiffness", text="Stiffness")
                            wiggle_spring_row_right_0.prop(context.object.data.ragdoll, "wiggle_damping", text="Damping")
                            
                            wiggle_spring_row_right_1 = wiggle_spring_col_1.row()
                            split = wiggle_spring_row_right_1.split(factor=0.5)
                            wiggle_spring_col_0 = split.column()
                            wiggle_spring_col_1 = split.column()
                            wiggle_spring_add_drivers = wiggle_spring_col_0.row()
                            wiggle_spring_remove_drivers = wiggle_spring_col_1.row()
                            wiggle_spring_add_drivers.operator("armature.wiggle_drivers_add", text="Add Drivers", icon='DECORATE_DRIVER')
                            wiggle_spring_remove_drivers.operator("armature.wiggle_drivers_remove", text="Remove Drivers", icon='PANEL_CLOSE')

                            #------------------------ Falloff ------------------------
                            wiggle_falloff_row = wiggle_box.row()
                            split = wiggle_falloff_row.split(factor=0.33)
                            wiggle_falloff_col_0 = split.column()
                            wiggle_falloff_col_1 = split.column()

                            wiggle_falloff_checkbox_row = wiggle_falloff_col_0.row()
                            wiggle_falloff_checkbox_row.prop(context.object.data.ragdoll, "wiggle_use_falloff", text="Falloff")

                            wiggle_falloff_settings_row_0 = wiggle_falloff_col_1.row()
                            wiggle_falloff_settings_row_0.prop(context.object.data.ragdoll, "wiggle_falloff_mode", text="")
                            wiggle_falloff_settings_row_0.prop(context.object.data.ragdoll, "wiggle_falloff_factor", text="Factor")

                            wiggle_falloff_settings_row_1 = wiggle_falloff_col_1.row()
                            split = wiggle_falloff_settings_row_1.split(factor=0.5)
                            col_0 = split.column()
                            col_1 = split.column()
                            wiggle_falloff_settings_row_0b = col_0.row()
                            wiggle_falloff_settings_row_0b.prop(context.object.data.ragdoll, "wiggle_falloff_invert", text="Invert")
                            wiggle_falloff_settings_row_0b.prop(context.object.data.ragdoll, "wiggle_falloff_chain_ends", text="Ends")



                            wiggle_falloff_settings_row_1 = col_1.row()
                            wiggle_falloff_settings_row_1.prop(context.object.data.ragdoll, "wiggle_falloff_offset", text="Offset")

                            #-------- UI States --------
                            wiggle_limit_row.enabled = context.object.data.ragdoll.wiggle
                            wiggle_spring_row.enabled = context.object.data.ragdoll.wiggle
                            wiggle_falloff_row.enabled = context.object.data.ragdoll.wiggle
                            
                            wiggle_limit_lin_row.enabled = context.object.data.ragdoll.wiggle_restrict_linear
                            wiggle_limit_ang_row.enabled = context.object.data.ragdoll.wiggle_restrict_angular
                            wiggle_falloff_settings_row_0.enabled = context.object.data.ragdoll.wiggle_use_falloff
                            wiggle_falloff_settings_row_1.enabled = context.object.data.ragdoll.wiggle_use_falloff
                            wiggle_falloff_settings_row_0b.enabled = context.object.data.ragdoll.wiggle_use_falloff
                            wiggle_spring_row_right_0.enabled = context.object.data.ragdoll.wiggle_use_springs
                            wiggle_spring_row_right_1.enabled = context.object.data.ragdoll.wiggle_use_springs
                            anim_override_row.enabled = not context.object.data.ragdoll.kinematic
                            wiggle_spring_add_drivers.enabled = not context.object.data.ragdoll.wiggle_drivers
                            wiggle_spring_remove_drivers.enabled = context.object.data.ragdoll.wiggle_drivers
                    
