# -*- coding: utf-8 -*-
"""
The script reads the input OML^O33 HL7 message and extracts all the necessary information (e.g., model name, WSI identifier)
for further processing.

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

import os

from pathlib import Path
from hl7apy.parser import parse_message
from hl7apy.exceptions import UnsupportedVersion


def extract_slide_id(msg_input_dict: dict) -> str:
    """
    This function extracts slide identifier(s) from the input OML^O33 input message.

    :param msg_input_dict: stores the segments/fields of the input OML^O33 message
    :return: a string containing the slide identifier
    """
    str_slide_path = msg_input_dict["OBR"]["OBR_13"]
        
    slide_path = Path(rf"{str_slide_path}")

    # If the path to the slide is a directory, then it means that it was scanned with a 3DHistech scanner
    if os.path.isdir(slide_path):
        vendor = '3DHistech'
    else:
        vendor = 'Other'

    slide_id = slide_path.name
    
    return vendor, slide_id
        

def extract_msg_info(hl7_input: str):
    """
    This function takes in input the OML^O33 HL7 message sent by the AP-LIS and:
    1) extracts the name of the deep-learning (DL) model to apply from the fields 4.1 or 4.2 of the SPM segment
    2) stores the content of the input message in a dictionary
    3) extracts the name of the WSI to process from field 13 of the OBR segment

    :param hl7_input: input OML^O33 HL7 message
    """
    
    try:
        msg_input = parse_message(hl7_input, find_groups=False)
    except UnsupportedVersion:
        msg_input = parse_message(hl7_input, find_groups=False)
    
    # Extract either from field SPM 4.1 or from field 4.2 the name of the DL model
    dl_model = msg_input.spm.spm_4.spm_4_2.value

    # Store all the fields/segments of the input HL7 message in two dictionaries:
    msg_input_dict = {}

    msg_input_dict2 = {}

    for segment in msg_input.children:
        segment_name = str(segment)
        segment_name = segment_name.split(" ")[1].split(">")[0]
        print(f"Processing segment:{segment}")
        msg_subset = {}
        for attribute in segment.children:
            field_value = attribute.value
            field_str = str(attribute)
            field = field_str.split(" ")[1]
            msg_subset[f"{field}"] = field_value
        msg_input_dict[f"{segment_name}"] = msg_subset
        msg_input_dict2[f"{segment_name}"] = segment.value
        
    # Extract the slide identifier
    vendor, slide_id = extract_slide_id(msg_input_dict)

    return vendor, dl_model, slide_id, msg_input, msg_input_dict, msg_input_dict2