# -*- coding: utf-8 -*-
import os
import uuid
import calendar,time
import redis
import socket
from flask import Flask, request, url_for, send_from_directory, render_template, redirect
from werkzeug import secure_filename
#from pip._internal.download import is_file_url
#from flask_redis import FlaskRedis

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
REDIS_URL = "redis://:password@localhost:6379/0"
download_url = ''
listening_port = 5002

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#redis_client = FlaskRedis(app)
#r = redis.Redis(host='192.168.100.38', port=6379, db=0)
r = redis.Redis(host='localhost', port=6379, db=0)


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
        <option value="color">彩色</option>
        <option value="black">黑白</option>
    </select>
    &nbsp;&nbsp;单双面:
    <select name="sides">
        <option value="one">单面</option>
        <option value="two-sided-long-edge">双面长边</option>
        <option value="two-sided-short-edgee">双面短边</option>
        
    </select>
    &nbsp;&nbsp;打印份数:
    <input type="text" name="copys" value="1">
    <input type="text" id="file_url" name="file_url" value="" style="display:none">
    <br><br>
    <input type="submit" value="打印">
</form>
<script>
function set_file_url(){
var embed=document.getElementById("embed_pdf");
var file_name = embed.getAttribute("src");
var file_url = document.getElementById("file_url");
file_url.value= file_name;
}
set_file_url();
</script>
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
            page = html + '<embed id=\"embed_pdf\" src=\"{}\" type=\"application/pdf\"   height=\"768px\" width=\"100%\">'.format(file_url)
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
            file = request.form.get('file_url')
            download_url = 'http://{}:{}{}'.format(get_host_ip(), listening_port, file)
            file_url = download_url
            
            print_args = 'color_mode={},sides={},copys={}'.format(color_mode, sides, copys)
            request_id = str(uuid.uuid4())
            dev_id = '9f3a3d62-a60e-11e9-86f1-20689d49592c'
            timestamp = calendar.timegm(time.gmtime())
            print('request_id=%s|dev_id=%s|print_args=%s'%(request_id, dev_id, print_args))
            #store print request info
            try:
                r.hmset(request_id, {'file_url':file_url, \
                                            'print_args':print_args, \
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

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=listening_port)
