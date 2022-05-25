### Run phone transcription

The CMULAB server uses the Allosaurus pretrained universal phone recognizer to generate the phone transcriptions. Please select "run-phone-transcription" option from the settings dropdown list. If you have an existing tier with audio segmentation information, please choose that as the input tier in the Parameters section otherwise the phone recognizer will treat the entire audio file as one segment. Once you click the start button, you will be asked to specify the Allosaurus model and language ID to use. The ELAN plugin by default uses the "eng2102" model (lang code "eng"). This model is fine-tuned for English, so for other languages it might be better to use the language-independent model "uni2005". With the "uni2005" model, you can either opt to use lang code "ipa" which tells the recognizer to use the entire IPA inventory (around 230 phones) or you can specify the ISO lang code for a specific language. Specifying a particular lang code rather than just "ipa" can improve the recognition accuracy. In total, 2185 languages are supported. You can find the full list here:
http://rabat.sp.cs.cmu.edu:8088/annotator/get_allosaurus_models/
Instead of entering a lang code, you can also specify path to a file containing a list of phones to restrict the phone output. Note that the list of phones should be a subset of the full phone inventory supported by the model (see link above).


#### Train phone transcription

You can fine-tune the available Allosaurus pretrained models by choosing the "train-phone-transcription" option in settings. To do that you will need to upload phone transcriptions provided/corrected by annotators in EAF file format. For example, you can correct/make changes to the phone transcriptions obtained from Allosaurus (see previous section) and save them to an EAF file. When you click the "Start" button, you will be asked to select these EAF files, as well as specify some other parameters such as pretrained model ID (that you would like to fine-tune), language code, number of training epochs, tier name containing the phone transcriptions in the EAF files, and annotator name (if specified in the EAF files). Once the training starts, you will be able to check it's status and view a list of other fine-tuned Allosaurus models here:
http://rabat.sp.cs.cmu.edu:8088/annotator/upload/#models
Once a fine-tuned model is ready, you can try using it's model ID to run phone transcription as described in the previous section.


### Run speaker diarization

To run speaker diarization, please add a new tier and annotate a few segments of the audio with speaker names. The diarization model will use these samples of each speaker to detect speakers and annotate the rest of the audio file. In the "Parameters" section, please select this tier as the "Input tier to process". After clicking "Start", you can experiment with the threshold parameter to see what gives the best output (the default value should work in most cases). The CMULAB server uses the Resemblyzer model for diarization.





