import bpy
import random
import time
import csv
import os
import sys
import numpy as np

utils = bpy.data.texts["utils"].as_module()

# -----RENDER SETTINGS-----
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 200
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800


FOLDER_PATH = 'C:\\autorenders_nut_fixed'
image_path = FOLDER_PATH + '\\nut_images'
mask_path =  FOLDER_PATH + '\\nut_masks'


# Define number of renders

START_IT = 0
END_IT   = 5

# Define number of objects

OBJ_NUM_MIN = 0
OBJ_NUM_MAX = 40

OBJ_NAME = 'nut_LOW'


def main():
    box_obj = bpy.data.objects['box']
    part_obj = bpy.data.objects[OBJ_NAME]

    data_filename = FOLDER_PATH + '\\data_nut.csv'
    
    #define fields in the .csv file to be recorded
    fieldnames = ['index', 'total_number', 'number_of_visible']
    
    # Create and drop objects  
    total_time = 0
    
    for i in range(START_IT, END_IT):
        start_it_time = time.time()
        with open(data_filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
        
            # Create an empty list to store the spheres created in this loop

            num_parts = random.randint(OBJ_NUM_MIN, OBJ_NUM_MAX) #=> logs
            objects = utils.create_objects(num_parts, part_obj)
            
            bpy.context.scene.frame_end = 150
            
            # Run the simulation
            bpy.ops.ptcache.bake_all(bake=True)

            # Set the current frame to the last frame of the simulation
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)

            visible_objects = utils.find_visible(objects)
            num_visible = len(visible_objects) #=> logs
            
            utils.random_light()
            utils.random_cam()
            
            utils.render_scene(objects, visible_objects, box_obj, i, image_path, mask_path)

            #append the logs
            writer.writerow({'index': i, 'total_number': num_parts, 'number_of_visible': num_visible})
            
            end_it_time = time.time()
            current_it_time = end_it_time - start_it_time
            total_time += end_it_time - start_it_time
            eta = total_time/(i - START_IT + 1) * (END_IT - START_IT)

            print(f'render number {i - START_IT + 1}/{END_IT - START_IT}\n',
                    f'for number of parts = {num_parts}\n',
                    f'time to render = {current_it_time//3600:02.2f}h:{(current_it_time%3600)//60:02.2f}m:{current_it_time%60:02.2f}s\n',
                    f'time passed    = {total_time//3600:02.2f}h:{(total_time%3600)//60:02.2f}m:{total_time%60:02.2f}s\n',
                    f'eta            = {eta//3600:02.2f}h:{(eta%3600)//60:02.2f}m:{eta%60:02.2f}s')
            
            # Delete objects
            bpy.ops.ptcache.free_bake_all()
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                bpy.data.meshes.remove(obj.data)
    
    print('END RENDERING')
    print(f'for {END_IT - START_IT} render(s) total time = {total_time//3600:02.2f}h:{(total_time%3600)//60:02.2f}m:{total_time%60:02.2f}s')
    
main()