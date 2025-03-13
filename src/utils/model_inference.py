# -*- coding: utf-8 -*-
""" The script runs deep-learning deployment with one of the three freely available toolboxes:
1) WSInfer (Kaczmarzyk, J. R. et al. Open and reusable deep learning for pathology with WSInfer and QuPath. NPJ Precis. Oncol. 8, 9 (2024))
2) WSInfer-MIL (https://github.com/SBU-BMI/wsinfer-mil; https://zenodo.org/records/12680704)
3) marugoto (https://github.com/KatherLab/marugoto)

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

import os
import pandas as pd
import subprocess

from colorama import init, Fore
from pathlib import Path
from utils import create_qupath_proj

# Automatically reset the style to normal after each print statement
init(autoreset=True)

def run_inference(vendor : str,
                  slide_id : str,
                  spm_4_2 : str,
                  slides_archive : str | Path,
                  wdir : str | Path,
                  paquo_qupath_dir : str):

    """
    This function runs deep-learning model deployment with the WSInfer open-source toolboxe
    :param vendor: slide scanner manufacturer, i.e. 3DHistech or other
    :param slide_id: slide identifier
    :param spm_4_2: name of the deepl-learning model as indicated in the SPM field 4.2 of the input OML^O33 HL7 message
    :param slides_archive: path to the slides archive
    :param wdir: path to the working directory
    :param paquo_qupath_dir: path to the QuPath installation used for paquo
    """

    if vendor == "3DHistech":
        slide_no_ext = slide_id
        # Create the correspondent mrxs file in the slide archive folder.
        # This will then be used to create the QuPath Project
        mrxs_path_archive = Path(rf"{slides_archive}/{slide_id}.mrxs")
        if os.path.isfile(mrxs_path_archive):
            pass
        else:
            open(mrxs_path_archive, "x").close()

    else:
        slide_no_ext = os.path.splitext(slide_id)[0]

    # Define the temporary slide directory where to store each new analyzed slide
    tmp_slidedir = Path(rf"{wdir}/tmp_slides/{slide_no_ext}")

    # Check if tmp_slidedir exists, and if it does not exist create the folder
    if not os.path.exists(tmp_slidedir):
        print(rf"...Creating {tmp_slidedir}")
        os.makedirs(tmp_slidedir)
        src = Path(rf"{slides_archive}/{slide_id}")
        dest = Path(rf"{tmp_slidedir}/{slide_id}")
        move_slide_cmd = f"cp -r {src} {dest}"
        print(f"...Copying slide {slide_id} to {tmp_slidedir}")
        subprocess.call(move_slide_cmd, shell = True)

        # Create an empty mrxs file, if it does not exist, in the temporary slide folder
        mrxs_path = Path(rf"{tmp_slidedir}/{slide_id}.mrxs")
        if os.path.isfile(mrxs_path):
            pass
            print(rf"File {slide_id}.mrxs already exists.")
        else:
            open(mrxs_path, "x").close()
            print(rf"File {slide_id}.mrxs is being created.")

    else:
        # If the folder already exists, it means that the slide has been previously analyzed with other algorithms, and thus also the mrxs file exists
        print(f"Slide {slide_id} already exists...Skipping copy of slide under {tmp_slidedir}")

    custom_modelsdir = Path(rf"{wdir}/custom_DL_models")

    # Read in intput the configuration CSV file containing all the DL models, with information on:
    # 1) the toolbox to use for each model
    # 2) the visualization style
    # 3) the predicted classes

    df = pd.read_csv(Path(rf"{wdir}/encodings_DL.csv"))

    # Extract the row index corresponding to the model to deploy
    idx = df.index[df['SPM_4.2'] == f"{spm_4_2}"].tolist()

    # Extract DL model name
    model_name = df.loc[idx, 'Model_Name'].to_string(index=False)

    # Create the results directory storing results for a given model deployed on a given slide
    tmp_resdir = Path(rf"{wdir}/results_inference/{slide_no_ext}/{model_name}")
    if not os.path.exists(tmp_resdir):
        os.makedirs(tmp_resdir)

    # Extract class labels
    class_names = df.loc[idx, 'Class_Names'].to_string(index=False)
    if "," in class_names:
        # Transform into list and remove white spaces to avoid spaces after comma
        class_names = class_names.replace(" ", "").split(",")
    else:
        class_names = [class_names]

    # Extract the name of the toolbox to use
    toolbox = df.loc[idx, 'Toolbox'].to_string(index=False)

    if toolbox == "wsinfer":
        # Run WSInfer for patch-level classification tasks
        qupathdir = Path(rf"{tmp_resdir}/qupath-proj")

        # Check if the model to run is a customized one or comes with the WSInfer installation
        customized_model = df.loc[idx, 'Customized'].to_string(index=False) #Yes/No

        if os.environ["PAQUO_QUPATH_DIR"] == '':
            pass
            print("Environmental variable \"PAQUO_QUPATH_DIR\" not set, WSInfer can be run!")
        else:
            print(f"Environmental variable \"PAQUO_QUPATH_DIR\" is: {os.environ.get('PAQUO_QUPATH_DIR', 'Not set')}... \n ...Changing to empty value in order to run WSInfer")
            os.environ["PAQUO_QUPATH_DIR"] = ''

        if customized_model == "Yes":
            #  We have to specify the model by providing as additional arguments model's .pt file and JSON file
            model_path = Path(rf"{custom_modelsdir}/{model_name}/model.pt")
            config_path = Path(rf"{custom_modelsdir}/{model_name}/config.json")
            command_wsinfer = f"wsinfer --backend=openslide run --wsi-dir {tmp_slidedir}/ --results-dir {tmp_resdir} --model-path {model_path} --config {config_path}"
        else:
            # We are using a WSInfer built-in model
            command_wsinfer = f"wsinfer --backend=openslide run --wsi-dir {tmp_slidedir}/ --results-dir {tmp_resdir} --model {model_name}"

        print(f"{Fore.BLUE}*" * 100)
        print(f"{Fore.BLUE}Running model inference with WSInfer for slide: {slide_id}")
        subprocess.call(command_wsinfer, shell = True)

        model_resdir = Path(rf"{tmp_resdir}/model-outputs-csv")

        # Since we are dealing with patch-level classification models, we will not have a slide-level predicted label nor a slide-level prediction score, but rather
        # tiles-level metrics.
        pred_label = None
        pred_score = None

        # Once model inference has been run, we have to set os.environ["PAQUO_QUPATH_DIR"] to the path to QuPath installation in order to be able to run paquo
        if os.environ["PAQUO_QUPATH_DIR"] != paquo_qupath_dir:
            print(f"...Setting environmental variable \"PAQUO_QUPATH_DIR\" to {paquo_qupath_dir}")
            os.environ["PAQUO_QUPATH_DIR"] = paquo_qupath_dir
        else:
            pass
            print(f"Environmental variable \"PAQUO_QUPATH_DIR\" correctly set to: {os.environ.get('PAQUO_QUPATH_DIR', 'Not set')}, paquo can be run!")

        # Select the more appropriate visualization heatmap to visualize in QuPath model's inference results
        visualization = df.loc[idx, 'Visualization'].to_string(index=False)
        if visualization == "measurement_map":
            print(f"{Fore.MAGENTA}*" * 100)
            print(f"{Fore.MAGENTA}Creating measurement map for slide: {slide_id}")
            create_qupath_proj.create_measurement_map(vendor, slide_id, model_resdir, slides_archive, qupathdir, class_names)
        elif visualization == 'color_map':
            print(f"{Fore.MAGENTA}*" * 100)
            print(f"{Fore.MAGENTA}Creating color map for slide: {slide_id}")
            create_qupath_proj.create_color_map(vendor, slide_id, model_resdir, slides_archive, qupathdir)
    else:
        print(f"Toolbox {toolbox} not available")
                
    return model_name, pred_label, pred_score


if __name__ == "model_inference":
    
    run_inference()




