# Closing the gap in the clinical adoption of computational pathology: a standardized, open-source framework to integrate deep-learning algorithms into the laboratory information system
A standardized, open-source framework to integrate both <ins>publicly available</ins> and <ins>custom developed</ins> deep-learning (DL) models into the anatomic pathology laboratory information system (AP-LIS).
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

> [!CAUTION]
> All DL models employed in this work as well as the freely available software used for DL model deployment and visualization are non-commercial, open-source resources intended for research use only. Hence, use of the integration framework outside of research context is under the responsibility of the user.

## Types of HL7 messages involved in the interconnection between the AP-LIS and the AI-DSS
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
> 1. The fields 4.1 and 4.2 (MODEL_NAME^MODEL_NAME) of the SPM segment should be populated with the name of the DL model to deploy.
> 2. Field 13 (/PATH/TO/ARCHIVE/SLIDE_ID) of the OBR segment should be populated with the path to the WSI to analyze.

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
> [!NOTE]
> The output of DL model inference results are transmitted from the AI-DSS to the AP-LIS through OBX segments. 

## Software requirements and setup
The integration framework has been developed and tested on a remote server based on Ubuntu's LTS operating system equipped with two AMD Radeon Instinct MI210 GPUs. Hence, PyTorch was installed with ROCm support. 
For NVIDIA GPUs please customize PyTorch installation with CUDA support. 

To get started, clone the GitHub respository through the command:
```bash
git clone https://github.com/MiriamAng/IntegrationFramework_APLIS.git
```
or
```bash
git clone git@github.com:MiriamAng/IntegrationFramework_APLIS.git
```

We suggest to run the integration framework in a dedicated conda environment. This can be built through the yml file provided [here](https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/conda_env.yml) as follows:
```bash
# Crete the conda environment env_name
conda env create -f /path/to/IntegrationFramework_APLIS/conda_env.yml

# Activate the conda environment
conda activate env_name
```


Once the GitHub repository has been cloned, and the conda environment activated, in order to run the integration framework:
1. navigate to the directory IntegrationFramework_APLIS
```bash
cd IntegrationFramework_APLIS
```
2. customize the script src/server_client_system.py by to:
    * provide the values of IP address and port (variables *hs*, *ps*) of the system as server, i.e., when listening for incoming analysis requests from the AP-LIS.
    >**NOTE!** This IP address is the private IP address of the computer you are running the integration framework on.
    
    * provide the values of IP address and port (variables *hlis*, *plis*) of the AP-LIS for sending OUL^R21 messages to communicate analysis results.
    >**NOTE!** This IP address is the public IP address of the AP-LIS. If the AP-LIS is in the same LAN of the computer you are running the integration framework on, then *hs=hlis*.
    
    * provide the path to the slides archive folder (variable *slides_dir*). The default value is a folder called slides_archive under the current working directory.
      
3. run the script under src/server_client_system.py and listen for incoming OUL^O33 HL7 messages 
```bash
python src/server_client_system.py
``` 


### NOTE!
> 1. The integration framework has been developed and tested using WSIs in MRXS format. For MRXS files, (i) a directory exists storing a file named Slidedat.ini; (ii) a mrxs file needs to be created in the same location as the directory, with the same name as the directory plus the .mrxs extension in order to be opened in Qupath. Hence, field 13 of the OBR segment of the incoming OUL^O33 message is populated with the path to a directory rather than with the path to a file (e.g., svs, ndpi).

> 2. [WSInfer-MIL](https://github.com/SBU-BMI/wsinfer-mil) and [marugoto](https://github.com/KatherLab/marugoto) source codes were partially costumized. Please refer to the Supplementary Material of [our preprint](https://www.biorxiv.org/content/10.1101/2024.07.11.603091v1) for detailed information on how the scripts were modified for the purposes of our integration framework. 

> 3. Scripts were written to contemplate the processing of multiple WSIs associated with a given sample (i.e., multiple SPM segments and multiple OBR/ORC segment pair). However, in the actual implementation of the framework, each OML^O33 message corresponds to the analysis request of a single WSI (i.e., a single SPM segment and a single OBR/ORC segment pair), even when multiple WSIs are available for the same patient.

> 4. The scripts assume that you have a CSV file called encodings_DL.csv containing information on the DL models to deploy integrated in the framework. An example of encodings_DL.csv file can be downloaded found [here](https://github.com/MiriamAng/IntegrationFramework_APLIS/blob/main/encodings_DL.csv). If want to add your own customized model to the list of available models, please make sure to update the encodings_DL.csv accordingly. 

> 5. The fields 4.1 and 4.2 of the SPM segment of the input OML^O33 HL7 message should be populated with the name of the DL model from column 'SPM_4.2' of the encodings_DL.csv file.



### Example of results folder structure after deployment of a DL model
**1. WSInfer built-in models**

Example of results folder structure afer running one of the WSInfer built-in models, e.g., the *colorectal-resnet34.penn* model. 
```bash
\---tmp_results
    \---00002548745622
        \---colorectal-resnet34.penn
            |   run_metadata.json
            |
            +---masks
            |       00002548745622.jpg
            |
            +---model-outputs-csv
            |       00002548745622.csv
            |       00002548745622_withoffset.csv
            |
            +---model-outputs-geojson
            |       00002548745622.geojson
            |
            +---patches
            |       00002548745622.h5
            |
            \---qupath-proj
                \---00002548745622_QuPathProj-colorectal_resnet34_penn
                    |   00002548745622-colorectal_resnet34_penn.qpproj
                    |   00002548745622-colorectal_resnet34_penn.qpproj.backup
                    |   project.qpproj.backup
                    |
                    +---classifiers
                    \---data
```

**2. WSInfer-MIL built-in models**

Example of results folder structure afer running one of the WSInfer-MIL built-in models, e.g., the *pancancer-tp53-mut.tcgan* model. 

**3. marugoto**

Example of results folder structure after running the *braf-attMIL-marugoto* model with marugoto 
```bash
\---tmp_results
    \---00002548745621
        \---braf-attMIL-marugoto
            |   cli-table.csv
            |   patient-preds.csv
            |   slide-table.csv
            |
            \---patches
                    00002548745621.h5
```


## How to test the integration framework
To test the integration framework, you can use [Hapi Test Panel](https://hapifhir.github.io/hapi-hl7v2/hapi-testpanel/install.html) that can be downloaded from [here](https://sourceforge.net/projects/hl7api/files/hapi-testpanel/2.0.1/).
Hapi Test Panel is as a comprehensive message editor, transmitter, and receiver designed to send, receive, and edit HL7 messages for testing purposes by allowing both transmitting HL7 messages to a specified server and listening for incoming messages. Information on Hapi Test Panel usage can be found in the official [documentation](https://hapifhir.github.io/hapi-hl7v2/hapi-testpanel/install.html).
> [!NOTE]
> Make sure to set-up the correct port and IP address for the server and the client according to the configuration of your system. 


## Citation
If you find our work useful, please cite [our preprint](https://www.biorxiv.org/content/10.1101/2024.07.11.603091v1)!
```bash
@article{angeloni2024closing,
  title={Closing the gap in the clinical adoption of computational pathology: a standardized, open-source framework to integrate deep-learning algorithms into the laboratory information system},
  author={Angeloni, Miriam and Rizzi, Davide and Schoen, Simon and Caputo, Alessandro and Merolla, Francesco and Hartmann, Arndt and Ferrazzi, Fulvia and Fraggetta, Filippo},
  journal={bioRxiv},
  year={2024},    
  doi={https://doi.org/10.1101/2024.07.11.603091}
}
```

## References
1) Kaczmarzyk, J. R. et al. Open and reusable deep learning for pathology with WSInfer and QuPath. NPJ Precis. Oncol. 8, 9 (2024).
2) WSInfer-MIL: https://zenodo.org/records/12680704
3) marugoto: https://github.com/KatherLab/marugoto
4) Bankhead, P. et al. QuPath: Open source software for digital pathology image analysis. Sci. Rep. 7, 1-7 (2017).


