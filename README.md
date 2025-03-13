# Closing the gap in the clinical adoption of computational pathology: a standardized, open-source framework to integrate deep-learning algorithms into the laboratory information system
A standardized, open-source framework to integrate both <ins>publicly available</ins> and <ins>custom developed</ins> deep-learning (DL) models into the anatomic pathology laboratory information system (AP-LIS).

> [!CAUTION]
> All DL models employed in this work as well as the freely available software used for DL model deployment and visualization are non-commercial, open-source resources intended for research use only. Hence, use of the integration framework outside of research context is under the responsibility of the user.

## Updates
- **Version 0.2.0**: Version 0.2.0 of the integration framework allows to run model inference on multiple proprietary slide formats (i.e., MRXS, SVS, NDPI, TIFF, TIF) with [WSInfer](https://github.com/SBU-BMI/wsinfer). DL model inference results can be visualized in QuPath as measurement maps or as color maps.

- **Version 0.1.0**: Version 0.1.0 of the integration framework allows to run model inference on 3DHistech's proprietary MRXS slide format with [WSInfer](https://github.com/SBU-BMI/wsinfer). DL model inference results can be visualized in QuPath as measurement maps or as color maps. The README associated with this version can be found [here](https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/README_v010.md).

> [!NOTE]
In order to use, in addition to [WSInfer](https://github.com/SBU-BMI/wsinfer), also WSInfer-MIL, now renamed to [SpinPath](https://github.com/SBU-BMI/SpinPath), and [marugoto](https://github.com/KatherLab/marugoto), a customization of their source codes is necessary. Please refer to [our publication](https://www.biorxiv.org/content/10.1101/2024.07.11.603091v1) for detailed information on how the source scripts were modified for the purposes of our integration framework. Furthermore, for marugoto, a customized conda environment with scikit v1.1.1 is required.

## Reference publication
If you use our work or parts of it, please cite [our preprint](https://www.biorxiv.org/content/10.1101/2024.07.11.603091v1)!
```bash
@article{angeloni2024closing,
  title={Closing the gap in the clinical adoption of computational pathology: a standardized, open-source framework to integrate deep-learning algorithms into the laboratory information system},
  author={Angeloni, Miriam and Rizzi, Davide and Schoen, Simon and Caputo, Alessandro and Merolla, Francesco and Hartmann, Arndt and Ferrazzi, Fulvia and Fraggetta, Filippo},
  journal={bioRxiv},
  year={2024},    
  doi={https://doi.org/10.1101/2024.07.11.603091}
}
```

## How it works
The developed integration framework relies on a Python-based server-client architecture to: 
1. interconnect the AP-LIS with an AI-based decision support sistem (AI-DSS) via HL7 messaging

<p align="center">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/integration_framework.png" width="600" />
</p>
  
2. run DL model deployment using freely available resources ([WSInfer](https://github.com/SBU-BMI/wsinfer), [WSInfer-MIL](https://github.com/SBU-BMI/wsinfer-mil), [marugoto](https://github.com/KatherLab/marugoto))

3. provide an intuitive visualization of model inference results through colored heatmaps in [QuPath](https://qupath.github.io/)
<p align="center">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/visualization_styles.PNG" width="700" />
</p>

**Types of HL7 messages involved in the interconnection between the AP-LIS and the AI-DSS**
All WSI analysis requests are transmitted from the AP-LIS to the AI-DSS via HL7 Laboratory Order Messages (***OML^O33***). 

**Example of OML^O33 message**
```bash
MSH|^~\&|ZZZ|WWW|XXX|YYYY|20240322080152||OML^O33^OML_O33|2857198947|P|2.6
PID|||PRVPRV43S04A075M^^^^CF~153042^^^^MPI~207444994^^^^CS||NAME^SURNAME||19431104|F|||ADDRESS|||||||||||||||
SPM|1|18584052||MODEL_NAME^MODEL_NAME||||||||||notes|||20240322100000|
ORC|NW|SLIDEBARCODE|| 18-B-01806|SC||||20240322100000|||MDMMDM63M29G224V^CLINICIAN^CLINICIAN|
OBR|1|SLIDEBARCODE||HE^HE||20240322100000|||||||/PATH/TO/ARCHIVE/SLIDE_ID
```
> [!NOTE]
> 1. The fields 4.1 and 4.2 (MODEL_NAME^MODEL_NAME) of the SPM segment should be populated with the name of the DL model to deploy as indicated in the column 'SPM_4.2' of the [encodings_DL.csv](https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/encodings_DL.csv) file.
> 2. Field 13 (/PATH/TO/ARCHIVE/SLIDE_ID) of the OBR segment should be populated with the path to the WSI to analyze. For slides scanned with 3DHistech scanners the location of the WSI is the folder containing the DAT files and the Slidedat.ini file. For other type of slides manufacturers the location of the WSI is the file with extension e.g. svs, ndpi, tif.
> 3. Make sure that slide identifiers do not contain spaces. 

Conversely, DL model inference results generated by the AI-DSS are transmitted to the AP-LIS via HL7 Unsolicited Laboratory Observation Messages (***OUL^R21***).

**Example of OUL^R21 message**
```bash
MSH|^~\&|XXX|YYY|ZZZ|WWW|20240322090848||OUL^R21|0001928917|P|2.6
PID|||PRVPRV43S04A075M^^^^CF~153042^^^^MPI~207444994^^^^CS||NAME^SURNAME||19431104|F|||ADDRESS|||||||||||||||
ORC|NW|SLIDEBARCODE|| 18-B-01806|SC||||20240322100000|||MDMMDM63M29G224V^CLINICIAN^CLINICIAN|
OBR|1|SLIDEBARCODE||HE^HE||20240322100000|||||||/PATH/TO/ARCHIVE/SLIDE_ID
OBX|1|ST|SLIDEBARCODE^MODEL||MODEL_NAME||||||F
OBX|2|ED|SLIDEBARCODE^RUN||b‘run_metadata.json’||||||F
OBX|3|ED|SLIDEBARCODE^MASK||b‘mask.jpg’||||||F
OBX|4|ED|SLIDEBARCODE^TABLE||b‘models_output.csv’||||||F
```

## Get started
### Clone the GitHub repository
The code made available on this GitHub page has been tested on a remote server based on Ubuntu's LTS operating system, equipped with one NVIDIA GPU, with a **QuPath installation v0.4.3** and **numpy<2.0**.
To get started, clone the GitHub respository through the command:
```bash
git clone https://github.com/MiriamAng/IntegrationFramework_APLIS.git
```
or
```bash
git clone git@github.com:MiriamAng/IntegrationFramework_APLIS.git
```

### Create the conda environment and install the required packages
1. Crete the conda environment *env_integration*
```bash
conda create -n env_integration
```
2. Activate the conda environment
```bash
conda activate env_integration
```
3. Install Pytorch
   
Please refer to [PyTorch's installation instructions](https://pytorch.org/get-started/locally/) and choose the installation instructions that fit your operating system.
If you have a GPU, make sure that PyTorch detects it by running the following code snippet. It should returns True.
```bash
import torch
print(torch.cuda.is_available())
```
4. Install WSInfer
   
Please refer to the [official WSInfer documentation](https://github.com/SBU-BMI/wsinfer) for further details. 
```bash
python -m pip install wsinfer
```
5. Install [paquo](https://github.com/Bayer-Group/paquo)
```bash
conda install -c conda-forge paquo
```
Make sure that paquo is using a working QuPath installation by running:
```bash
paquo --qupath-version
```
If you get in output a "ValueError: no valid qupath installation found", it means that: 

(i) either QuPath is not installed on your system

(ii) or paquo is not able to correctly retrieve QuPath installation.
After QuPath installation, make sure that paquo is able to retrieve via environmental variable:
If (i) then you can download a specific QuPath version by running:
```bash
export PAQUO_QUPATH_DIR="/some/path/to/your/QuPath/installation"
```
or via [.paquo.toml.file](https://paquo.readthedocs.io/en/latest/configuration.html)

6. Install openslide
```bash
conda install -c conda-forge openslide-python
```
7. Install the following other packages
```bash
pip install hl7apy
```
```bash
conda install -c conda-forge colorama
```
```bash
conda install -c conda-forge matplotlib
```
### Default folders structure
By default, the integration framework assumes that you have under your current working directory:
1. a folder called *slides_archive* storing the digitized slides to analyze.
Below is an exemplary slides_archive folder storing WSIs scanned with a 3Histech scanner. Note! If the MRXS files are not found in the folder they will be automatically created before any further processing;
2. a csv file called *encodings_DL.csv* storing information on the models to deploy, including output classes and the type of visualization in QuPath. 
You can start from the file provided in [this GitHub page](https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/encodings_DL.csv) which contains all WSInfer built-in models. If want to add your own customized model to the list of available models, please make sure to update the encodings_DL.csv accordingly;
3. (Optional, only if you need to deploy custom DL models) a folder called *custom_DL_models* structured as in the example below.
For customized models a model.pt file storing model's weights and a config.json file are necessary. See the official [WSInfer documentation](https://wsinfer.readthedocs.io/en/latest/user_guide.html#use-your-own-model) for deployment of your own models;

During model inference the folder *tmp_slides* will be then created to temporarly store the slides to analyze. This folder will be cleaned up every 3 hours. 
Model inference results will be stored under the *inference_results* folder, that will be automatically created. 
```bash
slides_archive/
├─ slide_1/
├─ slide_1.mrxs
├─ slide_2.ndpi
├─ slide_3.svs

custom_DL_models/
├─ custom_dl_model_1/
│  ├─ config.json
│  ├─ model.pt
├─ custom_dl_model_2/
│  ├─ config.json
│  ├─ model.pt

encodings_DL.csv

*tmp_slides/
├─ slide_1/
│  ├─ slide_1/
│  ├─ slide_1.mrxs
├─ slide_2/
│  ├─ slide_2.ndpi
├─ slide_3/
│  ├─ slide_3.svs

*inference_results/
├─ slide_1/
│  ├─ dl_model_1/
│  │  ├─ run_metadata.json
│  │  ├─ patches/
│  │  ├─ masks/
│  │  ├─ model-output-geojson/
│  │  ├─ model-output-csv/
│  │  ├─ qupath-proj/
│  │  │  ├─ slide_2_QuPathProj-dl_model_1/
│  │  │  │  ├─ classifiers/
│  │  │  │  ├─ data/
│  │  │  │  ├─ slide_2-dl_model_1.qpproj
│  │  │  │  ├─ project.qpproj.backup
│  ├─ dl_model_2/
│  ├─ dl_model_3/
├─ slide_2/
│  ├─ dl_model/
```

### Customize the main script
Once the GitHub repository has been cloned, and the conda environment set-up, in order to run the integration framework the main script [server_client_system.py](https://github.com/MiriamAng/IntegrationFramework_APLIS/tree/main/src) needs to be customized to set:
- the IP addresses and the ports to implement the server-client functionality between AI-DSS and AP-LIS. In server mode, the AI-DSS listens for incoming OML^O33 messages, sends ACK messages to the AP-LIS, and processes the input messages. In client mode, the AI-DSS transmits DL inference results to the AP-LIS as OUL^R21 messages and remains listening for the ACK message, upon receipt of which the connection between the AP-LIS and the AI-DSS is closed. 
- the path to the QuPath installation

To this aim:
1. set IP address and port (variables *hs*, *ps* - lines 371-372 in server_client_system.py) of the AI-DSS in server mode.
>**NOTE!** This correspond to the private IP address of the computer you are running the integration framework on.
2. set IP address and port (variables *hlis*, *plis* - lines 377-378 in server_client_system.py) of the AP-LIS, which is required in order to communicate analysis results.
>**NOTE!** This IP address is the public IP address of the AP-LIS.      
3. set the path to your QuPath installation (variable *paquo_qupath_dir* - line 399 in server_client_system.py)


### Run the main script
Once the aforementioned steps have been performed, you can initiate the integration framework and start listening for incoming HL7 messages by running:
```bash
python /path/to/IntegrationFramework_APLIS/src/server_client_system.py
```

## How to test the integration framework 
To test the integration framework, assume that the system on which DL model deployment is performed acts as the AI-DSS and the system sending HL7 messages to the AI-DSS acts as the AP-LIS. This can be simualted using [Hapi Test Panel](https://hapifhir.github.io/hapi-hl7v2/hapi-testpanel/install.html) that can be downloaded from [here](https://sourceforge.net/projects/hl7api/files/hapi-testpanel/2.0.1/). HAPI Test Panel is as a comprehensive message editor, transmitter, and receiver designed to send, receive, and edit HL7 messages for testing purposes by allowing both transmitting HL7 messages to a specified server and listening for incoming messages. Information on Hapi Test Panel usage can be found in the official [documentation](https://hapifhir.github.io/hapi-hl7v2/hapi-testpanel/install.html).
If HAPI Test Panel is installed on the same computer used to run the integration framework, then *hs=hlis*=('localhost' OR '127.0.0.1'). 

The images below provide an example on how to make the integration framework work with the help of Hapi Test Panel after you correctly set-up IP addresses and ports in the server_client_system.py script. Note! This example referes to a scenario where HL7 messages are sent from the same computer on which DL models are deployed, i.e., **AI-DSS and AP-LIS are on the same computer**.  

- *hs*, *ps*, *hlis*, and *plis* variables provided in the main script server_client_system.py:
  
<p align="left">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/Screenshot_1.JPG" width="800" />
</p>

- Set in HAPI Test Panel the correct IP addresses and ports for both the "Sender connection" and the "Receiving connection" using the variables set in the python script as follows:
<p align="center">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/Screenshot_2.JPG" width="800" />
</p>


<p align="center">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/Screenshot_3.JPG" width="800" />
</p>

- Activate the conda environment of the integration framework and run:
```bash
python /path/to/IntegrationFramework_APLIS/src/server_client_system.py
```
You should see printed on the terminal:
```bash
......listening for connections on 127.0.0.1:21111
```
- From HAPI Test Panel click on AI-DSS from the tab "Sending Connections" and then click on the play button

If the connection between AI-DSS and AP-LIS was correctly established then you should see printed on the terminal:
```bash
Connected to: ('127.0.0.1', A_PORT_NUMBER)
```
- From HAPI Test Panel click on AP-LIS from the tab "Receiving Connections" and then click on the play button

- Once both sending and receiving connections are activated, you can send the HL7 message to the AI-DSS by providing the input the correct model for deployment and the correct path to the slide to analyze:
<p align="center">
  <img src="https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/docs/Screenshot_4.JPG" width="800" />
</p>

## References
1) Kaczmarzyk, J. R. et al. Open and reusable deep learning for pathology with WSInfer and QuPath. NPJ Precis. Oncol. 8, 9 (2024).
2) WSInfer-MIL: https://zenodo.org/records/12680704
3) marugoto: https://github.com/KatherLab/marugoto
4) Bankhead, P. et al. QuPath: Open source software for digital pathology image analysis. Sci. Rep. 7, 1-7 (2017).


