import os
from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename

# Initialize the Flask application
app = Flask(__name__)

# Set the folder to store uploaded files
app.config['UPLOAD_FOLDER'] = 'uploads'

# Define the allowed file extensions for uploads (only .txt files are allowed)
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def filter_content(lines, filters):
    """
    Filter the content of the file based on the selected filters.
    Returns a list of tuples, each containing a line number and the corresponding line.
    """
    filtered_lines = []  # Initialize an empty list to store the filtered lines
    for i, line in enumerate(lines, 1):  # Enumerate the lines with line numbers starting from 1
        # Check if the line matches any of the selected filters
        if ('system' in filters and '[System]' in line) or \
           ('data' in filters and '[Data]' in line) or \
           ('debug' in filters and '[Debug]' in line) or \
           ('notification' in filters and '[Notification]' in line) or \
           ('all' in filters):  # If 'all' is selected, include all lines
            filtered_lines.append((i, line))  # Append the line number and line content to the list
    return filtered_lines  # Return the filtered lines

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handle the main route of the application. If the request method is POST, process the uploaded file.
    If the method is GET, render the template without any filtered content.
    """
    if request.method == 'POST':  # Check if the request is a POST (form submission)
        if 'file' not in request.files:  # Check if a file was not uploaded
            return redirect(request.url)  # Redirect to the same URL (reload the page)
        file = request.files['file']  # Get the uploaded file
        if file.filename == '':  # Check if the file has no name (i.e., no file was selected)
            return redirect(request.url)  # Redirect to the same URL (reload the page)
        if file and allowed_file(file.filename):  # Check if the file exists and has an allowed extension
            filename = secure_filename(file.filename)  # Secure the filename to prevent security issues
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save the uploaded file
            
            filters = request.form.getlist('filter')  # Get the selected filters from the form
            
            # Read and filter the file content
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
                lines = f.readlines()  # Read all lines from the file
            
            filtered_lines = filter_content(lines, filters)  # Filter the lines based on the selected filters
            
            # Render the template with the filtered content
            return render_template('index.html', filename=filename, filtered_lines=filtered_lines)
    
    # If the request is GET or if no file was uploaded, render the template without any filtered content
    return render_template('index.html', filename=None, filtered_lines=None)


if __name__ == '__main__':
    app.run(debug=True)
