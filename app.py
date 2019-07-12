# -*- coding: utf-8 -*-
import os
from flask import Flask, request, url_for, send_from_directory
from werkzeug import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


html = '''
    <!DOCTYPE html>
    <title>Upload File</title>
    <h1>Photo Upload</h1>
    <form method=post enctype=multipart/form-data>
         <input type=file name=file>
         <input type=submit value=upload>
    </form>
    '''


def allowed_file(filename):
    return True
    #return '.' in filename and \
    #       filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            pdf_file = filename + '.pdf'
            cmd = 'curl --form file=@{} http://localhost:5000/unoconv/pdf/ > {}'.format(filename, pdf_file)
            ret = os.popen(cmd).readlines()
            print('exec cmd %s|ret=%s'%(cmd, ret))
            file_url = url_for('uploaded_file', filename=pdf_file)
            return html + '<embed src=\"{}\" type=\"application/pdf\"   height=\"800px\" width=\"100%\">'.format(file_url)
            #return html + '<br><img src=' + file_url + '>'
    return html


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
