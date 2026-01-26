1. Pre-Annotation Processing  
2. Setting up Species and Project  
3. Uploading Calls (with or without Segments)  
4. From Upload to Task Batch  
5. Annotating Calls  
6. Exporting Data

## 1\. Pre-Annotation Processing

Before uploading any calls, it is wise to filter out as much noise as possible. To do this, first, you can filter for noise files. I do so using SonoBat’s Noise Scrubbing option. Once noise files have been deleted, I also like to set up a high-pass filter to reduce noise from influencing the automatic segmenter. High-pass filters will depend on the species. Keep in mind that many social calls are lower than the recommended filters for echolocation calls of that species, so it is wise to look at a couple of your social calls and make decisions on your data.

If your lab already has a way to segment calls, or calls that have been segmented in the past, those segments can be added in Battycoda. We have used SASLab to automatically segment calls. 

BattyCoda works best with short audio files, so it is recommended to split files if they are more than a minute long. 

## 2\. Setting up Species and Project 

Members with admin access for their organization will be able to add new species. For each species, there needs to be a .jpeg for the repertoire and a list of the call types. These can be inputted manually or from a text file. Noise and Unknown should be added as call types for ease of annotation. 

![][image1]

## 3\. Uploading Calls

Calls can be uploaded with or without pre-segmentation. Before you upload any files, make sure to note what group and project your files will be in. Groups are important because the people with access to your files will be based on groups. I like to have all of my files that undergrads will annotate in one group, and my test files in another group. I like to base the projects on an experiment block, so I have different projects for different years of field recordings of one experiment. How you differentiate projects is up to you, so keep in mind that the filtering of tasks is based on the project.

	**For segmented calls**

In order to add known segments to BattyCoda, you need an Excel or CSV file with the start time and end times of the segments. You can then use the ImprovedBatPickle.py file found in the github to make associated pickle files for Excel files. There is also a [picklecheck.py](http://picklecheck.py) script to ensure that the pickle files have the correct information to be uploaded to BattyCoda. This pickle file stores the onset and offset information of the segments. Once the .wav.pickle files are in your folder, you can use the api code to upload them in conjunction with your .wav files, using \[this\] code. You can upload single files with segments in BattyCoda with the New Recording button, then go to the recording and click “upload pickle file”. You can use the batch processing button for some files, \~ 50, where it will ask you for an upload of zip files of the folder of .wav files and folder of pickle files. If you are uploading many files at once, you want to use the API implementation. Example code for single file upload for testing can be found \[here\] and batch uploading \[here\]. 

**For unsegmented calls**

You can upload single files in BattyCoda with the New Recording button. You can use the batch processing button for some files, \~ 50\. If you are uploading many files at once, you want to use the API implementation. Example code for single file upload for testing can be found \[here\] and batch uploading \[here\]. 

## 4\. From Upload to Task Batch

Next, you need to get the calls through to the Task Batch stage. The tabs at the top are essentially the steps you will take

![][image2]

Once you have files uploaded, you will segment them. Move on to classification if you uploaded segmented files. You can click into a recording and press “Auto Segment,” and you will see this screen

![][image3]

I would recommend the minimum duration to be the length of the shortest call of your species, likely the echolocation call. Still testing the other options.

For classification, you can “new classification run” for one file or “Classify Unclassified Segments” for those that have not been classified. You will then be prompted to choose your classifier. 

![][image4]

For species without a functional classifier, choose dummy classification. Testing is done for species with classifiers to determine which mathematical model yields the most accurate results.  
Once the files are classified, on the classifier tab, you can choose the “create task batches” button. You will be prompted to choose which species you will create task batches for. 

![][image5]

You will be prompted to choose a confidence threshold, which would exclude high-confidence calls from manual inspection. Only do this if your species has a working classifier and you wish to exclude calls based on this threshold.

You now have task batches ready to be annotated\! All of these tasks can also be completed using the API, which is more relevant if you have many hundreds of files that tend to cause errors in browsers.

## 5\. Annotating Calls

Below is the interface you will see once you have chosen your file in BattyCoda. In the middle, we see the spectrogram of the call being annotated. The detailed view shows the spectrogram zoomed in to one specific call, which is the call you are labeling. The call you are labelling is the one right after the 0 seconds label. The overview is a zoomed-out version of the same call, to better understand the context of the call. 

![][image6]

Under the spectrogram, we have some other options. The channel observed is regarding multiple microphones in each recording. Even if you only uploaded one wav per recording, this option will persist. There is also the play audio bar. You can press play to hear a pitched-down segment of the call. This is most important for differentiating bat calls from noise.

To the left of the spectrogram is the repertoire image and information on the recording. This is a very helpful guide, but vocalizations are variable across individuals and contexts. Most annotators will want this image open in another tab while they work. Here we can also see the species, what recording this is, the segment, and the duration of the call in parentheses. Often, calls will be similar in shape but different in duration, so this is important to note. We also see the task batch and project here, and have the last task and skip task buttons.

To the right of the spectrogram, we see the list of calls to label. The call that the classifier believes to be the correct label will be at the top. Once you mark a call, you can click mark as done or next task to classify the call and move to the next call.

## 6\. Exporting Data

Once you have calls labelled, you can start exporting them. Go to your task batch page, filter for the specific project you want, then click “Download Completed Batches.” This will give you a zip file of the export Excel files for each file. Once is pictured below. 

![][image7]

The “Label” is the annotation made by hand, and “Classification” is the annotation made by the classifier. When using a dummy classifier, it is blank.

One can also export the parameters from files segmented on BattyCoda. On the classification tab, you can export the parameters used for classification.

![][image8]

This is where you would do that if it were working. That Excel file looks like this.

![][image9]

With these two outputs (or the parameter files from pre-BattyCoda Segmentation), you can do analysis once you combine the Labels with the Parameters, and an example of that in code can be seen \[here\].

## FAQ

Q: I hit an error, help\!

A: Please submit an issue report on the github [\[here\]](https://github.com/angiesalles/battycoda/issues) if you encounter any type of error, we will work on resolving those as soon as possible. 

Q: But my species doesn't have a known repertoire?

A: Congratulations, you get the fun job of naming all of the calls. Currently, we are constructing repertoires by hand. The clustering tab is there to hopefully be able to create these clusters and hence labels, but it is still under construction. When deciding the repertoires, it is not necessary to find every single call, you can add a “new call” call type for your species to put calls you would consider not described, and update the repertoire accordingly.

[image1]: docs/images/image1.png

[image2]: docs/images/image2.png

[image3]: docs/images/image3.png

[image4]: docs/images/image4.png

[image5]: docs/images/image5.png

[image6]: docs/images/image6.png

[image7]: docs/images/image7.png

[image8]: docs/images/image8.png

[image9]: docs/images/image9.png
