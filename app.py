import os
from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def filter_content(lines, filters):
    filtered_lines = []
    for i, line in enumerate(lines, 1):  # Enumerate with line numbers starting from 1
        if ('system' in filters and '[System]' in line) or \
           ('data' in filters and '[Data]' in line) or \
           ('debug' in filters and '[Debug]' in line) or \
           ('notification' in filters and '[Notification]' in line) or \
           ('all' in filters):
            filtered_lines.append((i, line))
    return filtered_lines

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            filters = request.form.getlist('filter')
            
            # Read and filter the file content
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
                lines = f.readlines()
            
            filtered_lines = filter_content(lines, filters)
            
            return render_template('index.html', filename=filename, filtered_lines=filtered_lines)
    
    return render_template('index.html', filename=None, filtered_lines=None)

if __name__ == '__main__':
    app.run(debug=True)
