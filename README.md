# SECUPATCH
#### Video Demo:  https://www.youtube.com/watch?v=edXzjIa_5Eo

## 📋 Overview
    Web-based compliance dashboard designed to help IT administrators, security analysts, and infrastructure teams ensure that servers in their organization meet required patching standards. Users can upload a patch manifest (YAML) and system log file (CSV), and SecuPatch automatically evaluates compliance, visualizes server patching status, and offers a downloadable compliance report.

## 🚀 Features
    - `project.py`: Main application with UI and business logic
    - `test_project.py`: Unit tests using pytest
    - `requirements.txt`: Project dependencies
    - `README.md`: Project documentation and video demo

## 🗂️ Project Structure
| File               | Description                                 |
|--------------------|---------------------------------------------|
| `project.py`        | Main application containing the Streamlit UI and business logic |
| `test_project.py`   | Unit tests for three core functions using `pytest` |
| `requirements.txt`  | List of required Python libraries |
| `README.md`         | Project documentation and video demo link |

## 🧪 Testing
This project uses `pytest` to validate core functionality. Three major functions are tested:

- `parse_log_file()`
- `evaluate_compliance()`
- `load_patch_manifest()`

## 📦 Dependencies
<b>Install project dependencies with:</b>

    pip install -r requirements.txt

<b>Dependencies include:</b>

    • streamlit,
    • pandas,
    • pyyaml,
    • plotly
