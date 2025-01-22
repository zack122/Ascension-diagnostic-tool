import os
import pandas as pd
from flask import Flask, request, render_template, redirect, session, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re

# Initialize the Flask application
app = Flask(__name__)

# Set the secret key for session management
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

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

def extract_date_from_line(line):
    """
    Extracts date from a log line in the format 'YYYY-MM-DD (HH:MM:SS): ...'
    Returns a datetime object representing the date, or None if no valid date is found.
    """
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}) \((\d{2}:\d{2}:\d{2})\):'
    match = re.match(timestamp_pattern, line)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        timestamp_str = f"{date_str} {time_str}"
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            return timestamp
        except ValueError:
            pass
    return None

def get_date_bounds(file_path):
    """
    Reads the 100th line to find the min date and the last line to find the max date.
    Returns (min_date, max_date) as datetime objects.
    """
    min_date = None
    max_date = None

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Get min_date from the 100th line (index 99)
    if len(lines) >= 10:
        idx = 19  # Indexing starts at 0
        while idx < len(lines):
            min_date = extract_date_from_line(lines[idx])
            if min_date:
                break
            idx += 1


    # Get max_date from the last line
    idx = len(lines) - 1
    while idx >= 0:
        max_date = extract_date_from_line(lines[idx])
        if max_date:
            break
        idx -= 1

    return min_date, max_date

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

def filter_content(lines, filters, time_shift_hours, start_date=None, end_date=None):
    """
    Filter the content of the file based on the selected filters and adjust timestamps.
    Returns a list of lists, each containing the line number and the corresponding line split into columns.
    """
    filtered_lines = []
    for i, line in enumerate(lines, 1):
        line_content = line.strip()
        
        # Skip empty lines
        if not line_content:
            continue
            
        # First check if this is a valid log line with timestamp
        timestamp = None
        timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}) \((\d{2}:\d{2}:\d{2})\):'
        match = re.match(timestamp_pattern, line_content)
        
        # Adjust timestamp if needed and validate date range
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            timestamp_str = f"{date_str} {time_str}"
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Apply time shift if specified
                if time_shift_hours != 0:
                    timestamp = timestamp + timedelta(hours=time_shift_hours)
                    line_content = adjust_timestamp(line_content, time_shift_hours)
                
                # Apply date filtering - skip if outside range
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
            except ValueError:
                # If timestamp parsing fails, treat as non-timestamp line
                pass
        
        # Apply content filters
        include_line = False
        if not filters or 'all' in filters:
            include_line = True
        else:
            for f in filters:
                if re.search(rf'\[{f}\]', line_content.lower()):
                    include_line = True
                    break
        
        if include_line:
            columns = [i] + line_content.split()
            filtered_lines.append(columns)
            
    return filtered_lines

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """
    Handle the main route of the application.
    """
    # Retrieve the file name from the session
    filename = session.get('uploaded_file')

    # Retrieve filters, time shift and date interval from the request
    filters = request.args.getlist('filter')
    time_shift_str = request.args.get('time_shift', '0')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None
    # Converts start_date_str and end_date_str into datetime objects.
    # If parsing fails (e.g., invalid format), sets the values to None.
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            start_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            end_date = None

    # Check if a new file was uploaded in a POST request
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'clear_file':
            # Clear the uploaded file from the session
            session.pop('uploaded_file', None)
            filename = None
            # check if a file is uploaded and enures its a valid name 
        elif 'file' in request.files and request.files['file'].filename != '':
            # Check if a file has been uploaded and it has a non-empty filename
            file = request.files['file']  # Get the uploaded file from the request
            if file and allowed_file(file.filename):  # Check if the file has a valid extension
                filename = secure_filename(file.filename)  # Sanitize the filename to prevent security issues
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    # If the upload folder doesn't exist, create it
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Construct the full file path
                file.save(file_path)  # Save the uploaded file to the specified path


                # Store the file name in the session
                session['uploaded_file'] = filename

                # Get the date bounds and store in session to make them accessible across multiple requests
                min_date, max_date = get_date_bounds(file_path)
                if min_date:
                    session['min_date'] = min_date.strftime('%Y-%m-%d')
                else:
                    session['min_date'] = None
                if max_date:
                    session['max_date'] = max_date.strftime('%Y-%m-%d')
                else:
                    session['max_date'] = None

        # Redirect to the table view with filters
        return redirect(url_for('show_table', page=1))

    # If a GET request, render the upload page with the uploaded file name
    min_date = session.get('min_date')
    max_date = session.get('max_date')
    #dynamic rendering of the index.html page
    return render_template('index.html',
                           uploaded_file=filename,
                           current_page=1,
                           total_pages=1,
                           selected_filters=filters,
                           time_shift=time_shift_str,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           min_date=min_date,
                           max_date=max_date)

@app.route('/table/<int:page>', methods=['GET', 'POST'])
def show_table(page):
    """
    Display a paginated table of filtered data from an uploaded file.
    """
    # Retrieve the file name from the session
    filename = session.get('uploaded_file')

    # Redirect to upload page if no file is uploaded
    if not filename or not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return redirect(url_for('upload_file'))

    # Retrieve filters and time_shift from request args
    filters = request.args.getlist('filter')
    time_shift_str = request.args.get('time_shift', '0')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Parse time_shift to integer
    try:
        time_shift_hours = int(time_shift_str)
    except ValueError:
        time_shift_hours = 0
        time_shift_str = '0'

    # Improved date parsing and validation
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(f"{start_date_str} 00:00:00", '%Y-%m-%d %H:%M:%S')
        except ValueError:
            flash('Invalid start date format', 'error')
            
    if end_date_str:
        try:
            # Set end date to end of day (23:59:59)
            end_date = datetime.strptime(f"{end_date_str} 23:59:59", '%Y-%m-%d %H:%M:%S')
        except ValueError:
            flash('Invalid end date format', 'error')
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        flash('Start date cannot be after end date', 'error')
        start_date, end_date = end_date, start_date  # Swap dates to make range valid

    # Retrieve date bounds from session
    min_date_str = session.get('min_date')
    max_date_str = session.get('max_date')
    min_date = datetime.strptime(min_date_str, '%Y-%m-%d') if min_date_str else None
    max_date = datetime.strptime(max_date_str, '%Y-%m-%d') if max_date_str else None

    # Ensure start_date and end_date are within the date bounds
    if start_date and min_date and start_date < min_date:
        start_date = min_date
    if end_date and max_date and end_date > max_date:
        end_date = max_date

    # Check if "all" is in filters
    if "all" in filters:
        filters = []

    # Read lines from the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Filter and adjust timestamps
    filtered_lines = filter_content(lines, filters, time_shift_hours, start_date, end_date)

    # Handle empty filtered lines
    if not filtered_lines:
        return render_template('index.html',
                               table=None,
                               current_page=1,
                               total_pages=1,
                               selected_filters=filters,
                               time_shift=time_shift_str,
                               message="No data available after applying time shift and filters.",
                               uploaded_file=filename,
                               min_date=min_date_str,
                               max_date=max_date_str,
                               start_date=start_date_str,
                               end_date=end_date_str)

    # Create DataFrame and paginate
    max_columns = max(len(line) for line in filtered_lines) - 2
    columns = ['Line Number', 'Date', 'Time'] + [f'Tag {i}' for i in range(1, max_columns)]
    filtered_df = pd.DataFrame(filtered_lines, columns=columns)
    start_row = (page - 1) * PER_PAGE
    end_row = start_row + PER_PAGE
    page_df = filtered_df.iloc[start_row:end_row]
    total_pages = (len(filtered_df) + PER_PAGE - 1) // PER_PAGE

    # Render the template with the table and uploaded file name
    return render_template('index.html',
                           table=page_df.to_html(classes='table', index=False, escape=False),
                           current_page=page,
                           total_pages=total_pages,
                           selected_filters=filters,
                           time_shift=time_shift_str,
                           uploaded_file=filename,
                           min_date=min_date_str,
                           max_date=max_date_str,
                           start_date=start_date_str,
                           end_date=end_date_str)

if __name__ == '__main__':
    app.run(debug=True, port=50001)