# adds image processing capabilities
from PIL import Image 
import cv2
import time
from keras.preprocessing import image
import numpy as np
import os
from twilio.rest import Client
import pandas as pd
import sqlite3
from datetime import datetime


# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = "AC34edde99be4693e7d5337d1fbd8e0f85"
auth_token = "b7a86c958f951a8b394c74f1f192d326"
client = Client(account_sid, auth_token)

count = 0
#--------------------------------Sentiment Analysis Part-----------------------------------------
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

#cap = cv2.VideoCapture(0)
#-----------------------------
#face expression recognizer initialization
from keras.models import model_from_json
model = model_from_json(open("facial_expression_model_structure.json", "r").read())
model.load_weights('facial_expression_model_weights.h5') #load weights
#model._make_predict_function()

emotions = ('angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral')

def get_frame(video,name):
	global count
	df = pd.read_csv('secrets.csv')
	sec = df.to_dict('list')
	num = sec['num'][0]

	camera_port=video
	camera=cv2.VideoCapture(camera_port) #this makes a web cam object
	time.sleep(2)

	while True:
		ret, img = camera.read()
		print(img.shape)
		
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		
		faces = face_cascade.detectMultiScale(gray, 1.3, 5)

		#print(faces) #locations of detected faces
		
		for (x,y,w,h) in faces:
			
			cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2) #draw rectangle to main image
			
			detected_face = img[int(y):int(y+h), int(x):int(x+w)] #crop detected face
			
			detected_face = cv2.cvtColor(detected_face, cv2.COLOR_BGR2GRAY) #transform to gray scale
			detected_face = cv2.resize(detected_face, (48, 48)) #resize to 48x48
			
			img_pixels = image.img_to_array(detected_face)
			img_pixels = np.expand_dims(img_pixels, axis = 0)
			
			img_pixels /= 255 #pixels are in scale of [0, 255]. normalize all pixels in scale of [0, 1]
			
			predictions = model.predict(img_pixels) #store probabilities of 7 expressions
			
			#find max indexed array 0: angry, 1:disgust, 2:fear, 3:happy, 4:sad, 5:surprise, 6:neutral
			max_index = np.argmax(predictions[0])
			
			emotion = emotions[max_index]

			if(emotion == 'sad' or emotion=='fear'):
					count = count+1
					print(count)
			else:
				count = 0
			
			if(count > 15):
				#write emotion text above rectangle
				count = 0
				now = datetime.now()
				dt_string = now.strftime("%d/%m/%Y %H:%M:%S")	
				con = sqlite3.connect('mydatabase.db')
				cursorObj = con.cursor()
				cursorObj.execute("CREATE TABLE IF NOT EXISTS Result (Date text,Name text,Output text)")
				cursorObj.execute("INSERT INTO Result VALUES(?,?,?)",(dt_string,name,"Depression Detected"))
				con.commit()
				cv2.putText(img, " Depression Detected", (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
			
				message = client.messages \
				.create(
					 body = "https://www.youtube.com/watch?v=2UtwSI7lgkQ",
					 from_='+18024713448',
					 to="+919175884383"
				 )

				
			else:
				cv2.putText(img, emotion + ":" + str(predictions[0][max_index]), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

		imgencode=cv2.imencode('.jpg',img)[1]
		stringData=imgencode.tostring()
		yield (b'--frame\r\n'
			b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')

	del(camera)

