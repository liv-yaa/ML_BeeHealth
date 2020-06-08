## Project title
"The Bee Machine" 

## Motivation
Our future as a planet depends on preserving our honeybee populations, which are intricately intertwined with the food and agricultural systems we have relied on for millenia. Preserving niche species and promoting biodiversity will be a challenge in the coming years, but with more research by honeybee immunologists and population studies, we can start to gather better metrics about honeybee health. Tracking honeybee populations is a substiantial task, and meanwhile, an array of different forces are causing colonies' health to dwindle. 

The Bee Machine is a tool that can help researchers by "crowd sourcing" health data about honeybee populations from around the world. A user anywhere can submit a photo of a bee and tag its location. Once the image is processed by the Bee Machine's machine learning model, a prediction of that honeybee's health will be returned. If the prediction is not accurate, the model will learn from its mistakes as well as its successes. Over time, statistics show that the model will return fewer false positive and false negative predictions and more true positive and true negative predictions. This way, any user who wants to contribute to our database can help track honeybee health trends.

## Tech and frameworks used:

- Python
- Flask
- Jinja
- CSS
- HTML
- SQLAlchemy
- PostgreSQL Database
- Bootstrap 
- Delployed & 1.1E+4 image database hosted on AWS

## How to use?
Upload a photo. Specify "healthy" for healthy bees. All other enties will be tagged "unhealthy".

The computer vision algorithm will use your submission to become better at bee health classifications.

## Contribute
You can contribute to The Bee Machine by uploading a bee photo. The more photos are submitted, the more powerful the health sorting algorithm will become. General guidelines for photo submissions would be to make sure the image is quality and it is a bee. Otherwise, the model should screen for any non-bee images too.

## Credits
<b>Built with</b>
- [Clarifai API] (https://clarifai.com/)
- [Kaggle: The Annotated HoneyBee Image Database] @jenny18 (https://www.kaggle.com/jenny18/honey-bee-annotated-images/kernels)

<b>Sage Advice</b>
- [Honey bee health detection with CNN] @dmitrypukhov (https://www.kaggle.com/dmitrypukhov/honey-bee-health-detection-with-cnn)
- [R2D3ML] @r2d3 (http://www.r2d3.us/visual-intro-to-machine-learning-part-1/)
- [Ratings Lab] @HackbrightAcademy (https://github.com/hackbrightacademy)
- @atrnh
- @J-A-Gray
- @vwxy

## Features Still In Progress
- Instead of form switch to a radio button
- Deployment on AWS - [Done 3/20]
- image preprocessing w/ scikitlearn
- (D3?) Map of geotagged images
- UX/aesthetic changes
- Export dataset to Kaggle

<br><br>
<i> dm me? https://www.linkedin.com/in/livsmith/ </i>
