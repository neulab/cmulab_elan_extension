### Run phone transcription

The CMULAB server uses the Allosaurus pretrained universal phone recognizer to generate the phone transcriptions. Please select "run-phone-transcription" option from the settings dropdown list. If you have an existing tier with audio segmentation information, please choose that as the input tier in the Parameters section otherwise the phone recognizer will treat the entire audio file as one segment. Once you click the start button, you will be asked to specify the Allosaurus model and language ID to use. You can find a list of available models and languages here: https://github.com/xinjli/allosaurus


#### Train phone transcription

You can fine-tune the available Allosaurus pretrained models by choosing the "train-phone-transcription" option in settings. To do that you will need to upload phone transcriptions provided/corrected by annotators in EAF file format. When you click the "Start" button, you will be asked to select these EAF files, as well as specify some other parameters such as pretrained model ID (that you would like to fine-tune), language code, number of training epochs, tier name containing the phone transcriptions in the EAF files, and annotator name (if specified in the EAF files). Once the training starts, you will be able to check it's status and view a list of other fine-tuned Allosaurus models here: http://rabat.sp.cs.cmu.edu:8088/annotator/upload/#models
Once a fine-tuned model is ready, you can try using it's model ID to run phone transcription as described in the previous section.


### Run speaker diarization

To run speaker diarization, please add a new tier and annotate a few segments of the audio with speaker names. The diarization model will use these samples of each speaker to detect speakers and annotate the rest of the audio file. After clicking "Start", you can experiment with the threshold parameter to see what gives the best output (the default value should work in most cases). The CMULAB server uses the Resemblyzer model for diarization.





