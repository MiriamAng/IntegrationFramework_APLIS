# -*- coding: utf-8 -*-
"""
The script implements the generation of the output OUL^R21 HL7 message that the AI-DSS sends to the AP-LIS

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

import base64
from io import BytesIO
import os
import pandas as pd
from pathlib import Path
from random import randint
from openslide import OpenSlide

from hl7apy.core import Message
from hl7apy.consts import VALIDATION_LEVEL
from hl7apy.parser import Group


def generate_msg_ctrl_id(ndigits: int) -> str:
    """
    This function creates a random message control ID made up of a number of digits equal to ndigits.
    Note: the maximum length for this field should be 199.

    :param ndigits: number of digits that make up the message control ID
    :return: a random message control ID
    """

    list_digits = [str(randint(0, 9)) for _ in range(ndigits)]

    msg_ctrl_id = str("".join(list_digits))

    return msg_ctrl_id



def encode_file_base64(file_path: str | Path) -> str:
    """
    This function takes in input the path to a file (e.g., CSV, PNG, JSON) and returns in output the file encoded in standard Base64 alphabet.
    Encoded files will be sent to the AP-LIS through the OBX segments of the output OUL^R21 HL7 message.
    """
    with open(file_path, "rb") as file_path:
        file_bytes = base64.standard_b64encode(file_path.read())
    file_bytes = BytesIO(file_bytes)
    encoded_file = file_bytes.getvalue().decode('utf-8')
    
    return encoded_file


def top_five_tiles(slidedir : str | Path,
                   csv_model_output : str | Path, 
                   model_name : str, 
                   wdir : str | Path):
    """
    This function extract the top 5 tiles supporting a chosen class

    """
    
    # Define the maximum number of tiles that we want to provide in output as OBX segments
    ntop = 5
    
    slide = OpenSlide(slidedir)
    
    # Create an empty list that will store the images of the top important tiles
    obs_values_add =  []
    
    # Read in the csv file containing model's results
    df_model_res = pd.read_csv(csv_model_output)
    
    # Read in intput the configuration file containing all the models
    info_models = pd.read_csv(Path(rf"{wdir}/encodings_DL.csv"))
    
    # Extract the index corresponding to the model in question
    idx = info_models.index[info_models['Model_Name'] == f"{model_name}"].tolist()
    
    # Check if for the selected model it is planned to export the top 5 files as OBX segment
    export_top_tiles = info_models.loc[idx, 'Export_Top_Tiles'].to_string(index=False)
    
    if export_top_tiles == "No":
        obs_id_add = []
        value_type_add = []
        obs_values_add = []
    else:
        class_names = info_models.loc[idx, 'Class_Names'].to_string(index=False)
        if "," in class_names:
            # Remove also white spaces to avoid spaces after comma
            class_names = class_names.replace(" ", "").split(",")
        else:
            class_names = [class_names]
            
        if len(class_names) == 1:
            pred_colname = f"prob_{class_names[0]}"
        elif len(class_names) == 2:
            pred_colname = f"prob_{class_names[1]}"
            
        # Sort the dataframe basing on the values stored in pred_colname
        df_model_res_sorted = df_model_res.sort_values(by=[f'{pred_colname}'], ascending=False)
        
        ntop_prob = [prob for i, prob in enumerate(df_model_res_sorted[f'{pred_colname}'][0:ntop]) if prob > 0.5]
        
        # Now the dataframe df_model_res_sorted has been sorted, I can take generate the tiles for the first (len(ntop_prob)) tiles
        for i, _ in enumerate(ntop_prob):
            minx = df_model_res_sorted.loc[i, 'minx']
            miny = df_model_res_sorted.loc[i, 'miny']
            width = df_model_res_sorted.loc[i, 'width']
            height = df_model_res_sorted.loc[i, 'height']
            patch_im = slide.read_region(location=(minx, miny), level=0, size=(width, height))
            patch_im = patch_im.convert("RGB")
            
            # Convert the region to a format suitable for encoding (e.g., JPG)
            buffered = BytesIO()
            patch_im.save(buffered, format="JPEG")
            
            # Encode the image to base64
            patch_base64 = base64.standard_b64encode(buffered.getvalue()).decode('utf-8')
            
            # Print or use the base64 encoded image string
            obs_values_add.append(patch_base64)
            
        # Now creates the lists necessary to populate the additional obx segments
        obs_id_add = [f"TILE_{idx+1}" for idx, _ in enumerate(obs_values_add)]
        value_type_add = ["ED" for _, _ in enumerate(obs_values_add)]
            
    return obs_id_add, value_type_add, obs_values_add


def create_msh(msg_input_dict, msg_output):
    """
    This function creates the message header (MSH segment) of the output OUL^R21 HL7 message

    """
    msg_output.msh.msh_3 = msg_input_dict["MSH"]["MSH_5"]
    msg_output.msh.msh_4 = msg_input_dict["MSH"]["MSH_6"]
    msg_output.msh.msh_5 = msg_input_dict["MSH"]["MSH_3"]
    msg_output.msh.msh_6 = msg_input_dict["MSH"]["MSH_4"]
    msg_output.msh.msh_9 = "OUL^R21"
    # Generate the message control ID
    msg_output.msh.msh_10 = msgControlId(16)
    msg_output.msh.msh_11 = "P"
    msg_output.msh.msh_12 = "2.6"
    
    # Validation
    try:
        msg_output.msh.validate()
        #print("MSH Validated")
    except Exception as e:
        print(e)
        
    return msg_output


def create_pid(msg_input, msg_output):
    """
    This function creates the patient segment (PID) of the output OUL^R21 HL7 message

    """
    # All the information related to the patient needs to be provided to the OUL_R21_PATIENT group
    msg_output.add_group("OUL_R21_PATIENT")
    msg_output.OUL_R21_PATIENT.add_segment('PID')
    msg_output.OUL_R21_PATIENT.pid = msg_input.pid.value # This information will be directly retrieved from the input OML^O33 message
    
    # Validation
    try:
        msg_output.OUL_R21_PATIENT.pid.validate()
        print("PID Validated")
    except Exception as e:
        print(e)
    
    return msg_output

#------------------------------------------------------------------------------------------------------------------#
#                                  CREATE THE ORDER GROUP (ORC, OBR, OBX)                                          #
#------------------------------------------------------------------------------------------------------------------#
def create_order_group(msg_input_dict, msg_input_dict2, msg_output, obs_ids, value_type, obs_values, obs_id_add, value_type_add, obs_values_add, idx_key = ""):
    order_group = Group("OUL_R21_ORDER_OBSERVATION", validation_level=VALIDATION_LEVEL.TOLERANT)
    
    # Add ORC segment
    order_group.add_segment('ORC')
    key_orc = "ORC" + f"{idx_key}"
    order_group.orc = msg_input_dict2[key_orc]
    
    # Add OBR segment
    order_group.add_segment('OBR')
    key_obr = "OBR" + f"{idx_key}"
    order_group.obr = msg_input_dict2[key_obr]
    
    # Add multiple OBX segments
    for idx, obs_id in enumerate(obs_ids):
        obs_group = Group("OUL_R21_OBSERVATION", validation_level=VALIDATION_LEVEL.TOLERANT)
        obs_group.add_segment('OBX')
        obs_group.obx.obx_1 = str(idx+1)
        obs_group.obx.obx_2 = value_type[idx]
        slidebarcode = msg_input_dict["OBR"]["OBR_2"]
        obs_id_field = f"{slidebarcode}^{obs_id}"
        obs_group.obx.obx_3 = obs_id_field
        if os.path.exists(obs_values[idx]):
            file_base64 = str(encodeFile_base64(obs_values[idx]))
            obs_group.obx.obx_5 = file_base64
        else:
            obs_group.obx.obx_5 = obs_values[idx]
        obs_group.obx.obx_11 = 'F'
        order_group.add(obs_group)  
    msg_output.add(order_group)
    
    if len(obs_values_add) != 0:
        for idx_add, obs_id in enumerate(obs_id_add):
            obs_group = Group("OUL_R21_OBSERVATION", validation_level=VALIDATION_LEVEL.TOLERANT)
            obs_group.add_segment('OBX')
            obs_group.obx.obx_1 = str(idx+1+idx_add+1)
            obs_group.obx.obx_2 = value_type_add[idx_add]
            slidebarcode = msg_input_dict["OBR"]["OBR_2"]
            obs_id_field = f"{slidebarcode}^{obs_id}"
            obs_group.obx.obx_3 = obs_id_field
            obs_group.obx.obx_5 = obs_values_add[idx_add]
            obs_group.obx.obx_11 = 'F'
            msg_output.add(obs_group)
    else:
        pass

    return msg_output

def create_msg(wdir, slide_list, msg_input, msg_input_dict, msg_input_dict2, model_name, list_dup_segments, list_label, list_score):
    """
    This function creates an unsolicited laboratory observation (OUL_R21) message that will be provided in output after the run of the DL model. 
    The message will contain parts of the results of the DL model. 
    
    Message structure:(https://github.com/crs4/hl7apy/blob/develop/hl7apy/v2_6/messages.py):
    'OUL_R21': ('sequence',
               (('MSH', SEGMENTS['MSH'], (1, 1), 'SEG'),
                ('SFT', SEGMENTS['SFT'], (0, -1), 'SEG'),
                ('NTE', SEGMENTS['NTE'], (0, 1), 'SEG'),
                ('OUL_R21_PATIENT', GROUPS['OUL_R21_PATIENT'], (0, 1), 'GRP'),
                ('OUL_R21_ORDER_OBSERVATION', GROUPS['OUL_R21_ORDER_OBSERVATION'], (1, -1), 'GRP'),
                ('DSC', SEGMENTS['DSC'], (0, 1), 'SEG'),)),
    """
    
    msg_output = Message("OUL_R21", validation_level=VALIDATION_LEVEL.TOLERANT)

    # Define the type of results to generate. I will generate the following OBX segments:
        # 1) the predicted label --> String
        # 2) the predicted score --> Number
        # 3) json file with the summary of the run --> encoded in base 64
        # 3) image of the mask --> encoded in base 64
        # 4) csv file with the attention scores/prediction for each tile --> encoded in base 64

    for i, slide in enumerate(slide_list):
        
        tmp_resdir = Path(f"{wdir}/tmp_results/{slide}/{model_name}")
        
        tmp_slidedir = Path(rf"{wdir}/tmp_slides/{slide}/{slide}.mrxs")
        
        # The content of the OBX segments will slightly change basing on weather we are running DL model deployment
        # with patch-level classification models or slide-level classification models.

        # For slide-level classification models, as those provided by WSInfer-MIL and marugoto, the OBX segmernt will
        # store the predicted label and the predicted score. Indeed, slide-level classification models provide in output
        # an overall slide-level prediction.
        if ('porpoise' in model_name) or ('tp53' in model_name) or ('marugoto' in model_name):
            obs_ids = ["MODEL", "PRED_LABEL", "PRED_SCORE"] 
            value_type = ["ST", "ST", "NM"]
            obs_values = [model_name, list_label[i], str(list_score[i])]
            obs_id_add = []
            value_type_add = []
            obs_values_add = []
            
        else:
            # Returns in output as OBX segments all the output files generated by WSInfer
            path_to_mask = Path(f"{tmp_resdir}/masks/{slide}.jpg")

            path_to_csv = Path(f"{tmp_resdir}/model-outputs-csv/{slide}.csv")
            
            # Extract top 5 tiles encoded in base64 only if provided according to model type
            obs_id_add, value_type_add, obs_values_add = top_five_tiles(tmp_slidedir, path_to_csv, model_name, wdir)
        
            # Path to json file
            for file in os.listdir(tmp_resdir):
                if file.endswith(".json"):
                    json_file = file
            path_to_json = Path(f"{tmp_resdir}/{json_file}")
            
            if None in list_label:
                obs_ids = ["MODEL", "RUN", "MASK", "TABLE"] 
                value_type = ["ST", "ED", "ED", "ED"]
                obs_values = [model_name, path_to_json, path_to_mask, path_to_csv]
            else:
                obs_ids = ["MODEL", "PRED_LABEL", "PRED_SCORE", "RUN", "MASK", "TABLE"] 
                value_type = ["ST", "ST", "NM", "ED", "ED", "ED"]
                obs_values = [model_name, list_label[i], str(list_score[i]), path_to_json, path_to_mask, path_to_csv]
    
        # Add to the OUL^R21 message the MSH segment
        msg_output = create_msh(msg_input_dict, msg_output)
    
        # Add to the OUL^R21 message the PID segment
        msg_output = create_pid(msg_input, msg_output)
    
        #------------- Order Observation and Observation Results -------------#
    
        if 'ORC' in list_dup_segments:
            howmany = len([key for key in list(msg_input_dict.keys()) if 'ORC' in key])
            for j in range(howmany):
                msg_output = create_order_group(msg_input_dict, msg_input_dict2, msg_output, obs_ids, value_type, obs_values, obs_id_add, value_type_add, obs_values_add, idx_key=f"_{j+1}")
        else:
            msg_output = create_order_group(msg_input_dict, msg_input_dict2, msg_output, obs_ids, value_type, obs_values, obs_id_add, value_type_add, obs_values_add, idx_key = "")
    
        try:
            msg_output.OUL_R21_ORDER_OBSERVATION.validate()
            print("ORDER_OBSERVATION Validated")
        except Exception as e:
            print(e)

        # Validate the entire message
        try:
            msg_output.validate()
            #print("Message Validated!")
        except Exception as e:
            print(e)
            
    return msg_output
    

if __name__ == "crate_output_msg":
    create_msg()

    
