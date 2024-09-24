import os
import pandas as pd
from flask import Flask, request, render_template, redirect, session
from werkzeug.utils import secure_filename
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# Set the secret key for session management
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Set the maximum file size for uploads to 10 GB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

# Set the folder to store uploaded files
app.config['UPLOAD_FOLDER'] = 'uploads'

# Define the allowed file extensions for uploads (only .txt files are allowed)
app.config['ALLOWED_EXTENSIONS'] = {'txt'}


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def filter_content(lines, filters):
    """
    Filter the content of the file based on the selected filters.
    Returns a list of tuples, each containing a line number and the corresponding line.
    """
    filtered_lines = []  # Initialize an empty list to store the filtered lines
    for i, line in enumerate(lines, 1):  # Enumerate the lines with line numbers starting from 1
        # Check if the line matches any of the selected filters
        if any(f in line.lower() for f in filters):
            filtered_lines.append((i, line.strip()))  # Append the line number and line content to the list
    return filtered_lines  # Return the filtered lines


def extract_date_from_line(line):
    try:
        date_str = line.split(' ')[0]
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (IndexError, ValueError):
        return None  # Return None if the date cannot be extracted


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """
    Handle the main route of the application. If the request method is POST, process the uploaded file.
    If the method is GET, render the template without any filtered content.
    """
    filters = request.form.getlist('filter')  # Retrieve the selected filters
    start_date_str = request.form.get('start_date')  # Retrieve the start date
    end_date_str = request.form.get('end_date')  # Retrieve the end date

    start_date = None
    end_date = None

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    if request.method == 'POST':
        # Check if a new file was uploaded
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):  # Valid file
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Store the filename in the session
                session['uploaded_file'] = filename

        # Retrieve the uploaded file from the session
        filename = session.get('uploaded_file')
        if not filename:
            return redirect(request.url)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Filter content without fully loading the file into memory
        filtered_lines = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f, 1):  # Process each line in the file
                log_date = extract_date_from_line(line)

                if start_date and log_date and log_date < start_date:
                    continue
                if end_date and log_date and log_date > end_date:
                    continue

                # Apply filters
                if any(f in line.lower() for f in filters):
                    filtered_lines.append((i, line.strip()))

        # Convert filtered lines to DataFrame
        filtered_df = pd.DataFrame(filtered_lines, columns=['Line Number', 'Line Content'])

        # Render the template with the filtered DataFrame
        return render_template('index.html', filtered_df=filtered_df.to_html(classes='table'), selected_filters=filters, start_date=start_date_str, end_date=end_date_str)

    # Handle GET request or no file uploaded yet
    return render_template('index.html', filtered_df=None, selected_filters=[], start_date=start_date_str, end_date=end_date_str)


if __name__ == '__main__':
    app.run(debug=True)
