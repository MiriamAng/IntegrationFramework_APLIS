# -*- coding: utf-8 -*-
""" The script implements the main server/client architecture for sending, receiving and processing HL7 messages.

Author: Miriam Angeloni
E-Mail: miriam.angeloni@uk-erlangen.de
"""

import os
import pickle
import queue
import socket
import shutil
import threading
import time

from colorama import init, Fore
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm
from utils import read_input_msg, create_ack_msg, model_inference, create_output_msg

# Automatically reset the style to normal after each printing
init(autoreset=True)

def save_queue(queue_obj, file_path):
    """
    This function saves the queue object containing the input HL7 messages to process as pickle file.
    In case the server stops working, upon its start the queue is loaded and the input HL7 messages retrieved to be processed.
    :param queue_obj: the queue object
    :param file_path: path to the pkl file storing the list of input HL7 messages to process
    """
    with open(file_path, 'wb') as f:
        pickle.dump(list(queue_obj.queue), f)


def load_queue(file_path):
    """
    :param file_path: path to the pkl file containing the list of input HL7 messages to process
    :return: the queue containing the input HL7 messages that still need to be processed
    """
    # Initialize the variable input_queue to avoid initialization errors
    input_queue = None

    # If the file path does not exist, create it as empty queue and save it
    if not file_path.is_file():
        input_queue = queue.Queue(maxsize=0)
        print(f"Queue not existing yet, creating it under: {file_path}")
        save_queue(input_queue, file_path)
    else:
        try:
            with open(file_path, 'rb') as f:
                input_queue_list = pickle.load(f)
            input_queue = queue.Queue(maxsize=0)
            for item in input_queue_list:
                input_queue.put(item)
            queue_obj_size = input_queue.qsize()
            if queue_obj_size == 0:
                print(f"Found {queue_obj_size} slides to analyze, waiting for incoming input HL7 messages!")
            else:
                print(f"Found {queue_obj_size} slides to analyze, proceeding with the analysis of the input HL7 messages!")
        except Exception as e:
            print(f"Error in retrieving the queue \n{e}")

    return input_queue


def remove_slides(directory, hrs=3):
    """
    This function removes slides older than 3 hours under the temporary slides folder

    :param directory: path to the directory to clean up, in this case the temporary slides folder
    :param hrs: time, in hours, between one cleaning process and another one
    """
    now = datetime.now()
    cutoff_time = now - timedelta(hours=hrs)

    for subfolder in directory.iterdir():
        if subfolder.is_dir():
            # Get the modification time of the folder
            mod_time = datetime.fromtimestamp(subfolder.stat().st_mtime)
            if mod_time < cutoff_time:
                print(f"...Removing slide {subfolder} from tmp_slidedir")
                shutil.rmtree(subfolder)
        else:
            pass


def cleanup_worker(directory: str | Path,
                   sleep_time: int):
    """
    This function defines the worker that will be used in the thread for cleaning up the temporary slides folder

    :param directory: path to the directory to clean up, in this case the temporary slides folder
    :param sleep_time: time, in hours, between one cleaning process and another one
    """
    while True:
        remove_slides(directory)
        time.sleep(sleep_time)


def strip_mllp_framing(byte_stream: bytes) -> bytes:
    """
    This function removes the MLLP framing from the HL7 input message

    :param byte_stream: input HL7 message received as bytes stream with the MLLP framing
    :return: input HL7 message as bytes stream without the MLLP framing
    """
    start_pos = byte_stream.find(b'\x0b') + 1
    end_pos = byte_stream.find(b'\x1c\r')

    # Extract the message content between the start and end positions of the MLLP framing
    hl7_msg = byte_stream[start_pos:end_pos]

    return hl7_msg



def start_client(address_lis: tuple,
                 msg: bytes):
    """
    In client mode, the AI-DSS:
     1) transmits the output OUL^R21 message to the AP-LIS
     2) listen for incoming ACK messages from the AP-LIS

    :param address_lis: public IP address of the AP-LIS as defined in the main() function
    :param msg: OUL^R21 message to send to the AP-LIS storing results of DL model deployment
    """

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the AP-LIS
        client_socket.connect(address_lis)

        # Transmit to the AP-LIS the OUL^R21 HL7 message storing results of DL model inference
        client_socket.sendall(msg)

        # Wait for the ACK message from the AP-LIS
        ack = b''
        while not ack.endswith(b'\x1c\x0d'):
            ack += client_socket.recv(4096)  # Specify the buffer size

        # Process the ACK message by stripping off the MLLP framing
        ack_message = strip_mllp_framing(ack)

        print(f"{Fore.YELLOW}*" * 100)
        print(f"{Fore.YELLOW}Received acknowledgment from the AP-LIS: \n{ack_message}")
        print(f"{Fore.YELLOW}*" * 100)

        client_socket.close()

        print(f'Connection with {address_lis} closed!')

    finally:
        # Close the connection
        client_socket.close()



def msg_worker(slides_archive: str | Path,
               wdir: str | Path,
               address_lis: tuple,
               num_retries: int,
               delay_secs: int):
    """
     This function processes each OML^O33 HL7 message stored in the queue, and it is run using a multi-threading approach

    :param slides_archive: full path to the directory storing WSIs
    :param wdir: full path to the working directory
    :param address_lis: public IP address of the AP-LIS as defined in the main() function
    :param num_retries: maximum number of analysis attempts for a given slide in case of failures
    :param delay_secs: waiting time in seconds before starting a new analysis attempt
    """

    while True:

        # Extract from the queue the first message to process following a FIFO rule
        msg, retry = input_msg_queue.get()

        print("Working paths:")
        print("-" * 40)
        print(f"SLIDES ARCHIVE: {slides_archive}")
        print(f"WORKING DIRECTORY: {wdir}")
        print("-" * 40)

        # Process the input HL7 message (OML_O33)
        print("Reading Input Message........")

        try:
            cod_model, slide_id, msg_input, msg_input_dict, msg_input_dict2 = read_input_msg.extract_msg_info(msg)

        except Exception as e:
            print(f"Error in extracting info from the input message. \n{e} for message {msg}")

            # Send a negative ACK message to the AP-LIS
            neg_ack = create_ack_msg.create_message(msg, anyerror=True, errorvalue=e)

            # Transform the negative ACK message in a sequence of bytes
            neg_ack_out = neg_ack.to_mllp().encode('utf-8')

            # Send the encoded negative ACK HL7 message to the AP-LIS (i.e., the server)
            start_client(address_lis, neg_ack_out)

            # Mark the HL7 message as processed
            input_msg_queue.task_done()

            continue

        print(f"{Fore.GREEN}*" * 100)
        print(f"{Fore.GREEN}Started processing message for slide ID: {slide_id}")
        print(f"{Fore.GREEN}*" * 100)

        # Run model inference
        try:
            model_name, pred_label, pred_score = model_inference.run_inference(slide_id, cod_model,
                                                                                     slides_archive, wdir, paquo_qupath_dir)
        except Exception as e:
            print(f"Error processing message. \n{e} for slide ID {slide_id}")
            if retry < num_retries:
                print(
                    f"... Retrying to process slide {slide_id} in {delay_secs} seconds: attempt "
                    f"{retry + 1}\\{num_retries}")
                time.sleep(delay_secs)
                input_msg_queue.queue.insert(0, (msg, retry + 1))
                continue
            else:
                print(f"Failed to process slide {slide_id} after {num_retries} attempts... Sending a negative ACK message and moving to the next slide")

                # Send a negative ACK message to the AP-LIS
                neg_ack = create_ack_msg.create_message(msg, anyerror=True, errorvalue=e)

                # Transform the negative ACK message in a sequence of bytes
                neg_ack_out = neg_ack.to_mllp().encode('utf-8')

                # Send the encoded negative ACK HL7 message to the AP-LIS (i.e., the server)
                start_client(address_lis, neg_ack_out)

                # Mark the HL7 message as processed
                input_msg_queue.task_done()

                continue

        # Create the output OUL^R21 HL7 message
        for _ in tqdm(range(100), desc="Creating Output Message"):
            oul_r21_msg = create_output_msg.create_msg(wdir, slide_id, msg_input, msg_input_dict,
                                                             msg_input_dict2, model_name,
                                                             pred_label, pred_score)
            time.sleep(0.02)

        print(f"{Fore.GREEN}*" * 100)
        print(f"{Fore.GREEN}Finished processing message for slide ID: {slide_id}")
        print(f"{Fore.GREEN}*" * 100)

        # Transform the output message in a sequence of bytes
        oul_r21_out = oul_r21_msg.to_mllp().encode('utf-8')

        # Send the encoded OUL^R21 HL7 message to the AP-LIS (i.e., the server)
        start_client(address_lis, oul_r21_out)

        # Mark the HL7 message as processed
        input_msg_queue.task_done()



def store_msg_produce_ack(address_as_server: tuple,
                          msg_queue: queue.Queue):
    """
    This function:
     1) stores in a queue each single OML^O33 HL7 input message received from the AP-LIS
     2) and generates an ACK message before any further message processing.

    :param address_as_server: local IP address of the system where the AI-DSS is implemented
    :param msg_queue: queue object storing all the input HL7 messages that need to be processed
    """

    # Build a TCP socket for accepting connections from the AP-LIS
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # To avoid "Python [Errno 98] Address already in use" when interrupting the python script and re-starting it soon after
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind function since we are hosting
    server.bind(address_as_server)

    # Listen for incoming connections
    server.listen()
    print(f"......listening for connections on {address_as_server[0]}:{address_as_server[1]}")

    while True:
        # For each connection we (AI-DSS) get a new socket that allows us to communicate with the client (AP-LIS) from which the request arrived
        # Create the communication socket
        commun_socket, address = server.accept()
        print(f"Connected to: {address}")

        # MLLP frame starts with b'\x0b' (header) and ends with b'\x1c\x0d' (footer). 
        # The input OML^O33 HL7 message is the actual string part between the header and the footer, therefore
        # we have to retrieve the actual content in between.
        input_msg = b''
        # Keep reading the incoming bytes stream until you reach the footer sequence.
        while not input_msg.endswith(b'\x1c\x0d'):
            input_msg += commun_socket.recv(4096)  # Specify the buffer size

        print(f"{Fore.YELLOW}*" * 100)
        print(f"{Fore.YELLOW}Received input message: \n{input_msg}")
        print(f"{Fore.YELLOW}*" * 100)

        # Strip off MLLP framing
        hl7_msg = strip_mllp_framing(input_msg)

        # Decode bytes to string
        hl7_msg_decoded = hl7_msg.decode('utf-8')

        # Process the HL7 message received in input and extract useful information in order to:
        # 1) produce an ACK message
        # 2) run DL model inference
        # 3) produce an output OML^R21 HL7 message

        # 1) Generate the ACK message to send to the AP-LIS
        ack_msg = create_ack_msg.create_message(hl7_msg_decoded)

        # Store the incoming messages in a queue as tuples together with the number "0" that servers as a counter for the number of retries in case of failure.
        msg_queue.put((hl7_msg_decoded, 0))

        print(f"{Fore.YELLOW}Input message inserted in the queue.")
        print(f"{Fore.YELLOW}*" * 40)

        print(f"{Fore.RED}*" * 40)
        print(f"{Fore.RED}QUEUE SIZE: {input_msg_queue.qsize()}")
        print(f"{Fore.RED}*" * 40)

        # After putting the message in the queue, the AI-DSS can send an ACK message to the AP-LIS
        ack_out = ack_msg.to_mllp().encode('utf-8')

        commun_socket.send(ack_out)

        print(f"{Fore.YELLOW}*" * 100)
        print(f"{Fore.YELLOW}ACK message sent to the AP-LIS: \n{ack_out}")
        print(f"{Fore.YELLOW}*" * 100)

        # Close the communication socket once the ACK message has been sent
        commun_socket.close()
        print(f'Connection with {address} closed!')



def main():
    """
    The function defines the main variables necessary for the integration framework.
    """

    # Define the slides archive
    slides_dir = Path(rf"{working_dir}", "slides_archive")

    # Define the temporary slides folder where all the slides undergoing model deployment will be temporarily stored.
    # This folder will be cleaned up at regular time intervals as defined by the variable "cleanup_interval_seconds"
    tmp_slides_dir = Path(rf"{working_dir}", "tmp_slides")

    # Create the folder if it does not exist
    tmp_slides_dir.mkdir(parents=True, exist_ok=True)

    folder_to_clean = tmp_slides_dir

    # Define variables needed to re-try a process if it fails
    # Constants
    nmax = 3
    delay = 3  # in seconds

    # Define IP address and port as server, i.e., when listening for incoming analysis requests from the AP-LIS
    #hs = socket.gethostbyname(socket.gethostname())
    hs = '127.0.0.1' # need to be changed according to the private IP address of the system where the integration is running
    ps = 21111 # can be customized by users
    address_as_server = (hs, ps)

    # Define the public IP address and the port of the AP-LIS for communication when the AI-DSS acts as a client to send results
    # of analysis requests
    hlis = '127.0.0.1' # need to be changed according to the public IP address of the AP-LIS
    plis = 17779 # can be customized by users
    address_lis = (hlis, plis)

    # Start the message worker thread to process the messages in the queue
    msg_worker_thread = threading.Thread(target=msg_worker, args=(
        slides_dir, working_dir, address_lis, nmax, delay))
    msg_worker_thread.daemon = True
    msg_worker_thread.start()

    # Start the clean-up worker thread to clean up the tmp_slides folder every hour
    cleanup_interval_seconds = 3600  # 1 hour
    cleanup_worker_thread = threading.Thread(target=cleanup_worker, args=(folder_to_clean, cleanup_interval_seconds))
    cleanup_worker_thread.daemon = True
    cleanup_worker_thread.start()

    store_msg_produce_ack(address_as_server, input_msg_queue)


if __name__ == "__main__":

    # Set environmental variable to the location of QuPath installation
    paquo_qupath_dir = '/path/to/QuPath/QuPath-X.X.X'
    os.environ["PAQUO_QUPATH_DIR"] = paquo_qupath_dir

    # Define as working directory the current working directory
    working_dir = Path(os.getcwd())

    # Define a log folder where the queue file will be stored
    queue_loc = Path(rf"{working_dir}", "log")

    # Create the folder if it does not exist
    queue_loc.mkdir(parents=True, exist_ok=True)

    # Define the exact path to the pickle file
    queue_file = Path(queue_loc, "queue_to_analyze.pkl")

    input_msg_queue = load_queue(queue_file)

    main()
