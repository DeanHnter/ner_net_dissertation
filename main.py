from flask import Flask, render_template, send_from_directory, url_for,  flash, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from final_func import *
import docx
from pdfminer.high_level import extract_text
import os
import nltk


app = Flask (__name__)


UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
DOWNLOAD_FOLDER = "download/" 
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER 

#session.clear()
app.secret_key = 'dd hh'

@app.route("/", methods= ["GET","POST"])
def index():
    return render_template("index.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/questionnaire")
def questionnaire():
    return render_template("questionnaire.html")


#Options to read the files in the websites. DOC or TXT or PDF. file_name== name+path

def input_file(file_name):
  split_tup = os.path.splitext(file_name)
  if split_tup[1] == ".doc" or split_tup[1]== ".docx" or split_tup[1] == "docm":
    doc = docx.Document(file_name)
    result = [p.text for p in doc.paragraphs if len(p.text)>0 and p.text.isspace() == False]
  elif split_tup[1] == ".txt":
    with open(file_name, "r") as f:
      result= f.readlines()
  elif split_tup[1] == ".pdf":
    text = extract_text(file_name)
    result= [sent for sent in text.split("\n") if len(sent)>0 and sent.isspace()== False]
  return result

#write the file for later downloading
def download(list_nes):
    with open(os.path.join(app.config['DOWNLOAD_FOLDER'], 'nes_list.tsv'),'w', encoding='UTF8') as f:
        for t in list_nes:
            f.write(t[0]+"\t"+t[1] +"\t"+t[2]+ "\n")

#Upload file

@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        if 'file' not in request.files:
            flash("You must select one document")
            return redirect(url_for("index"))

        if f.filename == '':
            flash("You must select one document")
            return redirect(url_for("index"))
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))	
        session["a"]=os.path.join(app.config['UPLOAD_FOLDER'], filename)	
        flash('File successfully uploaded')
        text= input_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        session["b"]= text
        list_nes_final, n_nes, time_final= run_experiment(text)
        session["d"] = list_nes_final
        file_write= download(list_nes_final)
        print(n_nes)
        print(time_final)
        print(list_nes_final)
        return render_template('index.html', filename=filename, text= text, list_final=list_nes_final, num_nes= n_nes, tiempo= time_final)
        #return render_template("index.html", filename=filename, text= text)



#Read from text area
#this should be finish and called as soon as submit is clicked, maybe it wont have the loading gift :C
@app.route("/uploadtext", methods= ["POST", "GET"])
def uploadtext():
    try:
        text= request.form["texti"]
        #text= request.args['text']
        text= [sent for sent in text.split(".") if len(sent)>0 and sent.isspace()== False]
        print("first saved", text)
        session["c"] = text
        print("second session", session.get("c", None))
        list_nes_final, n_nes, time_final= run_experiment(text)
        session["d"] = list_nes_final
        print("After experiment")
        file_write= download(list_nes_final)
        print(n_nes)
        print(time_final)
        print(list_nes_final)
        return render_template("index.html", text= text, list_final=list_nes_final, num_nes= n_nes, tiempo= time_final)
    except:
        flash("You must enter text or select a document. ")
        return redirect(url_for("index"))



#session["a"] == Filename
#session["b"] == text from file
#session["c"] == text from textfield
#session["d"] == list of nes and translation

#background onclick calling of the final function

@app.route('/finalfunc_f', methods = ["POST", "GET"])    
def finalfunc_f():
    text= session.get("b",None)
    print(text)
    #count=0
    #for i in range(20):
    #    count+=1
    #    print(count)
    #    sleep(2)
    list_nes_final, n_nes, time_final= run_experiment(text)
    session["d"] = list_nes_final
    return render_template('index.html', list_final=list_nes_final, num_nes= n_nes, tiempo= time_final)
    #return render_template("index.html", count= count)  #text= text, list_final= list_nes_final, n_nes= n_nes

@app.route('/finalfunc_t', methods = ["POST", "GET"])
def finalfunc_t():
    text= session.get("c",None)
    print(text)
    #count=0
    #for i in range(20):
    #    count+=1
    #    print(count)
    #    sleep(2)
    list_nes_final, n_nes, time_final= run_experiment(text)
    session["d"] = list_nes_final
    return render_template('index.html', list_final=list_nes_final, num_nes= n_nes, tiempo= time_final)
    #session.clear()
    
    #return render_template("index.html", text= text )#list_final= list_nes_final, n_nes= n_nes)


@app.route("/download", methods= ["POST","GET"])
def downloader():
    try:
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'nes_list.tsv', as_attachment=True)
    except:
        return "File path error or file does not exist"

@app.route("/bye")
def bye():
    print("bye")
    dir= app.config['UPLOAD_FOLDER']
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
    return "Deleted all"


if __name__== "__main__":
    app.run(debug=True)