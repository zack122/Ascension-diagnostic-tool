import os
import pandas as pd
from flask import Flask, request, render_template, redirect, session, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re



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

PER_PAGE = 1000  # Set the number of rows per page


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

    # Check if a new file was uploaded in a POST request
    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):  # Valid file
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Store the file path in the session instead of the DataFrame
                session['uploaded_file'] = filename

        # Redirect to the paginated table, starting at page 1, with filters applied
        return redirect(url_for('show_table', page=1, filter=filters))

    # If a GET request, render the initial upload page
    return render_template('index.html',
                           filtered_df=None,
                           selected_filters=filters,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           current_page=1,  # Default value
                           total_pages=1)  # Default value




@app.route('/table/<int:page>', methods=['GET', 'POST'])
def show_table(page):
    """
    Paginate the filtered DataFrame and show the corresponding rows.
    """
    # Retrieve the file path from the session
    filename = session.get('uploaded_file')
    if not filename or not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return redirect(url_for('upload_file'))  # Redirect if file not found

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Get the filters from the form submission if POST, else from query parameters (URL)
    if request.method == 'POST':
        filters = request.form.getlist('filter')
        # Redirect to the first page with the selected filters
        return redirect(url_for('show_table', page=1, filter=filters))
    else:
        filters = request.args.getlist('filter')

    # Handle the case when no filters are selected
    if not filters:
        filters = []  # Do not apply any filters if nothing is selected

    filtered_lines = []
    with open(file_path, 'r') as f:
        for i, line in enumerate(f, 1):  # Process each line in the file
            if not filters or any(f in line.lower() for f in filters):  # Apply filters or show all lines if no filters
                filtered_lines.append([i] + line.strip().split())

    # Handle empty filtered_lines
    if not filtered_lines:
        return render_template('index.html',
                               filtered_df="No data available",
                               current_page=page,
                               total_pages=1,
                               selected_filters=filters)

    # Determine the number of columns needed based on the longest line
    max_columns = max(len(line) for line in filtered_lines) if filtered_lines else 1

    # Continue with the rest of the logic to create the DataFrame and paginate
    columns = ['Line Number'] + [f'Column {i}' for i in range(1, max_columns)]
    filtered_df = pd.DataFrame(filtered_lines, columns=columns)

    # Pagination logic
    start_row = (page - 1) * PER_PAGE
    end_row = start_row + PER_PAGE
    page_df = filtered_df.iloc[start_row:end_row]

    # Calculate total pages
    total_pages = (len(filtered_df) // PER_PAGE) + (1 if len(filtered_df) % PER_PAGE > 0 else 0)

    # Render paginated table and include filters in the URL
    return render_template('index.html',
                           table=page_df.to_html(classes='table'),
                           current_page=page,
                           total_pages=total_pages,
                           selected_filters=filters,
                           start_date=None,
                           end_date=None)  # Start date and end date are None for now




if __name__ == '__main__':
    app.run(debug=True, port=50001)
