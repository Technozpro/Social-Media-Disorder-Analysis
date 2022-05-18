# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response
#from werkzeug import secure_filename
from werkzeug.utils import secure_filename
from supportFile import *
import os
import cv2
import pandas as pd
import utils
import nltk
import moviepy.editor as mp
import speech_recognition as sr 
import sqlite3
from datetime import datetime

video = ''
name = ''

r = sr.Recognizer()

app = Flask(__name__)

app.secret_key = '1234'
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return render_template('home.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
	return render_template('home.html')

@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
	return render_template('doctor.html')

@app.route('/input', methods=['GET', 'POST'])
def input():
	error = None
	
	if request.method == 'POST':
		if request.form['sub']=='Submit':
			num = request.form['num']
			
			users = {'Name':request.form['name'],'Email':request.form['email'],'Contact':request.form['num']}
			df = pd.DataFrame(users,index=[0])
			df.to_csv('users.csv',mode='a',header=False)

			sec = {'num':num}
			df = pd.DataFrame(sec,index=[0])
			df.to_csv('secrets.csv')

			name = request.form['name']
			num = request.form['num']
			email = request.form['email']
			password = request.form['password']
			age = request.form['age']
			gender = request.form['gender']

			con = sqlite3.connect('mydatabase.db')
			cursorObj = con.cursor()
			cursorObj.execute(f"SELECT Name from Users WHERE Name='{name}' AND password = '{password}';")
		
			if(cursorObj.fetchone()):
				error = "User already Registered...!!!"
			else:
				now = datetime.now()
				dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
				con = sqlite3.connect('mydatabase.db')
				cursorObj = con.cursor()
				cursorObj.execute("CREATE TABLE IF NOT EXISTS Users (Date text,Name text,Contact text,Email text,password text,age text,gender text)")
				cursorObj.execute("INSERT INTO Users VALUES(?,?,?,?,?,?,?)",(dt_string,name,num,email,password,age,gender))
				con.commit()

				return redirect(url_for('login'))

	return render_template('input.html',error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	global video
	global name
	if request.method == 'POST':
		name = request.form['name']
		video = request.form['video']
		password = request.form['password']
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT Name from Users WHERE Name='{name}' AND password = '{password}';")

		if(video == '0'):
			video = 0
	
		if(cursorObj.fetchone()):
			return redirect(url_for('video'))
		else:
			error = "Invalid Credentials Please try again..!!!"
	return render_template('login.html',error=error)

@app.route('/video', methods=['GET', 'POST'])
def video():
	return render_template('video.html')

@app.route('/video_stream')
def video_stream():
	global video
	global name
	return Response(get_frame(video,name),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/textmining',methods=['GET', 'POST'])
def textmining():
	global video
	global name
	'''
	if request.method == 'POST':
		username = request.form["name"]
		video = request.form["video"]
		num = request.form["num"]
	'''

	clip = mp.VideoFileClip(video) 
	clip.audio.write_audiofile('converted.wav')
	audio = sr.AudioFile("converted.wav")
	with audio as source:
		audio_file = r.record(source)
	symptoms = r.recognize_google(audio_file)

	username = name

	print(username)
	print(symptoms)

	# define punctuation
	punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''

	my_str = symptoms

	# To take input from the user
	# my_str = input("Enter a string: ")

	# remove punctuation from the string
	no_punct = ""
	for char in my_str:
		if char not in punctuations:
			no_punct = no_punct + char
	
	symptoms = no_punct

	
	utils.export("data/"+username+"-symptoms.txt", symptoms, "w")
			
	data = utils.getTrainData()

	def get_words_in_tweets(tweets):	
		all_words = []
		for (words, sentiment) in tweets:
			all_words.extend(words)
		return all_words

	def get_word_features(wordlist):		
	
		wordlist = nltk.FreqDist(wordlist)
		word_features = wordlist.keys()
		return word_features

	word_features = get_word_features(get_words_in_tweets(data))		
	


	def extract_features(document):		
		document_words = set(document)
		features = {}
		for word in word_features:
			#features[word.decode("utf8")] = (word in document_words)
			features[word] = (word in document_words)
		#print(features)
		return features

	allsetlength = len(data)
	print(allsetlength)		
	#training_set = nltk.classify.apply_features(extract_features, data[:allsetlength/10*8])		
	training_set = nltk.classify.apply_features(extract_features, data)
	#test_set = data[allsetlength/10*8:]		
	test_set = data[88:]		
	classifier = nltk.NaiveBayesClassifier.train(training_set)			
	
	def classify(symptoms):
		return(classifier.classify(extract_features(symptoms.split())))
		
			
		
	f = open("data/"+ username+"-symptoms.txt", "r")	
	f = [line for line in f if line.strip() != ""]	
	tot=0
	pos=0
	neg=0
	for symptom in f:
		tot = tot + 1
		result = classify(symptom)
		now = datetime.now()
		dt_string = now.strftime("%d/%m/%Y %H:%M:%S")	
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS TextResult (Date text,Name text,Output text)")
		cursorObj.execute("INSERT INTO TextResult VALUES(?,?,?)",(dt_string,name,result))
		con.commit()
		if(result == "Depression Detected"):
			neg = neg + 1
		print(result)

	pos = tot - neg
	if(neg > pos):
		result = "Depression Detected: " + str((neg/tot)*100) + "%"
		'''
		message = client.messages \
								.create(
										body = "https://www.youtube.com/watch?v=2UtwSI7lgkQ",
										from_='+14696544981',
										to="+91"+str(num)
									)
		'''
	else:
		result = "No Depression Detected"


	return render_template('textmining.html',result=result)			    
	#return render_template('textmining.html')

@app.route('/record', methods=['GET', 'POST'])
def record():
	global name
	conn = sqlite3.connect('mydatabase.db', isolation_level=None,
						detect_types=sqlite3.PARSE_COLNAMES)
	db_df = pd.read_sql_query(f"SELECT * from Result WHERE Name='{name}';", conn)
	
	return render_template('record.html',tables=[db_df.to_html(classes='w3-table-all w3-hoverable w3-padding')], titles=db_df.columns.values)

@app.route('/text_record', methods=['GET', 'POST'])
def text_record():
	global name
	conn = sqlite3.connect('mydatabase.db', isolation_level=None,
						detect_types=sqlite3.PARSE_COLNAMES)
	db_df = pd.read_sql_query(f"SELECT * from TextResult WHERE Name='{name}';", conn)
	
	return render_template('text_record.html',tables=[db_df.to_html(classes='w3-table-all w3-hoverable w3-padding')], titles=db_df.columns.values)

@app.route('/testing',methods=['GET', 'POST'])
def testing(): 
	if request.method == 'POST':
		screen_name = str(request.form["Sreen_Name"])
		#print(username)
		count = 300	

		tweets = utils.cleanTweets(utils.getTweets(screen_name,count))
		print(tweets)		
		utils.export("data/" + "person1.txt", tweets, "w")

		
		with open(os.path.join('data/'+'person1.txt'),encoding="utf8") as fp:
			Tweets1 = fp.readlines()

		
		TotalTweets = Tweets1
		utils.export("data/"+"person.txt", TotalTweets, "w")
		'''		
		with open('Person.txt',w) as fp:
			fp.write(TotalTweets)			
		'''	
		data = utils.getTrainData()
		tot = 0		
		pos = 0	
		neg = 0	
		def get_words_in_tweets(tweets):	
			all_words = []
			for (words, sentiment) in tweets:
	  			all_words.extend(words)
			return all_words

		def get_word_features(wordlist):		
		
			wordlist = nltk.FreqDist(wordlist)
			word_features = wordlist.keys()
			return word_features

		word_features = get_word_features(get_words_in_tweets(data))
		#print(word_features)				
		


		def extract_features(document):		
			document_words = set(document)
			features = {}
			for word in word_features:
				#features[word.decode("utf8")] = (word in document_words)
				features[word] = (word in document_words)
			print(features)
			return features

		allsetlength = len(data)
		print(allsetlength)		
		#training_set = nltk.classify.apply_features(extract_features, data[:allsetlength/10*8])		
		training_set = nltk.classify.apply_features(extract_features, data[:88])
		#test_set = data[allsetlength/10*8:]		
		test_set = data[88:]		
		classifier = nltk.NaiveBayesClassifier.train(training_set)			
		
		def classify(tweet):
			return(classifier.classify(extract_features(tweet.split())))
			
				
			
		f = open("data/person.txt", "r",encoding="utf8")	
			
		#print(tot,neg,pos)
		for tweet in f:
			tot = tot + 1
			result = classify(tweet)
			if(result == 'pos'):
				pos = pos + 1		
			elif(result == 'neg'):				
				neg = neg + 1
			senti = (neg/(tot/2))*100    #divided by two because of blank lines in person.txt

			if(senti > 35):
				"""
				message = client.messages \
				.create(
					 body="Join Earth's mightiest heroes. Like Kevin Bacon.",
					 from_='+15017122661',
					 to='+15558675310'
				 )
				print(message.sid)
				"""
				print('SMS Sent')              
				
		if(tot>0):
			pos1 = pos - (tot/2)					
			tot1 = tot/2
			diff = (pos1 - neg)/tot1
		else:
			diff = 0 			    
		#pred = float(currentPrice) + (float(currentPrice)*diff)
		if(diff>=0.75):
			pred = "NO Depression"
		elif(diff>=0.50):
			pred = "Mild Depression"
		elif(diff>=0.25):
			pred = "Moderate Depression"
		else:
			pred = "Severe Depression"

		depression = (1 - diff)*100
			
		return render_template('testing.html',tot=int(tot/2),pos=int(pos-(tot/2)),neg=neg,senti=diff*100,name=screen_name,pred=pred,depression=depression)			    
	return render_template('testing.html') 

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
	# response.cache_control.no_store = True
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)
