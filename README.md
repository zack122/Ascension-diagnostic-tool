# Ascension Diagnostic Tool for Log Files

The Ascension Diagnostic Tool is a Python Flask web application developed for Ocean Diagnostics. It allows users to upload, filter, and analyze Ascension log files through a user-friendly web interface. The tool provides features such as keyword filtering, timestamp adjustment, and paginated display of log entries.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Application Structure](#application-structure)
- [License](#license)
- [Contact](#contact)

## Features

- **File Upload**: Upload log files in `.txt` format up to 10 GB in size.
- **Keyword Filtering**: Filter log entries based on predefined keywords:
  - `system`
  - `data`
  - `debug`
  - `notification`
  - `warning`
  - `error`
  - `kernel`
  - `tx`
  - `rx`
- **Timestamp Adjustment**: Shift log entry timestamps by a specified number of hours.
- **Date Range Filtering**: (Placeholder in code) Filter log entries within a specific date range.
- **Paginated Display**: View filtered log entries in a paginated table, 1,000 entries per page.
- **Column Management**: Hide and restore table columns interactively.

## Prerequisites

- **Python 3.6 or higher**
- **Pip** package installer
- **Virtual Environment** (recommended)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ocean-diagnostics/ascension-diagnostic-tool.git
   cd ascension-diagnostic-tool
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

   **Note**: If `requirements.txt` is not provided, install the following packages:

   ```bash
   pip install flask pandas werkzeug
   ```

## Usage

1. **Run the Application**

   ```bash
   python app.py
   ```

   The application will start on `http://localhost:50001` by default.

2. **Access the Web Interface**

   Open your web browser and navigate to `http://localhost:50000`.

3. **Upload a Log File**

   - Click on the file input field and select a `.txt` log file to upload.

4. **Apply Filters**

   - **Choose Filters**: Select one or more keywords to filter the log entries.
   - **Time Shift**: Enter the number of hours to adjust the timestamps.
   - **Date Range**: (Feature placeholder) Specify the start and end dates to filter entries.
   - Click on **Apply Filters** to process the log file.

5. **Navigate Through Log Entries**

   - Use the pagination controls to navigate between pages.
   - Click on table headers to hide/show columns.
   - Restore hidden columns using the buttons provided.

## Application Structure

- **`app.py`**: The main Flask application script containing routes and logic.
- **`templates/index.html`**: HTML template for rendering the web interface.
- **`static/style.css`**: CSS file for styling the web interface.
- **`uploads/`**: Directory where uploaded log files are stored.


## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions or support, please contact:

- **Ocean Diagnostics Support**
- **Email**: support@oceandiagnostics.com
- **Website**: [www.oceandiagnostics.com](http://www.oceandiagnostics.com)

---

*This README was generated for the Ascension Diagnostic Tool to assist users in understanding and utilizing the application's features effectively.*
