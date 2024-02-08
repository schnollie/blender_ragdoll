import bpy
import math
import mathutils
import ragdoll_aux

#---- Callback Functions ---- 
def armature_poll(self, object):
    return object.type == 'ARMATURE'

def mesh_poll(self, object):
     return object.type == 'MESH'

def empty_poll(self, object):
    return object.type == 'EMPTY'

def meshes_update(self, context):
    control_rig = ragdoll_aux.validate_selection(context.object)
    RagDoll.rigid_bodies_scale(control_rig, 'RIGID_BODIES')
    RagDoll.rigid_bodies_scale(control_rig, 'WIGGLE')

def wiggle_const_update(self, context):
    control_rig = ragdoll_aux.validate_selection(context.object)
    if control_rig.data.ragdoll.type == 'DEFORM':
        control_rig = control_rig.data.ragdoll.control_rig
    if control_rig:
        # limits
        limit_lin = control_rig.data.ragdoll.wiggles.constraints.restrict_linear
        limit_ang = control_rig.data.ragdoll.wiggles.constraints.restrict_angular
        global_max_lin = control_rig.data.ragdoll.wiggles.constraints.distance
        global_max_ang = control_rig.data.ragdoll.wiggles.constraints.rotation
        # settings
        use_wiggle = control_rig.data.ragdoll.wiggles.constraints.wiggle
        use_falloff = control_rig.data.ragdoll.wiggles.constraints.use_falloff
        use_springs = control_rig.data.ragdoll.wiggles.constraints.use_springs
        falloff_mode = control_rig.data.ragdoll.wiggles.constraints.falloff_mode
        falloff_factor = control_rig.data.ragdoll.wiggles.constraints.falloff_factor
        falloff_offset = control_rig.data.ragdoll.wiggles.constraints.falloff_offset
        falloff_invert = control_rig.data.ragdoll.wiggles.constraints.falloff_invert
        bone_level_max = control_rig.data.ragdoll.bone_level_max
        wiggle_falloff_chain_ends = control_rig.data.ragdoll.wiggles.constraints.falloff_chain_ends

        for i in range(len(control_rig.pose.bones)):
            pbone = control_rig.pose.bones[i]
            max_lin = global_max_lin
            max_ang = global_max_ang

            
            if pbone.ragdoll.wiggle_constraint != None:
                wiggle_const = pbone.ragdoll.wiggle_constraint.rigid_body_constraint
                
                if wiggle_const:
                    if not use_wiggle:
                        wiggle_const.enabled = False
                    else:
                        wiggle_const.enabled = True
                        if use_falloff:
                            tree_level = pbone.ragdoll.tree_level
                            bone_name = wiggle_const.object1.parent_bone
                            
                            visible_bones = ragdoll_aux.get_visible_posebones(control_rig)
                            if wiggle_falloff_chain_ends == True:
                                last_in_chain = True
                                for child in control_rig.pose.bones[bone_name].children:
                                    if child in visible_bones:
                                        last_in_chain = False
                                if last_in_chain:
                                    tree_level = bone_level_max 
                    
                            if falloff_invert:
                                # reverse falloff direction / bone chain hierarchy if desired
                                tree_level = control_rig.data.ragdoll.bone_level_max - tree_level
                            
                            # define step size
                            if falloff_mode == 'QUADRATIC':
                                if tree_level == 0:
                                    max_lin = global_max_lin
                                else:
                                    # base quadratic function
                                    max_lin = global_max_lin * falloff_factor * tree_level**2  + falloff_offset
                                    # inverse value
                                    max_lin = 1/max_lin
                                    # scale to stepsize
                                    max_lin = max_lin * global_max_lin
                                    # clamp
                                    max_lin = min(max_lin, global_max_lin)
                            else:
                                # step size is divided by falloff factor to be consistent w/ control of quadratic function
                                max_lin = global_max_lin - ((global_max_lin / bone_level_max / falloff_factor) * tree_level ) + falloff_offset 
                                #clamp
                                max_lin = min(max_lin, global_max_lin)

                        # modify constraints
                        if wiggle_const.type == 'GENERIC_SPRING':
                            wiggle_const.use_limit_ang_x, wiggle_const.use_limit_ang_y, wiggle_const.use_limit_ang_z = limit_ang, limit_ang, limit_ang
                            wiggle_const.use_limit_lin_x, wiggle_const.use_limit_lin_y, wiggle_const.use_limit_lin_z = limit_lin, limit_lin, limit_lin
                            
                            wiggle_const.limit_lin_x_lower, wiggle_const.limit_lin_x_upper = - max_lin, max_lin
                            wiggle_const.limit_lin_y_lower, wiggle_const.limit_lin_y_upper = - max_lin, max_lin
                            wiggle_const.limit_lin_z_lower, wiggle_const.limit_lin_z_upper = - max_lin, max_lin 

                            wiggle_const.limit_ang_x_lower, wiggle_const.limit_ang_x_upper = math.degrees(- max_ang), math.degrees(max_ang)
                            wiggle_const.limit_ang_y_lower, wiggle_const.limit_ang_y_upper = math.degrees(- max_ang), math.degrees(max_ang)
                            wiggle_const.limit_ang_z_lower, wiggle_const.limit_ang_z_upper = math.degrees(- max_ang), math.degrees(max_ang)

                            wiggle_const.use_spring_x = use_springs
                            wiggle_const.use_spring_y = use_springs
                            wiggle_const.use_spring_z = use_springs

                            if use_springs == True:
                                wiggle_const.spring_stiffness_x = control_rig.data.ragdoll.wiggles.constraints.stiffness
                                wiggle_const.spring_stiffness_y = control_rig.data.ragdoll.wiggles.constraints.stiffness
                                wiggle_const.spring_stiffness_z = control_rig.data.ragdoll.wiggles.constraints.stiffness
                                
                                wiggle_const.spring_damping_x = control_rig.data.ragdoll.wiggles.constraints.damping
                                wiggle_const.spring_damping_y = control_rig.data.ragdoll.wiggles.constraints.damping
                                wiggle_const.spring_damping_z = control_rig.data.ragdoll.wiggles.constraints.damping
        print("Info: Wiggle updated")


#---- Property Definition ----
class RdRigidBodyConstraints(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Rigid Body Constraint Collection")
    suffix: bpy.props.StringProperty(name="Rigid Body Constraint Suffix", default=".Constraint")


class RdConnectors(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Connector Collection")
    suffix: bpy.props.StringProperty(name="Ragdoll Ridig Body Suffix", default=".Connect")


class RdRigidBodies(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Rigid Body Geometry Collection")
    suffix: bpy.props.StringProperty(name="Ragdoll Rigid Body Suffix", default=".RigidBody")
    width_min: bpy.props.FloatProperty(name="Minimum Rigid Body Geo Width", default=0.1, min=0.0, update=meshes_update)
    width_max: bpy.props.FloatProperty(name="Minimum Rigid Body Geo Width", default=0.1, min=0.0, update=meshes_update)
    width_relative: bpy.props.FloatProperty(name="Relative Rigid Body Geo Width", default=0.1, min=0.0, update=meshes_update)

    constraints : bpy.props.PointerProperty(type=RdRigidBodyConstraints)
    connectors : bpy.props.PointerProperty(type=RdConnectors)


class RdWiggleConstraints(bpy.types.PropertyGroup):
    wiggle: bpy.props.BoolProperty(name="Use Wiggle", default=False, update=wiggle_const_update)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Wiggle Constraint Collection")
    suffix: bpy.props.StringProperty(name="Ragdoll Wiggle Constraint Suffix", default=".WiggleConstraint")

    distance: bpy.props.FloatProperty(name="Maximum Wiggle Translation",min=0.0, max=16.0, default=0.2, update=wiggle_const_update)
    rotation: bpy.props.FloatProperty(name="Maximum Wiggle Rotation", subtype="ANGLE", min=0.0, max=math.radians(360.0), default=math.radians(22.5), update=wiggle_const_update)
    restrict_linear: bpy.props.BoolProperty(name="Limit Wiggle Translation", default=True, update=wiggle_const_update)
    restrict_angular: bpy.props.BoolProperty(name="Limit Wiggle Rotation", default=False, update=wiggle_const_update)

    use_falloff: bpy.props.BoolProperty(name="Use Wiggle Falloff", default=False, update=wiggle_const_update)
    falloff_invert: bpy.props.BoolProperty(name="Invert Falloff", default=False, update=wiggle_const_update)
    falloff_chain_ends: bpy.props.BoolProperty(name="Chain Ends", default=True, update=wiggle_const_update)
    falloff_mode: bpy.props.EnumProperty(items=[
                                                            ('LINEAR', "Linear", "Linear bone chain based falloff in wiggle"),
                                                            ('QUADRATIC', "Quadratic", "Quadratic bone chain based falloff in wiggle")                          
                                                            ], default='QUADRATIC', name="Falloff Mode", update=wiggle_const_update)
    
    falloff_factor: bpy.props.FloatProperty(name="wiggle_falloff_factor", min=0.0, max=10.0, default=1.0, update=wiggle_const_update)
    falloff_offset: bpy.props.FloatProperty(name="wiggle_falloff_factor", min=-10.0, max=10.0, update=wiggle_const_update)
    drivers: bpy.props.BoolProperty(name="Wiggle has Drivers", default=False)
    use_springs: bpy.props.BoolProperty(name="Use Springs", default=True, update=wiggle_const_update)
    stiffness: bpy.props.FloatProperty(name="Stiffnesss", min=0, max=1000, update=wiggle_const_update)
    damping: bpy.props.FloatProperty(name="Stiffnesss", min=0, max=1000, update=wiggle_const_update)
    drivers: bpy.props.BoolProperty(name="Wiggle has Drivers", default=False)



    def add():
        print("Info: Wiggle Constraints added")

    def update():
        pass

    def remove():
        pass


class RdWiggles(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Wiggle Geometry Collection")
    suffix: bpy.props.StringProperty(name="Ragdoll Wiggle Geometry Suffix", default=".Wiggle")
    constraints : bpy.props.PointerProperty(type=RdWiggleConstraints)


class RdHookConstraints(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Hook Constraint Collection")
    suffix: bpy.props.StringProperty(name="Ragdoll Hook Constraint Suffix", default=".HookConstraint")


class RdHooks(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection, name="Ragdoll Hook Geometry")
    suffix: bpy.props.StringProperty(name="Ragdoll Hook Geometry Suffix", default=".Hook")
    constraints : bpy.props.PointerProperty(type=RdHookConstraints)


class RagDollBone(bpy.types.PropertyGroup):
    is_ragdoll: bpy.props.BoolProperty(name="Part of a Ragdoll", default=False)
    tree_level: bpy.props.IntProperty(name="tree_level", min=0, default =0)
    rigid_body: bpy.props.PointerProperty(type=bpy.types.Object, name="Rigid Body", poll=mesh_poll)
    constraint: bpy.props.PointerProperty(type=bpy.types.Object, name="Rigid Body Constraint", poll=empty_poll)
    connector: bpy.props.PointerProperty(type=bpy.types.Object, name="Rigid Body Connector", poll=empty_poll)
    wiggle: bpy.props.PointerProperty(type=bpy.types.Object, name="Wiggle", poll=mesh_poll)
    wiggle_constraint: bpy.props.PointerProperty(type=bpy.types.Object, name="Wiggle Constraint", poll=empty_poll)
    hook_constraint: bpy.props.PointerProperty(type=bpy.types.Object, name="Hook Constraint", poll=empty_poll)
    hook_mesh: bpy.props.PointerProperty(type=bpy.types.Object, name="Hook Mesh", poll=mesh_poll)
    hook_bone_name : bpy.props.StringProperty(name="Name of Control Bone for associated Hook")

    type: bpy.props.EnumProperty(items=
                                    [
                                        ('DEFAULT', "Ragdoll Bone", "RagDoll Bone of Control or Deform Rig"),
                                        ('HOOK', "Ragdoll Hook Bone in Control Rig", "Deform Rig of a RagDoll")                          
                                    ], default='DEFAULT')


class RagDoll(bpy.types.PropertyGroup):
    #-------- Object Pointers --------
    deform_rig: bpy.props.PointerProperty(type=bpy.types.Object, poll=armature_poll)
    control_rig: bpy.props.PointerProperty(type=bpy.types.Object,poll=armature_poll)
    deform_mesh: bpy.props.PointerProperty(type=bpy.types.Object, name="Target Mesh", poll=mesh_poll)
    deform_mesh_offset: bpy.props.FloatVectorProperty(name="Offset", subtype="XYZ")
    #-------- Control Rig Name Suffix --------
    ctrl_rig_suffix: bpy.props.StringProperty(default=".Control")
    
    #-------- Grouped Simulation Objects and Properties -------- 
    rigid_bodies : bpy.props.PointerProperty(type=RdRigidBodies)
    hooks: bpy.props.PointerProperty(type=RdHooks)
    wiggles: bpy.props.PointerProperty(type=RdWiggles)

    #-------- Armature Sub Type --------
    type: bpy.props.EnumProperty(items=
                                    [   
                                        ('CONTROL', "Control Rig", "Control Rig of a RagDoll"),
                                        ('DEFORM', "Deform Rig", "Deform Rig of a RagDoll")                          
                                    ], 
                                    default='DEFORM')
    
    #-------- JSON Config File --------
    config: bpy.props.PointerProperty(type=bpy.types.Text)

    # -------- State --------
    initialized: bpy.props.BoolProperty(name="RagDoll initialized", default=False)
    
    # -------- Animation/Simulation switches --------
    kinematic: bpy.props.BoolProperty(name="Animated", default=True)
    simulation_influence: bpy.props.FloatProperty(name="Rigid Body_Influence",min=0.0, max=1.0, default=0.0)
   
    # -------- Hierarchy --------
    bone_level_max: bpy.props.IntProperty(name="bone_level_max", min=0, default=0)
 
    def new(armature_object):
        if armature_object.type == 'ARMATURE':
            # get selected bones that are not hidden
            bones = ragdoll_aux.get_visible_posebones(armature_object)
            for b in bones:
                b.ragdoll.is_ragdoll = True
            
            # store bones' hierarchy level in bone prop
            deform_rig = ragdoll_aux.bones_tree_levels_set(armature_object, bones)
            
            # copy deform armature to use as control
            control_rig = RagDoll.secondary_rig_add(deform_rig)
        
            # primary rigid body objects (transform targets for bones)
            control_rig.data.ragdoll.rigid_bodies.collection = RagDoll.rigid_bodies_add(bones, mode='RIGID_BODIES')
            control_rig.data.ragdoll.rigid_bodies.constraints.collection = RagDoll.rigid_body_constraints_add(control_rig, mode='RIGID_BODIES')
            RagDoll.rb_constraint_defaults(control_rig.data.ragdoll.rigid_bodies.constraints.collection, 0, 22.5)
            
            # secondary rigid body objects (wiggles)
            control_rig.data.ragdoll.wiggles.collection = RagDoll.rigid_bodies_add(bones, mode='WIGGLE')
            control_rig.data.ragdoll.wiggles.constraints.collection = RagDoll.rigid_body_constraints_add(control_rig, mode='WIGGLES') # wiggle constraints
            RagDoll.rb_constraint_defaults(control_rig.data.ragdoll.wiggles.constraints.collection, 0.01, 22.5)
            
            # read transformational limits from file, set to primary rigid body constraints
            RagDoll.rb_constraint_limit(control_rig)

            # additional object layer to copy transforms from, as rigid body meshes' pivots have to be centered
            control_rig.data.ragdoll.rigid_bodies.connectors.collection = RagDoll.rb_connectors_add(control_rig)
 
            # add controls to pose bones 
            RagDoll.bone_constraints_add(bones, control_rig)
            RagDoll.bone_drivers_add(deform_rig, control_rig)
            
            # set armatures' state
            control_rig.data.ragdoll.initialized = True
            deform_rig.data.ragdoll.initialized = True

            print("Info: added ragdoll")


    def update(context):
        rig = context.object
        if ragdoll_aux.validate_selection(rig):
            control_rig = rig
            if rig.data.ragdoll.type == 'DEFORM':
                control_rig = rig.data.ragdoll.control_rig
            RagDoll.rb_constraint_limit(control_rig)
            RagDoll.rigid_bodies_scale(control_rig)
            print("Info: ragdoll updated")


    def remove(armature_object):
        if armature_object.type == 'ARMATURE':
            if armature_object.data.ragdoll.type == 'DEFORM':
                deform_rig = armature_object
                control_rig = armature_object.data.ragdoll.control_rig

            else:
                control_rig = armature_object
                deform_rig = armature_object.data.ragdoll.deform_rig
                
            for bone in deform_rig.pose.bones:
                bone.ragdoll.is_ragdoll = False
                for const in bone.constraints:
                    if const.name == "Copy Transforms RD" or const.name == "Copy Transforms CTRL":
                        bone.constraints.remove(const)


            rigid_bodies = control_rig.data.ragdoll.rigid_bodies.collection
            constraints = control_rig.data.ragdoll.rigid_bodies.constraints.collection
            connectors = control_rig.data.ragdoll.rigid_bodies.connectors.collection
            wiggles = control_rig.data.ragdoll.wiggles.collection
            wiggle_constraints = control_rig.data.ragdoll.wiggles.constraints.collection
            hooks = control_rig.data.ragdoll.hooks.collection
            hook_constraints = control_rig.data.ragdoll.hooks.constraints.collection

            if bpy.context.scene.rigidbody_world:
                collection = bpy.context.scene.rigidbody_world.collection
                if rigid_bodies: 
                    ragdoll_aux.object_remove_from_collection(collection, rigid_bodies.objects)
                if wiggles: 
                    ragdoll_aux.object_remove_from_collection(collection, wiggles.objects)
                if hooks: 
                    ragdoll_aux.object_remove_from_collection(collection, hooks.objects)

            if bpy.context.scene.rigidbody_world.constraints:
                collection = bpy.context.scene.rigidbody_world.constraints.collection_objects.data
                rb_obj_list =  bpy.context.scene.rigidbody_world.constraints

                if constraints: 
                    ragdoll_aux.object_remove_from_collection(collection, constraints.objects)
                    ragdoll_aux.object_remove_from_collection(rb_obj_list, constraints.objects)
                if wiggle_constraints:
                    ragdoll_aux.object_remove_from_collection(collection, wiggle_constraints.objects)
                    ragdoll_aux.object_remove_from_collection(rb_obj_list, wiggle_constraints.objects)
                if hook_constraints:
                    ragdoll_aux.object_remove_from_collection(collection, hook_constraints.objects)
                    ragdoll_aux.object_remove_from_collection(rb_obj_list, hook_constraints.objects)


            ragdoll_aux.collection_remove(rigid_bodies)
            ragdoll_aux.collection_remove(constraints)
            ragdoll_aux.collection_remove(connectors)
            ragdoll_aux.collection_remove(wiggles)
            ragdoll_aux.collection_remove(wiggle_constraints)
            ragdoll_aux.collection_remove(hooks)
            ragdoll_aux.collection_remove(hook_constraints)

            armature_data = control_rig.data

            bpy.data.objects.remove(control_rig, do_unlink=True)
            if armature_data.name in bpy.data.armatures:
                bpy.data.armatures.remove(armature_data, do_unlink=True)

            ragdoll_aux.drivers_remove_invalid(deform_rig)
            ragdoll_aux.drivers_remove_related(deform_rig)

            deform_rig.data.ragdoll.initialized = False

            print("Info: removed ragdoll")


    def secondary_rig_add(armature_object):
        if armature_object:
            # copy armature
            secondary_rig = armature_object.copy()
            secondary_rig.name = armature_object.name + armature_object.data.ragdoll.ctrl_rig_suffix
            # copy armature data
            secondary_rig.data = armature_object.data.copy()
            # copy armature custom props
            for key in armature_object.keys():
                secondary_rig[key] = armature_object[key]
            bpy.context.collection.objects.link(secondary_rig)
            
            # adjust viewport display to differentiate Armatures
            if armature_object.data.display_type == 'OCTAHEDRAL':
                secondary_rig.data.display_type = 'STICK'
            else:
                secondary_rig.data.display_type = 'OCTAHEDRAL'

            deform = None
            ctrl = None

            if armature_object.data.ragdoll.type == 'DEFORM':
                secondary_rig.data.ragdoll.type = 'CONTROL'
                deform = armature_object
                ctrl = secondary_rig
            
            elif armature_object.data.ragdoll.type == 'CONTROL':
                secondary_rig.data.ragdoll.type = 'DEFORM'
                deform = secondary_rig
                ctrl = armature_object

            ctrl.data["rd_influence"] = 1.0
            ctrl.data.id_properties_ensure()  # Make sure the manager is updated
            property_manager = ctrl.data.id_properties_ui("rd_influence")
            property_manager.update(min=0, max=1)

            ctrl.data.ragdoll.deform_rig = deform
            ctrl.data.ragdoll.initialized = True
            
            deform.data.ragdoll.control_rig = ctrl
            deform.data.ragdoll.initialized = True

            ragdoll_aux.deselect_all()
            ctrl.select_set(True)
            bpy.context.view_layer.objects.active = ctrl
            
            print("Info: ctrl rig added")
            return ctrl

        else:
            print("Error: No active armature.")
            return None


    def rigid_bodies_add(pbones, mode='RIGID_BODIES'):
        if isinstance(type(pbones), bpy.types.PoseBone.__class__):
            pbones = [pbones]
        rb_bones = []
        
        # set current frame to beginning of frame range # TODO: get frame range for this!
        bpy.context.scene.frame_current = 1
        
        selected_rig = ragdoll_aux.validate_selection(bpy.context.object, 'ARMATURE')
        control_rig = None
        deform_rig = None

        if selected_rig:
            if selected_rig.data.ragdoll.type == 'DEFORM':
                control_rig = selected_rig.data.ragdoll.control_rig
                deform_rig = selected_rig
            elif selected_rig.data.ragdoll.type == 'CONTROL':
                control_rig = selected_rig
                deform_rig = selected_rig.data.ragdoll.deform_rig
        
        # select name and collection
        if mode == 'RIGID_BODIES':
            suffix = deform_rig.data.ragdoll.rigid_bodies.suffix
        
        elif mode == 'WIGGLE':
            suffix = deform_rig.data.ragdoll.wiggles.suffix

        elif mode == 'HOOK':
            suffix = deform_rig.data.ragdoll.hooks.suffix

        if control_rig:
            for pb in pbones:
                geo_name = deform_rig.name + "." + pb.name + suffix
                # add and scale box geometry per bone
                new_cube = ragdoll_aux.cube(1, geo_name)
                new_cube.display_type = 'WIRE'

                for vert in new_cube.data.vertices:
                    vert.co[0] *= 1 / new_cube.dimensions[1] * pb.length * deform_rig.data.ragdoll.rigid_bodies.width_relative
                    vert.co[1] *= 1 / new_cube.dimensions[1] * pb.length
                    vert.co[2] *= 1 / new_cube.dimensions[1] * pb.length * deform_rig.data.ragdoll.rigid_bodies.width_relative

                # parent cube to control rig bone
                new_cube.matrix_local = pb.matrix
                new_cube.parent = control_rig
                new_cube.parent_type = 'BONE'
                new_cube.parent_bone = pb.name

                # apply bone's transform to cube
                vector = (pb.head - pb.tail) / 2
                translate = mathutils.Matrix.Translation(vector)
                new_cube.matrix_parent_inverse = pb.matrix.inverted() @ translate
            
                # add cube to rigid body collection & set collision shape 
                bpy.context.scene.rigidbody_world.collection.objects.link(new_cube)
                new_cube.rigid_body.collision_shape = 'BOX'
                new_cube.rigid_body.kinematic = True

                # add driver to switch animation/simulation
                if mode == 'RIGID_BODIES':
                    # set bone property
                    pb.ragdoll.rigid_body = new_cube
                    if control_rig.pose.bones.get(pb.name):
                        control_rig.pose.bones[pb.name].ragdoll.rigid_body = new_cube
                        
                    # add driver
                    driven_value = new_cube.rigid_body.driver_add("kinematic")
                    driven_value.driver.type = 'SCRIPTED'
                    driven_value.driver.expression = "kinematic"
                    driver_var = driven_value.driver.variables.new()
                    driver_var.name = "kinematic"
                    driver_var.type = 'SINGLE_PROP'
                    target = driver_var.targets[0]
                    target.id_type = 'ARMATURE'
                    target.id = control_rig.data
                    target.data_path = 'ragdoll.kinematic'

                elif mode == 'WIGGLE':
                    # TODO: set this elsewhere
                    new_cube.rigid_body.collision_collections[0] = False
                    new_cube.rigid_body.collision_collections[1] = True
                    # set bone property
                    pb.ragdoll.wiggle = new_cube
                    if control_rig.pose.bones.get(pb.name):
                        control_rig.pose.bones[pb.name].ragdoll.wiggle = new_cube

                elif mode == 'HOOK':
                    pb.ragdoll.rigid_body = new_cube

                rb_bones.append(new_cube)
    
        
        # add cubes to collection
        collection_name = deform_rig.name + suffix
        collection = ragdoll_aux.object_add_to_collection(collection_name, [rb_geo for rb_geo in rb_bones])
        ragdoll_aux.object_remove_from_collection(bpy.context.scene.collection, [rb_geo for rb_geo in rb_bones])
        RagDoll.rigid_bodies_scale(control_rig, 'RIGID_BODIES')
        
        return collection


    def rigid_bodies_scale(control_rig, mode='RIGID_BODIES'):
        width_relative = control_rig.data.ragdoll.rigid_bodies.width_relative
        width_min = control_rig.data.ragdoll.rigid_bodies.width_min
        width_max = control_rig.data.ragdoll.rigid_bodies.width_max

        if width_min + width_max + width_relative > 0:
            for bone in control_rig.pose.bones:
                mesh = None
                if mode == 'RIGID_BODIES':
                    if bone.ragdoll.rigid_body:
                        mesh = bone.ragdoll.rigid_body
                elif mode == 'WIGGLES':
                    if bone.ragdoll.wiggle:
                        mesh = bone.ragdoll.wiggle
                if mesh:
                    for vert in mesh.data.vertices:
                        for i in range(3):
                            # reset cube to dimensions = [1,1,1] 
                            vert.co[i] *= abs(0.5 / vert.co[i])
                            if i == 1:
                                vert.co[i] *= bone.length
                            else:
                                # clamp values to min/max
                                width_factor = width_relative * bone.length

                                if width_max != 0:
                                    width_factor = min(width_max, width_relative)
                                
                                if width_min != 0:
                                    width_factor = max(width_factor, width_min)
            
                                # apply new transform
                                vert.co[i] *= width_factor

                    mesh.data.update()
                    bpy.context.view_layer.update()

        else:
            print("Error: Cannot create mesh with width of 0")


    def wiggle_spring_drivers_add(control_rig):
        for obj in control_rig.data.ragdoll.wiggles.constraints.collection.objects:
            if obj.rigid_body_constraint and obj.rigid_body_constraint.type == 'GENERIC_SPRING':
                obj.rigid_body_constraint.use_spring_x = True
                obj.rigid_body_constraint.use_spring_y = True
                obj.rigid_body_constraint.use_spring_z = True

                properties = {
                    "stiffness": [
                        "spring_stiffness_x",
                        "spring_stiffness_y",
                        "spring_stiffness_z",
                        ],
                    "damping": [
                        "spring_damping_x",
                        "spring_damping_y",
                        "spring_damping_z",
                    ]
    
                }
    
                for key, value in properties.items():
                    for prop in value:
                        fcurve = obj.rigid_body_constraint.driver_add(prop)
                        var = fcurve.driver.variables.new()
                        var.name = key
                        var.type = 'SINGLE_PROP'
                        target = var.targets[0]
                        target.id_type = 'ARMATURE'
                        target.id = control_rig.data
                        target.data_path = 'ragdoll.wiggle_%s'%key
                        fcurve.driver.expression = key

            else:
                print("Error: Wrong Rigid Body Constraint Type: %s"%obj.rigid_body_constraint.type)
        

    def wiggle_spring_drivers_remove(control_rig):
        wiggle_constraints = control_rig.data.ragdoll.wiggles.constraints.collection
        for obj in wiggle_constraints.objects:
            for d in obj.animation_data.drivers:
                obj.animation_data.drivers.remove(d)


    def rb_const_add(object_0, object_1, parent_bone, suffix, size=0.1, constraint_type='GENERIC_SPRING'):
        name = parent_bone.id_data.name + "." + parent_bone.name + suffix
        empty = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(empty)
        empty.empty_display_size = size
        
        bpy.context.scene.rigidbody_world.constraints.objects.link(empty)
        empty.rigid_body_constraint.type = constraint_type
        
        vec = (parent_bone.head - parent_bone.tail)
        trans = mathutils.Matrix.Translation(vec)
        empty.matrix_local = parent_bone.matrix
        
        empty.parent = parent_bone.id_data
        empty.parent_type = 'BONE'
        empty.parent_bone = parent_bone.name
        empty.matrix_parent_inverse = parent_bone.matrix.inverted() @ trans
        
        if object_0:
            empty.rigid_body_constraint.object1 = object_0
        if object_1:
            empty.rigid_body_constraint.object2 = object_1

        return empty
        

    def rigid_body_constraints_add(control_rig, hook_bones=None, mode='RIGID_BODIES'):
        bones = ragdoll_aux.get_visible_posebones(control_rig)
        empty = None
        collection = None

        if mode == 'RIGID_BODIES':
            suffix = control_rig.data.ragdoll.rigid_bodies.constraints.suffix
            collection_name = control_rig.data.ragdoll.deform_rig.name + suffix
            for bone in bones:
                for child in bone.children:
                    obj_0 = bone.ragdoll.rigid_body
                    obj_1 = child.ragdoll.rigid_body
                    empty = RagDoll.rb_const_add(obj_0, obj_1, child, suffix, 0.1)
                    bone.ragdoll.constraint = empty
                    collection = ragdoll_aux.object_add_to_collection(collection_name, empty)
                    ragdoll_aux.object_remove_from_collection(bpy.context.scene.collection, empty)

        elif mode == 'WIGGLES':
            suffix = control_rig.data.ragdoll.wiggles.constraints.suffix
            collection_name = control_rig.data.ragdoll.deform_rig.name + suffix
            for bone in bones:
                obj_0 = bone.ragdoll.rigid_body
                obj_1 = bone.ragdoll.wiggle
                empty = RagDoll.rb_const_add(obj_0, obj_1, bone, suffix)
                empty.rigid_body_constraint.enabled = control_rig.data.ragdoll.wiggles.constraints.wiggle
                bone.ragdoll.wiggle_constraint = empty
                collection = ragdoll_aux.object_add_to_collection(collection_name, empty)
                ragdoll_aux.object_remove_from_collection(bpy.context.scene.collection, empty)

        elif mode == 'HOOK':
            suffix = control_rig.data.ragdoll.hooks.constraints.suffix
            collection_name = control_rig.data.ragdoll.deform_rig.name + suffix
            if hook_bones:
                bone_mesh = hook_bones[0].ragdoll.rigid_body
                hook_mesh = hook_bones[1].ragdoll.rigid_body
                empty = RagDoll.rb_const_add(bone_mesh, hook_mesh, hook_bones[1], suffix)
                hook_bones[0].ragdoll.hook_constraint = empty
                hook_bones[0].ragdoll.hook_mesh = hook_mesh
                hook_bones[0].ragdoll.hook_bone_name = hook_bones[1].name

                collection = ragdoll_aux.object_add_to_collection(collection_name, empty)
                ragdoll_aux.object_remove_from_collection(bpy.context.scene.collection, empty)
        
        return collection


    def rb_constraint_defaults(constraints, max_lin, max_ang):
        if constraints:
            for obj in constraints.objects:
                rb_const = obj.rigid_body_constraint
                if rb_const:
                    if rb_const.type == 'GENERIC' or rb_const.type == 'GENERIC_SPRING':
                        rb_const.use_limit_lin_x = True
                        rb_const.use_limit_lin_y = True
                        rb_const.use_limit_lin_z = True
                        
                        rb_const.use_limit_ang_x = True
                        rb_const.use_limit_ang_y = True
                        rb_const.use_limit_ang_z = True
                        # default limits
                        rb_const.limit_lin_x_lower = -max_lin
                        rb_const.limit_lin_x_upper = max_lin
                        rb_const.limit_lin_y_lower = -max_lin
                        rb_const.limit_lin_y_upper = max_lin
                        rb_const.limit_lin_z_lower = -max_lin
                        rb_const.limit_lin_z_upper = max_lin
                        
                        rb_const.limit_ang_x_lower = math.radians(-max_ang)
                        rb_const.limit_ang_x_upper = math.radians(max_ang)
                        rb_const.limit_ang_y_lower = math.radians(-max_ang)
                        rb_const.limit_ang_y_upper = math.radians(max_ang)
                        rb_const.limit_ang_z_lower = math.radians(-max_ang)
                        rb_const.limit_ang_z_upper = math.radians(max_ang) 


    def rb_constraint_limit(control_rig):
        config = control_rig.data.ragdoll.config
        if config:
            config_data = ragdoll_aux.config_load(config)

            if config_data != None:
                collection = control_rig.data.ragdoll.rigid_bodies.constraints.collection
                for obj in collection.objects:
                    if obj.rigid_body_constraint:
                        constraint = obj.rigid_body_constraint
                        stripped_name = obj.name.rstrip(control_rig.data.ragdoll.rigid_bodies.constraints.suffix)
                        stripped_name = stripped_name.lstrip(control_rig.data.ragdoll.deform_rig.name).strip(".")
                        
                        if "strip" in config_data:
                            for i in range(len(config_data["strip"])):
                                stripped_name = stripped_name.replace(config_data["strip"][i],"")

                        bone_data = config_data.get("bones").get(stripped_name)
                        
                        if bone_data:
                            limit_lin_x_lower = bone_data.get("limit_lin_x_lower")
                            limit_lin_x_upper = bone_data.get("limit_lin_x_upper")
                            limit_lin_y_lower = bone_data.get("limit_lin_y_lower")
                            limit_lin_y_upper = bone_data.get("limit_lin_y_upper")
                            limit_lin_z_lower = bone_data.get("limit_lin_z_lower")
                            limit_lin_z_upper = bone_data.get("limit_lin_z_upper")

                            limit_ang_x_lower = bone_data.get("limit_ang_x_lower")
                            limit_ang_x_upper = bone_data.get("limit_ang_x_upper")
                            limit_ang_y_lower = bone_data.get("limit_ang_y_lower")
                            limit_ang_y_upper = bone_data.get("limit_ang_y_upper")
                            limit_ang_z_lower = bone_data.get("limit_ang_z_lower")
                            limit_ang_z_upper = bone_data.get("limit_ang_z_upper")

                            constraint.limit_lin_x_lower = limit_lin_x_lower if limit_lin_x_lower else constraint.limit_lin_x_lower  
                            constraint.limit_lin_x_upper = limit_lin_x_upper if limit_lin_x_upper else constraint.limit_lin_x_upper 
                            constraint.limit_lin_y_lower = limit_lin_y_lower if limit_lin_y_lower else constraint.limit_lin_y_lower 
                            constraint.limit_lin_y_upper = limit_lin_y_upper if limit_lin_y_upper else constraint.limit_lin_y_upper 
                            constraint.limit_lin_z_lower = limit_lin_z_lower if limit_lin_z_lower else constraint.limit_lin_z_lower 
                            constraint.limit_lin_z_upper = limit_lin_z_upper if limit_lin_z_upper else constraint.limit_lin_z_upper 

                            constraint.limit_ang_x_lower = math.radians(limit_ang_x_lower) if limit_ang_x_lower else constraint.limit_ang_x_lower 
                            constraint.limit_ang_x_upper = math.radians(limit_ang_x_upper) if limit_ang_x_upper else constraint.limit_ang_x_upper 
                            constraint.limit_ang_y_lower = math.radians(limit_ang_y_lower) if limit_ang_y_lower else constraint.limit_ang_y_lower 
                            constraint.limit_ang_y_upper = math.radians(limit_ang_y_upper) if limit_ang_y_upper else constraint.limit_ang_y_upper 
                            constraint.limit_ang_z_lower = math.radians(limit_ang_z_lower) if limit_ang_z_lower else constraint.limit_ang_z_lower 
                            constraint.limit_ang_z_upper = math.radians(limit_ang_z_upper) if limit_ang_z_upper else constraint.limit_ang_z_upper 

        else:
            RagDoll.rb_constraint_defaults(control_rig.data.ragdoll.rigid_bodies.constraints.collection, 0, 22.5)


    def rb_connectors_add(control_rig):
        # set current frame to 0
        bpy.context.scene.frame_current = 1
        empties = []
        bones = ragdoll_aux.get_visible_posebones(control_rig)
        deform_rig = control_rig.data.ragdoll.deform_rig

        for bone in bones:
            geo_name = deform_rig.name + "." + bone.name + control_rig.data.ragdoll.rigid_bodies.suffix
            geo = bpy.data.objects.get(geo_name)

            if geo:
                # add empty
                empty_name = ""
                empty_name = deform_rig.name + "." + bone.name + control_rig.data.ragdoll.rigid_bodies.connectors.suffix
                empty = bpy.data.objects.new(empty_name, None)
                bpy.context.collection.objects.link(empty)
                
                # set & store position
                empty.matrix_world = deform_rig.matrix_world @ bone.matrix
                obj_matrix = empty.matrix_world.copy()
                
                # set parent
                empty.parent_type = 'OBJECT'
                empty.parent = geo
                
                # remove parent inverse transform
                empty.matrix_world.identity()
                bpy.context.view_layer.update()
                empty.matrix_world = obj_matrix 

                # modifiy visualization
                empty.empty_display_type = 'SPHERE'
                empty.empty_display_size = 0.05

                empties.append(empty)

        # add empties to collection
        collection_name = deform_rig.name + control_rig.data.ragdoll.rigid_bodies.connectors.suffix
        collection = ragdoll_aux.object_add_to_collection(collection_name, empties)
        ragdoll_aux.object_remove_from_collection(bpy.context.scene.collection, empties)
        print("Info: rd connectors added")
        return collection


    def bone_constraints_add(bones, control_rig):
        # control_rig = ragdoll_aux.validate_selection(bpy.context.object, 'ARMATURE')
        
        for bone in bones:
            deform_rig_name = bone.id_data.name
            connector_name = deform_rig_name + "." + bone.name + control_rig.data.ragdoll.rigid_bodies.connectors.suffix
            connector = bpy.data.objects.get(connector_name)
            if connector:
                # add copy transform constraint for simulation
                copy_transforms_rd = bone.constraints.new('COPY_TRANSFORMS')
                copy_transforms_rd.name = "Copy Transforms RD"
                copy_transforms_rd.target = connector
            
                # add copy transform constraint for animation
                copy_transforms_ctrl = bone.constraints.new('COPY_TRANSFORMS')
                copy_transforms_ctrl.name = "Copy Transforms CTRL"
                copy_transforms_ctrl.target = control_rig
                copy_transforms_ctrl.subtarget = bone.name
            
        print("Info: bone constraints set")


    def bone_drivers_add(deform_rig, control_rig):
        for bone in deform_rig.pose.bones:
            # add driver to copy ragdoll transform constraint
            for const in bone.constraints:
                # TODO: not use constraints' names. custom props and pointers seem to be off stable API for constraints? 
                if 'RD' in const.name or 'CTRL' in const.name:
                    rd_influence = const.driver_add("influence")
                    rd_influence.driver.type = 'SCRIPTED'
                    var = rd_influence.driver.variables.new()
                    var.name = "simulation_influence"
                    var.type = 'SINGLE_PROP'
                    target = var.targets[0]
                    target.id_type = 'ARMATURE'
                    target.id = control_rig.data
                    target.data_path = 'ragdoll.simulation_influence'
                    rd_influence.driver.expression = "1-simulation_influence"

                    if 'CTRL' in const.name:
                        rd_influence.driver.expression = "simulation_influence"

        print("Info: bone constraint drivers set")


    def hook_bone_add(context, length):
        if bpy.context.mode == 'EDIT_ARMATURE':
            bone_name = "RagDollHook.000" # TODO: name elsewhere
            edit_bone = context.object.data.edit_bones.new(name=bone_name)
            cursor_loc = bpy.context.scene.cursor.location
            head = cursor_loc @ context.object.matrix_world
            tail = head + mathutils.Vector([0,0,length])
            setattr(edit_bone, 'use_deform', False)
            setattr(edit_bone, 'head', head)
            setattr(edit_bone, 'tail', tail)

            return edit_bone


    def hook_set(context, pose_bone, hook_pose_bone):
        pose_bone.ragdoll.type = 'HOOK'
        context.object.data.ragdoll.hooks.collection = RagDoll.rigid_bodies_add(hook_pose_bone, mode='HOOK')
        context.object.data.ragdoll.hooks.constraints.collection = RagDoll.rigid_body_constraints_add(context.object, [pose_bone, hook_pose_bone], 'HOOK')
        RagDoll.rb_constraint_defaults(context.object.data.ragdoll.hooks.constraints.collection, 0, 22.5)

        return pose_bone
    

    def hook_objects_remove(context, bone_name):
        hook_constraint = context.object.pose.bones[bone_name].ragdoll.hook_constraint
        hook_mesh = context.object.pose.bones[bone_name].ragdoll.hook_mesh
        hook_bone_name = context.object.pose.bones[bone_name].ragdoll.hook_bone_name

        ragdoll_aux.object_remove_from_collection(bpy.context.scene.rigidbody_world.collection, hook_mesh)
        ragdoll_aux.object_remove_from_collection(bpy.context.scene.rigidbody_world.constraints, hook_constraint)
        bpy.data.objects.remove(hook_constraint, do_unlink=True)
        bpy.data.objects.remove(hook_mesh, do_unlink=True)

        if bone_name in context.object.pose.bones:
            context.object.pose.bones[bone_name].ragdoll.type = 'DEFAULT'
     
        return hook_bone_name
    

    def hook_bone_remove(context, edit_bone_name):
        edit_bone = context.object.data.edit_bones[edit_bone_name]
        context.object.data.edit_bones.remove(edit_bone)