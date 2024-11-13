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


def adjust_timestamp(line, time_shift_hours):
    """
    Adjusts the timestamp in a log line by the specified number of hours.
    """
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}) \((\d{2}:\d{2}:\d{2})\):(.*)'
    match = re.match(timestamp_pattern, line)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        rest_of_line = match.group(3)
        timestamp_str = f"{date_str} {time_str}"
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            # Adjust the timestamp
            adjusted_timestamp = timestamp + timedelta(hours=time_shift_hours)
            # Format the adjusted timestamp back to string
            adjusted_date_str = adjusted_timestamp.strftime('%Y-%m-%d')
            adjusted_time_str = adjusted_timestamp.strftime('%H:%M:%S')
            # Reconstruct the line with adjusted timestamp
            adjusted_line = f"{adjusted_date_str} ({adjusted_time_str}):{rest_of_line}"
            return adjusted_line
        except ValueError:
            # If timestamp parsing fails, return the original line
            return line
    else:
        # If the line doesn't match the timestamp pattern, return it as is
        return line


def filter_content(lines, filters, time_shift_hours):
    """
    Filter the content of the file based on the selected filters and adjust timestamps.
    Returns a list of lists, each containing the line number and the corresponding line split into columns.
    """
    filtered_lines = []
    for i, line in enumerate(lines, 1):
        line_content = line.strip()
        # Adjust the timestamp if necessary
        if time_shift_hours != 0:
            line_content = adjust_timestamp(line_content, time_shift_hours)
        # Apply filters to check if the line should be included:
        # - If `filters` is empty, include all lines (no filtering applied).
        # - If `filters` has keywords, check if any keyword is in the line (case-insensitive).
        if not filters or any(f.lower() in line_content.lower() for f in filters):
            # Split `line_content` into columns by whitespace and add line number at the beginning
            columns = [i] + line_content.split()
            filtered_lines.append(columns)
    # Return the list of filtered and processed lines, each with line number and split columns
    return filtered_lines


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """
    Handle the main route of the application.
    """
    # provides access to data sent from the client (typically from an HTML form in the webpage), so the function can respond based on user inputs.
    filters = request.form.getlist('filter')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    time_shift_str = request.form.get('time_shift', '0')

    start_date = None
    end_date = None

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Check if a new file was uploaded in a POST request (check if log file was uploaded)
    if request.method == 'POST':
        # Check if the file was uploaded and is valid  
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):  # Valid file
                filename = secure_filename(file.filename) #sanitizes the filename to remove any potentially harmful characters, ensuring it’s safe to use.
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Store the file path in the session
                session['uploaded_file'] = filename

        # Redirect to the paginated table, starting at page 1, with filters and time_shift applied
        return redirect(url_for('show_table', page=1, filter=filters, time_shift=time_shift_str))

    # If a GET request, render the initial upload page
    return render_template('index.html',
                           filtered_df=None,
                           selected_filters=filters,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           current_page=1,
                           total_pages=1,
                           time_shift='0')


@app.route('/table/<int:page>', methods=['GET', 'POST'])
def show_table(page):
    """
    Display a paginated table of filtered data from an uploaded file.
    This function processes filters and time shifts applied by the user,
    reads the file, and paginates the resulting filtered data for display.

    Parameters:
        page (int): The page number for pagination.

    Returns:
        Rendered HTML page with the filtered, paginated data table.
    """

    # Retrieve the file path from the session
    filename = session.get('uploaded_file')
    # If the file is not in the session or does not exist on disk, redirect to the upload page
    if not filename or not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return redirect(url_for('upload_file'))

    # Define the full path to the file based on the upload folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Retrieve filters and time_shift from the request, based on POST or GET method
    if request.method == 'POST':
        # For POST: Get filters and time shift values from the form data
        filters = request.form.getlist('filter')
        time_shift_str = request.form.get('time_shift', '0')
        # Redirect to the first page with the new filters and time shift
        return redirect(url_for('show_table', page=1, filter=filters, time_shift=time_shift_str))
    else:
        # For GET: Retrieve filters and time shift values from the URL query parameters
        filters = request.args.getlist('filter')
        time_shift_str = request.args.get('time_shift', '0')

    # Parse time_shift to integer; default to 0 if parsing fails
    try:
        time_shift_hours = int(time_shift_str)
    except ValueError:
        time_shift_hours = 0
        time_shift_str = '0'

    # Check if "all" is in filters and, if so, clear the filter list (no filtering)
    if "all" in filters:
        filters = []

    # Read all lines from the uploaded file
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Filter and adjust timestamps for the file's lines based on user inputs
    filtered_lines = filter_content(lines, filters, time_shift_hours)

    # If no lines remain after filtering, render the page with a "No data available" message
    if not filtered_lines:
        return render_template('index.html',
                               table=None,
                               current_page=1,
                               total_pages=1,
                               selected_filters=filters,
                               time_shift=time_shift_str,
                               start_date=None,
                               end_date=None,
                               message="No data available after applying time shift and filters.")

    # Determine the maximum number of columns needed based on the longest line
    max_columns = max(len(line) for line in filtered_lines)
    # Set column headers: 'Line Number' followed by 'Column 1', 'Column 2', etc.
    columns = ['Line Number'] + [f'Column {i}' for i in range(1, max_columns)]
    # Create a DataFrame with the filtered lines and the defined columns
    filtered_df = pd.DataFrame(filtered_lines, columns=columns)

    # Define pagination range: calculate start and end rows for the current page
    start_row = (page - 1) * PER_PAGE
    end_row = start_row + PER_PAGE
    # Select rows for the current page from the DataFrame
    page_df = filtered_df.iloc[start_row:end_row]

    # Calculate total pages based on the number of rows in the filtered DataFrame
    total_pages = (len(filtered_df) + PER_PAGE - 1) // PER_PAGE

    # Render the HTML template with the paginated table and related information
    return render_template('index.html',
                           table=page_df.to_html(classes='table', index=False, escape=False),
                           current_page=page,
                           total_pages=total_pages,
                           selected_filters=filters,
                           time_shift=time_shift_str,
                           start_date=None,
                           end_date=None)


if __name__ == '__main__':
    app.run(debug=True, port=50001)
