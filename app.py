# -*- coding: utf-8 -*-
import os
import uuid
import calendar,time
import redis
from flask import Flask, request, url_for, send_from_directory, render_template, redirect
from werkzeug import secure_filename
#from flask_redis import FlaskRedis

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
REDIS_URL = "redis://:password@localhost:6379/0"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#redis_client = FlaskRedis(app)
r = redis.Redis(host='192.168.100.38', port=6379, db=0)

html = '''
    <!DOCTYPE html>
    <title>Upload File</title>
    <h1>file upload</h1>
    <form method=post enctype=multipart/form-data>
         <input type=file name=file>
         <input type=submit value=upload>
    </form>
    '''

print_args = '''
<form method=post>
    颜色:
    <select name="color_mode">
        <option value="color">color</option>
        <option value="black">black</option>
    </select>
    单双面:
    <select name="sides">
        <option value="one-side">one</option>
        <option value="two-sides">two</option>
    </select>
    打印份数:
    <input type="text" name="copys" value="1">
    <input type="text" name="file_url" value="http://192.168.0.111:5002/uploads/hi.doc.pdf">
    <br><br>
    <input type="submit" value="打印">
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
        color_mode = request.form.get('color_mode')
        if None != color_mode:
            return print_req()

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            pdf_file = filename + '.pdf'
            cmd = 'curl --form file=@{} http://localhost:5000/unoconv/pdf/ > {}'.format(filename, pdf_file)
            ret = os.popen(cmd).readlines()
            print('exec cmd %s|ret=%s'%(cmd, ret))
            file_url = url_for('uploaded_file', filename=pdf_file)
            #return html + '<embed src=\"{}\" type=\"application/pdf\"   height=\"800px\" width=\"100%\">'.format(file_url)
            page = html + '<embed src=\"{}\" type=\"application/pdf\"   height=\"768px\" width=\"100%\">'.format(file_url)
            page = page + print_args
            return page

    return html

#@app.route('/print_req', methods=['post'])
def print_req():
    if request.method == 'POST':
        color_mode = request.form.get('color_mode')
        if color_mode:
            sides = request.form.get('sides')
            copys = request.form.get('copys')
            file_url = request.form.get('file_url')
            
            print_args = 'color_mode:{},sides:{},copys:{}'.format(color_mode, sides, copys)
            request_id = str(uuid.uuid4())
            dev_id = 'a46fd75c-a5e0-11e9-86f1-20689d49592c'
            timestamp = calendar.timegm(time.gmtime())
            print('request_id=%s|file_url=%s|color_mode=%s|sides=%s|copys=%s'%(request_id, file_url, color_mode, sides, copys))
            #store print request info
            try:
                r.hmset(request_id, {'file_url':file_url, \
                                            'color_mode':color_mode, \
                                            'sides':sides, \
                                            'copys':copys, \
                                            'dev_id':dev_id, \
                                            'timestamp':timestamp})
            except redis.exceptions:
                print('error hmset failed!')
                pass
            # insert print request_id into redis list(print_req_list)
            try:
                r.lpush('print_req_list', request_id)
            except redis.exceptions:
                print('error hmset failed!')
                pass

            return '打印任务提交成功！'
        else:
            return '打印参数错误！'

    return '非法访问！'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
