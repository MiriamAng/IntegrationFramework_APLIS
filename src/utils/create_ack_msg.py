# -*- coding: utf-8 -*-
"""
The script creates an acknowledgment (ACK) message that the AI-DSS sends to the AP-LIS upon reception of an OML^O33 HL7 message.

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

from random import randint

from hl7apy.exceptions import UnsupportedVersion
from hl7apy.core import Message
from hl7apy.consts import VALIDATION_LEVEL
from hl7apy.parser import parse_message


def generate_msg_ctrl_id(ndigits: int) -> str:
    """
    This function creates a random message control ID made up of a number of digits equal to ndigits.
    Note: the maximum length for this field should be 199.

    :param ndigits: number of digits that make up the message control ID
    :return: a random message control ID, in the form of a string object
    """

    list_digits = [str(randint(0, 9)) for _ in range(ndigits)]

    msg_ctrl_id = str("".join(list_digits))

    return msg_ctrl_id

def create_message(hl7_input: str,
                   anyerror = False,
                   errorvalue = None) -> str:
    """
    This function creates an ACK message that will be sent to the AP-LIS once the input OML^O33 HL7 message has
    been received. By default, the function will generate a positive message, i.e., without any errors being raised.
    Message structure (https://github.com/crs4/hl7apy/blob/develop/hl7apy/v2_6/messages.py):
    'ACK': ('sequence',
                (('MSH', SEGMENTS['MSH'], (1, 1), 'SEG'),
                 ('SFT', SEGMENTS['SFT'], (0, -1), 'SEG'),
                 ('UAC', SEGMENTS['UAC'], (0, 1), 'SEG'),
                 ('MSA', SEGMENTS['MSA'], (1, 1), 'SEG'),
                 ('ERR', SEGMENTS['ERR'], (0, -1), 'SEG'),))

    :param hl7_input: string storing the input OML^O33 HL7 message
    :param anyerror: boolean determining whether the ACK will be a  positive ACK or a negative ACK
    :param errorvalue: string describing the error occurred
    :return: a string storing the ACK message
    """

    try:
        msg_input = parse_message(hl7_input, find_groups=False)
    except UnsupportedVersion:
        msg_input = parse_message(hl7_input, find_groups=False)

    # Create the ACK message
    ack_msg = Message("ACK", validation_level=VALIDATION_LEVEL.STRICT)

    # Define the MSH segment
    ack_msg.msh.msh_3 = msg_input.msh.msh_5.value
    ack_msg.msh.msh_4 = msg_input.msh.msh_6.value
    ack_msg.msh.msh_5 = msg_input.msh.msh_3.value
    ack_msg.msh.msh_6 = msg_input.msh.msh_4.value
    ack_msg.msh.msh_9 = "ACK"
    ack_msg.msh.msh_10 = generate_msg_ctrl_id(16) # Generate the message control ID
    ack_msg.msh.msh_11 = "P"
    ack_msg.msh.msh_12 = "2.6"

    # Define the MSA segment
    ack_msg.add_segment('MSA')
    # The field MSA_2 contains the message control ID of the message sent by the sending system (AP-LIS).
    # This allows the sending system to associate this response with the correct message.
    ack_msg.msa.msa_2 = msg_input.msh.msh_10.value

    if not anyerror:
        # Positive ACK message
        ack_msg.msa.msa_1 = 'AA'
    else:
        # Negative ACK message
        ack_msg.msa.msa_1 = 'AE'
        ack_msg.add_segment('ERR')
        ack_msg.err.err_1 = f"^^^207&{errorvalue}"
        ack_msg.err.err_3 = "207"
        ack_msg.err.err_4 = "E"

    # Validate the ACK message
    # try:
    #     ack_msg.validate()
    #     print("ACK Message Validated!")
    # except Exception as e:
    #     pass
    #     print(e)

    return ack_msg
