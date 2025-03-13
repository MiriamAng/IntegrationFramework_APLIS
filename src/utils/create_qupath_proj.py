# -*- coding: utf-8 -*-
"""
The script implements the 3 visualization styles (measurement map, color map, density map)
used to intuitively visualize deep-learning model inference results in QuPath.

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

import json
import numpy as np
import pandas as pd
import os
from pathlib import Path
import shutil

import matplotlib as plt
from openslide import OpenSlide
from shapely.geometry import Polygon
from shapely import Point, MultiPoint

from paquo.images import QuPathImageType
from paquo.projects import QuPathProject
from paquo.colors import QuPathColor
from paquo.classes import QuPathPathClass


def calculate_offset(slidepath: str | Path):
    """
    This function calculates the x and y offsets to subtract to the openslide patch coordinates in order to correctly
    build-up tile detection objects in QuPath

    :param slidepath: full path to the digitized slide (MRXS file in case of a slide scanned with a 3DHistech scanner)
    :return: x and y offsets to subtract to tiles coordinates
    """
    slide = OpenSlide(slidepath)
    if slide.properties.get('openslide.vendor') == 'mirax':
        x_shift = int(slide.properties.get('openslide.bounds-x'))
        y_shift = int(slide.properties.get('openslide.bounds-y'))
    else:
        # If the digitization was not performed with a 3DHistech scanner, then the offset is equal to zero.
        x_shift = y_shift = 0
        
    return x_shift, y_shift


def crate_points(score: float,
                 path_class: QuPathPathClass,
                 x: float,
                 y: float,
                 image: OpenSlide):
    """
    This function creates a number of points in the middle of tile detections, and proportional to the associated
    attention score, in order to be able to use the density map visualization style in QuPath.

    :param score: percentile-ranked attention score
    :param path_class: QuPathPathClass object with the predicted classes and the associated class color in QuPath
    :param x: x coordinate at the center of the tile
    :param y: x coordinate at the center of the tile
    :param image:
    :return: detection objects
    """
    if score >= 0.9:
        
        # Create 9 points
        points = MultiPoint([[x, y], [x, y], 
                             [x, y], [x, y], 
                             [x, y], [x, y],
                             [x, y], [x, y],
                             [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
    
    elif 0.8 <= score < 0.9:
        
        # Create 8 points
        points = MultiPoint([[x, y], [x, y], 
                             [x, y], [x, y], 
                             [x, y], [x, y],
                             [x, y], [x, y]])
        
        image.hierarchy.add_detection(points, path_class)

    elif 0.7 <= score < 0.8:
        
        # Create 7 points
        points = MultiPoint([[x, y], [x, y], 
                             [x, y], [x, y],
                             [x, y], [x, y],
                             [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
        
    elif 0.6 <= score < 0.7:
        
        # Create 6 points
        points = MultiPoint([[x, y], [x, y], 
                             [x, y], [x, y],
                             [x, y], [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
        
    elif 0.5 <= score < 0.6:
        
        # Create 5 points
        points = MultiPoint([[x, y], [x, y],
                             [x, y], [x, y],
                             [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
    
    elif 0.4 <= score < 0.5:
        
        # Create 4 points
        points = MultiPoint([[x, y], [x, y],
                             [x, y], [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
    
    elif 0.3 <= score < 0.4:
    
        # Create 3 points
        points = MultiPoint([[x, y], [x, y],
                             [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
        
    elif 0.2 <= score < 0.3:
        
        # Create 2 points
        points = MultiPoint([[x, y], [x, y]])
        
        image.hierarchy.add_detection(points, path_class)
    
    else:
        
        # Create 1 points
        points = Point(x, y)
        
        image.hierarchy.add_detection(points, path_class)


def create_density_map(vendor: str,
                       slide_id: str,
                       res_dl_dir: str | Path,
                       slides_dir: str | Path,
                       output_dir: str | Path,
                       pred_class: str,
                       pred_score: float):
    """
    This function implements the density map visualization in QuPath
    This visualization is particularly useful to visualize predictions from MIL models

    :param vendor: slide scanner manufacturer, i.e. 3DHistech or other
    :param slide_id: slide identifier
    :param res_dl_dir: full path to the folder where results from the DL model deployment are stored
    :param slides_dir: full path to the slides archive folder
    :param output_dir: full path to the directory storing the QuPath project
    :param pred_class: class predicted by the DL model
    :param pred_score: prediction score associated with the predicted class
    """

    if vendor == "3DHistech":
        slide_no_ext = slide_id
        slide_path = os.path.join(slides_dir, f"{slide_no_ext}.mrxs")
    else:
        slide_no_ext = os.path.splitext(slide_id)[0]
        slide_path = os.path.join(slides_dir, slide_id)

    model_original = os.path.basename(os.path.dirname(output_dir)).replace("-", "_")
    
    # Replace dots in model's name, if any, with underscores to avoid errors when creating the QuPath project
    if "." in model_original:
        model = model_original.replace(".", "_")
    else:
        model = model_original
    
    # Create a QuPath project folder
    qupath_proj_dir = Path(output_dir, f"{slide_no_ext}_QuPathProj-{model}")
    
    if os.path.exists(qupath_proj_dir):
        print(f"QuPath project already exists. Overwriting the existing directory: {qupath_proj_dir}")
        shutil.rmtree(qupath_proj_dir)
        os.makedirs(qupath_proj_dir, exist_ok=True)
    else:
        os.makedirs(qupath_proj_dir, exist_ok=True)
        print("A new QuPath project is being created.")

    project = Path(rf"{qupath_proj_dir}")
    
    # Specify the colors for each class
    color_class = QuPathColor(200, 193, 240)
    
    # Define new classes
    my_classes_and_colors = [
        (f"{pred_class}", color_class)
    ]
    
    # Specify the color to assign to tiles detection
    color_tile = QuPathColor(255,255,255, alpha = 128)
            
    with QuPathProject(project, mode='a') as qp:
        
        new_classes = []
        
        for class_name, class_color in my_classes_and_colors:
            new_classes.append(
                QuPathPathClass(name=class_name, color=class_color)
            )
            
        # Setting QuPathProject.path_class always replaces all classes
        qp.path_classes = new_classes
        
        # Specify the classes
        class_tile = QuPathPathClass("Tiles", color_tile)
        
        path_classes =  new_classes
            
        print(f"Slide being processed: {slide_id}")
        
        filepath = os.path.join(res_dl_dir, "model_coords_attscores.csv")
    
        attention_score_df = pd.read_csv(filepath)
        
        image = Path(f"{slide_path}")

        # Add an image
        entry = qp.add_image(image, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        
        x_offset, y_offset = calculate_offset(slide_path)
        
        height = int(attention_score_df.iloc[1]["height"])
        
        width = int(attention_score_df.iloc[1]["width"])
        
        if "risk" in pred_class:
            description = f"Slide predicted {pred_class} with a risk score of {pred_score}"
        else:
            description = f"Slide predicted {pred_class} with a prediction score of {pred_score}"
        
        entry.description = description
        
        for i in attention_score_df.index.tolist():
            
            x = int(attention_score_df.iloc[i]["minx"] - x_offset)
            
            y = int(attention_score_df.iloc[i]["miny"] - y_offset)
            
            att_score = np.array(attention_score_df.iloc[i]["att_score_pct_rnk"], dtype = float)
            
            crate_points(att_score, path_classes[0], x + width / 2, y + height / 2, entry)
                
            # Create tiles as well
            tile = Polygon.from_bounds(x, y, x+width, y+height)

            entry.hierarchy.add_tile(
                roi=tile,
                path_class = class_tile
                )

        print(f"Density Heatmap for slide {slide_id} completed!")
    
    print(f"\n\n... Renaming project.qpproj file to {slide_id}-{model}.qpproj")
    oldpath = Path(f"{qupath_proj_dir}", "project.qpproj")
    newpath = Path(f"{qupath_proj_dir}", f"{slide_id}-{model}.qpproj")
    oldpath.rename(newpath)


def create_classes(df):
    """
    The function creates the QuPath classes associated with a given multi-class patch-level classification model.
    :param df: data frame storing deep-learning model inference results
    :return: the names of the classes predicted by the deep-learning model and a list of class-color pairs for the QuPath project

    """
    
    classes = [colname.split("_")[1] for colname in df.columns if 'prob' in colname]
    
    # Define a color palette
    col_dec = [plt.colors.to_rgb(col) for col in plt.cm.tab10.colors]

    col_rgb = [tuple([int(255*cc) for cc in c]) for i, c in enumerate(col_dec)]   
    
    my_classes_and_colors = [(cl, eval(f"QuPathColor{col_rgb[j]}")) for j, cl in enumerate(classes)]
    
    return classes, my_classes_and_colors

    
def create_color_map(vendor: str,
                       slide_id: str,
                       res_dl_dir: str | Path,
                       slides_dir: str | Path,
                       output_dir: str | Path):
    """
    This function implements the color map visualization in QuPath

    :param vendor: slide scanner manufacturer, i.e. 3DHistech or other
    :param slide_id: slide identifier
    :param res_dl_dir: full path to the folder where results from the DL model deployment are stored
    :param slides_dir: full path to the slides archive folder
    :param output_dir: full path to the directory storing the QuPath project
    """

    if vendor == "3DHistech":
        slide_no_ext = slide_id
        slide_path = os.path.join(slides_dir, f"{slide_no_ext}.mrxs")
    else:
        slide_no_ext = os.path.splitext(slide_id)[0]
        slide_path = os.path.join(slides_dir, slide_id)

    model_original = os.path.basename(os.path.dirname(output_dir)).replace("-", "_")
    
    # Replace dots in model's name, if any, with underscores to avoid errors when creating the QuPath project
    if "." in model_original:
        model = model_original.replace(".", "_")
    else:
        model = model_original
    
    print(f"{model}")
    
    # Create a QuPath project folder
    qupath_proj_dir = Path(output_dir, f"{slide_no_ext}_QuPathProj-{model}")
    
    if os.path.exists(qupath_proj_dir):
        print(f"QuPath project already exists. Overwriting the existing directory: {qupath_proj_dir}")
        shutil.rmtree(qupath_proj_dir)
        os.makedirs(qupath_proj_dir, exist_ok=True)
    else:
        os.makedirs(qupath_proj_dir, exist_ok=True)
        print("A new QuPath project is being created.")

    project = Path(f"{qupath_proj_dir}")
    
    filepath = os.path.join(res_dl_dir, f"{slide_no_ext}.csv")
    
    pred_df = pd.read_csv(filepath)
    
    x_offset, y_offset = calculate_offset(slide_path)
    
    # Specify the classes to use in the description of a given WSI
    classes, classes_colors = create_classes(pred_df)
    
    minx_offset = [x - x_offset for x in pred_df["minx"]],
    
    pred_df.insert(1, "minx_offset", minx_offset[0])
    
    miny_offset = [y - y_offset for y in pred_df["miny"]],

    pred_df.insert(3, "miny_offset", miny_offset[0])
    
    # Save the updated csv file
    pred_df.to_csv(os.path.join(res_dl_dir, f"{slide_no_ext}_withoffset.csv"))
            
    with QuPathProject(project, mode='a') as qp:
   
        new_classes = []
        
        for class_name, class_color in classes_colors:
            new_classes.append(
                QuPathPathClass(name=class_name, color=class_color)
            )
            
        # Setting QuPathProject.path_class always replaces all classes
        qp.path_classes = new_classes
            
        print(f"Slide being processed: {slide_id}")
        
        image = Path(f"{slide_path}")
        
        # Add an image
        entry = qp.add_image(image, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        
        height = int(pred_df.iloc[1]["height"])
        
        width = int(pred_df.iloc[1]["width"])
        
        prob_columns = [colname for colname in pred_df.columns if 'prob' in colname]
        
        for i in pred_df.index.tolist():
            
            x = int(pred_df.iloc[i]["minx_offset"])
            
            y = int(pred_df.iloc[i]["miny_offset"])
            
            pred_colname = pred_df.iloc[i][prob_columns].idxmax()
            
            measure = pred_df.iloc[i][f"{pred_colname}"]
            
            # Extract the index of the class
            idx_pred = prob_columns.index(pred_colname)
                
            path_class = new_classes[idx_pred]
            
            # Create tiles as well
            tile = Polygon.from_bounds(x, y, x+width, y+height)

            entry.hierarchy.add_tile(
                roi=tile,
                path_class = path_class,
                measurements={
                    f"{classes[idx_pred]}": measure
                    }
                )

        print(f"Color Map for slide {slide_id} completed!")
    
    print(f"\n\n... Renaming project.qpproj file to {slide_id}-{model}.qpproj")
    oldpath = Path(f"{qupath_proj_dir}", "project.qpproj")
    newpath = Path(f"{qupath_proj_dir}", f"{slide_no_ext}-{model}.qpproj")
    oldpath.rename(newpath)



def create_measurement_map(vendor: str,
                       slide_id: str,
                       res_dl_dir: str | Path,
                       slides_dir: str | Path,
                       output_dir: str | Path,
                       class_names: list):
    """
    This function implements the measurement map visualization in QuPath
    :param vendor: slide scanner manufacturer, i.e. 3DHistech or other
    :param slide_id: slide identifier
    :param res_dl_dir: full path to the folder where results from the DL model deployment are stored
    :param slides_dir: full path to the slides archive folder
    :param output_dir: full path to the directory storing the QuPath project
    :param class_names: list containing the names of the classes predicted by the deep-learning model
    """

    if vendor == "3DHistech":
        slide_no_ext = slide_id
        slide_path = os.path.join(slides_dir, f"{slide_no_ext}.mrxs")
    else:
        slide_no_ext = os.path.splitext(slide_id)[0]
        slide_path = os.path.join(slides_dir, slide_id)

    if len(class_names) == 1:
        cl = class_names[0]
        pred_colname = f"prob_{class_names[0]}"
    elif len(class_names) == 2:
        cl = class_names[1]
        pred_colname = f"prob_{class_names[1]}"
    
    model_original = os.path.basename(os.path.dirname(output_dir)).replace("-", "_")
    
    # Replace dots in model's name, if any, with underscores to avoid errors when creating the QuPath project
    if "." in model_original:
        model = model_original.replace(".", "_")
    else:
        model = model_original
    
    # Create a QuPath project folder
    qupath_proj_dir = Path(output_dir, f"{slide_no_ext}_QuPathProj-{model}")
    
    if os.path.exists(qupath_proj_dir):
        print(f"QuPath project already exists. Overwriting the existing directory: {qupath_proj_dir}")
        shutil.rmtree(qupath_proj_dir)
        os.makedirs(qupath_proj_dir, exist_ok=True)
    else:
        os.makedirs(qupath_proj_dir, exist_ok=True)
        print("A new QuPath project is being created.")

    project = Path(rf"{qupath_proj_dir}")
    
    filepath = os.path.join(res_dl_dir, f"{slide_no_ext}.csv")
    
    pred_df = pd.read_csv(filepath)
    
    x_offset, y_offset = calculate_offset(slide_path)
    
    minx_offset = [x - x_offset for x in pred_df["minx"]],
    
    pred_df.insert(1, "minx_offset", minx_offset[0])
    
    miny_offset = [y - y_offset for y in pred_df["miny"]],
    
    pred_df.insert(3, "miny_offset", miny_offset[0])
    
    # Save the updated csv file
    pred_df.to_csv(os.path.join(res_dl_dir, f"{slide_no_ext}_withoffset.csv"))
            
    with QuPathProject(project, mode='a') as qp:
        
        color_tile = QuPathColor(128, 128, 128)
            
        class_tile = QuPathPathClass(name = f"{cl}", color = color_tile)
            
        # Setting QuPathProject.path_class always replaces all classes
        qp.path_class = class_tile
        
        print(f"Slide being processed: {slide_id}")
        
        image = Path(f"{slide_path}")
        
        # add an image
        entry = qp.add_image(image, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        
        height = int(pred_df.iloc[1]["height"])
        
        width = int(pred_df.iloc[1]["width"])
        
        for i in pred_df.index.tolist():
            
            x = int(pred_df.iloc[i]["minx_offset"])
            
            y = int(pred_df.iloc[i]["miny_offset"])
            
            measure = pred_df.iloc[i][f"{pred_colname}"]
            
            # Create tiles as well
            tile = Polygon.from_bounds(x, y, x+width, y+height)

            entry.hierarchy.add_tile(
                roi=tile,
                path_class = class_tile,
                measurements={
                    f"{cl}": measure
                    }
                )

        print(f"Measurement map for slide {slide_id} completed!")
    
    print(f"\n\n... Renaming project.qpproj file to {slide_id}-{model}.qpproj")
    oldpath = Path(f"{qupath_proj_dir}", "project.qpproj")
    newpath = Path(f"{qupath_proj_dir}", f"{slide_id}-{model}.qpproj")
    oldpath.rename(newpath)