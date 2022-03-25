## [CMU Linguistic Annotation Backend](https://github.com/neulab/cmulab/) plugin for [ELAN](https://archive.mpi.nl/tla/elan)

This plugin is still a work in progress. Eventually it will allow ELAN users to invoke various services (translation, transcription, POS tagging etc.) provided by the CMU Linguistic Annotation Backend server


### Setup

#### Linux

1. Download the latest version of ELAN from [here](https://archive.mpi.nl/tla/elan/download) and install it:
```
wget https://www.mpi.nl/tools/elan/ELAN-XX_linux.tar.gz
tar xzf ELAN-XX_linux.tar.gz
```

2. [Download a copy of this repo](https://github.com/zaidsheikh/cmulab_elan_extension/archive/refs/heads/main.zip) and unzip it. Copy the `cmulab_elan_extension-main/` folder into ELAN's extensions dir (`ELAN-XX/lib/app/extensions/`).

#### Mac

1. If ELAN is not already installed on your Mac, [download the latest .dmg installer](https://archive.mpi.nl/tla/elan/download) and install it. It should be installed in the `/Applications/ELAN_XX` directory, where `XX` is the name of the version.
2. Download this [zip file](https://github.com/zaidsheikh/cmulab_elan_extension/archive/refs/heads/main.zip) and unzip it. You should see a folder named `cmulab_elan_extension-main` containing the contents of this repo.
3. Right-click `ELAN_XX` and click "Show Package Contents", then copy your `cmulab_elan_extension-main` folder into `ELAN_XX.app/Contents/app/extensions`.


#### Windows

1. Download the latest version of ELAN from [here](https://archive.mpi.nl/tla/elan/download) and install it.
2. [Download a copy of this repo](https://github.com/zaidsheikh/cmulab_elan_extension/archive/refs/heads/main.zip) and unzip it. Copy the `cmulab_elan_extension-main/` folder into ELAN's extensions dir (`ELAN-XX/app/extensions/`).
3. Install [Python 3](https://www.python.org/downloads/) if it isn't already installed.


### Instructions

Start ELAN with the provided test audio file

`ELAN_6-1/bin/ELAN allosaurus-elan/test/allosaurus.wav &`

Switch to the "Recognizers" tab and then select "CMU Linguistic Annotation Backend" from the Recognizer dropdown list at the top and then click the "Start" button.
If this is your first time using this plugin, you will be prompted to login to the [CMULAB backend server](https://github.com/neulab/cmulab) and get an access token (you can create an account or simply login with an existing Google account).

![image](https://user-images.githubusercontent.com/2358298/160126327-75f80d58-e490-4f23-98fd-716267364ea4.png)
