import tkinter as tk
from tkinter import filedialog, messagebox, Label, Button
import os
import zipfile
from xml.etree import ElementTree as ET
from flask import Flask, request, jsonify
import traceback


app = Flask(__name__)


def correct_xml(xml_path):
    # Parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Iterate over all elements and find 'MissingDependencies' to replace
    for missing_deps in root.findall('.//MissingDependencies'):
        # Remove all children and attributes if any
        for child in list(missing_deps):
            missing_deps.remove(child)
        missing_deps.attrib.clear()
        missing_deps.text = None

    # Write the corrected XML back to the file
    tree.write(xml_path)


def process_zip_file(zip_file_path, directory):
    # Correct the filename by removing all apostrophes
    corrected_filename = zip_file_path.replace("'", "")
    if corrected_filename != zip_file_path:
        os.rename(zip_file_path, corrected_filename)
        zip_file_path = corrected_filename

    temp_extracted_dir = os.path.join(directory, 'temp_extracted')

    # Extract the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extracted_dir)

    solution_xml_path = os.path.join(temp_extracted_dir, 'solution.xml')

    if os.path.exists(solution_xml_path):
        correct_xml(solution_xml_path)

    # Zip the contents back
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_extracted_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_extracted_dir)
                zipf.write(file_path, arcname)

    # Cleanup
    for root, dirs, files in os.walk(temp_extracted_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(temp_extracted_dir)


def process_zip_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".zip") or filename.endswith(".zip'"):
            zip_file_path = os.path.join(directory, filename)
            process_zip_file(zip_file_path, directory)


def gui():
    def select_directory():
        directory_path = filedialog.askdirectory()
        if directory_path:
            try:
                process_zip_files(directory_path)
                messagebox.showinfo("Complete", "Process completed successfully!")
                status_label.config(text="Process completed successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                status_label.config(text="An error occurred.")

    root = tk.Tk()
    root.title("Dominik Morse' Solution Fixer")

    root.geometry('500x300')

    root.configure(bg='#333333')
    for widget in [tk.Button, tk.Label]:
        root.tk_setPalette(background='#333333', foreground='white',
                           activeBackground='#555555', activeForeground='white')

    select_button = tk.Button(root, text="Select Directory", command=select_directory)
    select_button.pack(pady=20)

    status_label = tk.Label(root, text="Select a directory to start the process.")
    status_label.pack(pady=10)

    root.mainloop()


@app.route('/process-zip-files', methods=['POST'])
def api_process_zip_files():
    try:
        directory = request.json['directory']
        process_zip_files(directory)
        return jsonify({"message": "Process completed successfully!"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
