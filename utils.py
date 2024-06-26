import mathutils
from mathutils import Vector
import random
import bpy
import math
import os


def set_transparent(objects):
    """
    set parsed objects to be transparent
    """
    
    for obj in objects:
        obj.hide_render = True
        
def set_opaque(objects):
    """
    set parsed objects to be opaque
    """
    
    for obj in objects:
        obj.hide_render = False


def create_circle_around_object(obj, num_points, radius = 0.15):
    """
    returns a list of points around an object arranged in a circle around object center
    """
    
    bbox_corners = [Vector(corner) for corner in obj.bound_box]

    # Calculate the center of the object
    center = sum(bbox_corners, Vector()) / 8

    # Create list of points on a circle around the center in the x, y plane
    circle_points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        circle_points.append(mathutils.Vector((x, y, center.z)))
    
    # Transform points into world coordinates
    world_points = [obj.matrix_world @ p for p in circle_points]
    
    return world_points


def is_visible_ray_cast(obj, num_rays = 15, visibility_threshold = 1, angle_threshold = math.pi/8):
    """
    True if the object is visible from camera within visibility_threshold and lies within angle_threshold, 
    False otherwise
    """

    #check if the object is flat
    normal_vector = obj.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    angle = normal_vector.angle(Vector((0, 0, 1)))
    if angle > angle_threshold and abs(angle - math.pi) > angle_threshold:
        return False
    
    #ray casting to check visibility
    scene = bpy.context.scene
    camera = scene.camera
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    num_hits = 0
    points = create_circle_around_object(obj, num_rays)
    for point in points:
        ray_direction = point - camera.location
        hit, _, _, _, hit_object, _ = scene.ray_cast(depsgraph, camera.location, ray_direction.normalized())
        if hit and hit_object == obj:
            num_hits += 1
    
    if num_hits >= num_rays * visibility_threshold:
        return True
    else:
        return False
    

def find_visible(objects):
    """
    Call is_visible_ray_cast for each object
    """
    
    visible_objects = []
    for obj in objects:
        if is_visible_ray_cast(obj):
            visible_objects.append(obj)
    return visible_objects


def render_scene(objects, visible_objects, box_obj, i, image_path, mask_path):
    """
    Render raw image and mask
    """
    
    image_filename = f"nut_{i:04}"
    mask_filename = f"nut_{i:04}_mask"
    
    # RAW RENDER

    bpy.context.view_layer.use_pass_cryptomatte_object = True
    bpy.context.scene.use_nodes = True
    
    nodes = bpy.context.scene.node_tree.nodes
    
    node_render_layers = nodes.new('CompositorNodeRLayers')
    node_render_layers.location = mathutils.Vector((0.0, 460.0))
    
    node_file_output_render = nodes.new('CompositorNodeOutputFile')
    node_file_output_render.location = mathutils.Vector((600.0, 460.0))
    node_file_output_render.width = 220
    node_file_output_render.base_path = image_path
    node_file_output_render.format.compression = 100
    
    node_file_output_render.inputs['Image'].name = image_filename
    node_file_output_render.file_slots['Image'].path = image_filename
    
    links = bpy.context.scene.node_tree.links
    links.new(node_render_layers.outputs['Image'], node_file_output_render.inputs[image_filename])
    
    bpy.ops.render.render(write_still=True)
    
    rendered_file_path = os.path.join(image_path, f"{image_filename}0150.png")
    
    os.rename(rendered_file_path, os.path.join(image_path, f"{image_filename}.png"))
    
    for node in nodes:
        bpy.context.scene.node_tree.nodes.remove(node)
    
    
    # set up render for mask
    set_transparent([box_obj])  # set the box to be transparent
    set_transparent(objects)     # set objects to be transparent
    set_opaque(visible_objects)  # set visible objects opaque
    light = bpy.data.objects['Light']
    light.hide_render = True
    
    # set up nodes
    
    bpy.context.view_layer.use_pass_cryptomatte_object = True
    bpy.context.scene.use_nodes = True
    
    nodes = bpy.context.scene.node_tree.nodes
    
    node_render_layers = nodes.new('CompositorNodeRLayers')
    node_render_layers.location = mathutils.Vector((0.0, 460.0))
    
    node_file_output_render = nodes.new('CompositorNodeOutputFile')
    node_file_output_render.location = mathutils.Vector((600.0, 460.0))
    node_file_output_render.width = 220
    node_file_output_render.base_path = mask_path
    node_file_output_render.format.compression = 100
    
    node_file_output_render.inputs['Image'].name = mask_filename
    node_file_output_render.file_slots['Image'].path = mask_filename
    
    
    node_cryptomatte = nodes.new('CompositorNodeCryptomatteV2')
    node_cryptomatte.location = mathutils.Vector((300.0, 360.0))
    
    node_file_output_render.format.file_format = 'OPEN_EXR'
    
    names = [obj.name for obj in visible_objects]
    node_cryptomatte.matte_id = ",".join(names)
    
    
    links = bpy.context.scene.node_tree.links
    links.new(node_render_layers.outputs['Image'], node_cryptomatte.inputs['Image'])
    links.new(node_cryptomatte.outputs['Pick'],   node_file_output_render.inputs[mask_filename])
    
        
    bpy.ops.render.render(write_still=True)
    
    rendered_file_path = os.path.join(mask_path, f"{mask_filename}0150.exr")
    
    os.rename(rendered_file_path, os.path.join(mask_path, f"{mask_filename}.exr"))
    
    for node in nodes:
        bpy.context.scene.node_tree.nodes.remove(node)
    
    
    # Return to settings for raw
    set_opaque([box_obj])  # return the box to be opaque
    set_opaque(objects)
    light.hide_render = False

def create_objects(num_parts, part_obj, x_range = (-0.3, 0.3), y_range = (-0.3, 0.3)):
    """
    Create copies of target object
    """
    objects = []
    for j in range(num_parts):

        # Set random position
        x = random.uniform(-0.3, 0.3)
        y = random.uniform(-0.3, 0.3)
        z = 5 + j*1
        
        # Creater objects in scene
        copy_object = part_obj.copy()
        copy_object.data = part_obj.data.copy()
        
        bpy.context.collection.objects.link(copy_object)
        bpy.context.view_layer.objects.active = copy_object
        bpy.ops.rigidbody.object_add()
        
        copy_object.rigid_body.collision_shape = 'MESH'
        copy_object.rigid_body.mass = 1
        copy_object.rigid_body.collision_margin = 0.001
        copy_object.rigid_body.friction = 1.0
        
        copy_object.location = (x,y,z)
        
        objects.append(copy_object)

    return objects
    
def random_light():
    """
    Set random position and power of the light source
    """
    
    light = bpy.data.objects['Light']
    
    x_light = random.uniform(-2,2)
    y_light = random.uniform(-2,2)
    z_light = random.uniform(6,12)
    
    light.location = (x_light,y_light,z_light)
    
    energy_light = random.uniform(500, 3000)
    light.data.energy = energy_light

def random_cam():
    """
    Set random position and rotation of the camera
    Currently rotation is set such, that the camera is poitining at (0,0,0)
    """

    x_cam = random.uniform(-0.1,0.1)
    y_cam = random.uniform(-0.1,0.1)
    z_cam = random.uniform(10,12)
    
    # Define the coordinates of points A and B
    point_A = mathutils.Vector((0, 0, 0))  # Example coordinates of point A
    point_B = mathutils.Vector((x_cam, y_cam, z_cam))  # Example coordinates of point B

    # Calculate the direction vector from point B to point A
    direction_vector = point_B - point_A

    # Create a matrix representing the rotation that aligns the camera's forward direction with the direction vector
    rotation_quaternion = direction_vector.to_track_quat('Z', 'Y')

    # Set the rotation of the camera using the quaternion
    scene = bpy.context.scene
    camera = scene.camera
    camera.rotation_mode = 'QUATERNION'  # Set rotation mode to quaternion
    camera.rotation_quaternion = rotation_quaternion
    camera.location = (x_cam,y_cam,z_cam)
