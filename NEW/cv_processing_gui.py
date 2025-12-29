"""
CV Processing System - GUI Interface

A modern PyQt6 GUI for the complete CV processing workflow:
1. Retrieve CVs from Recruitee
2. Process PDFs with OCR to extract text
3. Analyze text with AI prompts
4. Generate Excel output
5. Upload results to Recruitee
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# Import our modules
from CV_retrieve import (
    download_cv,
    search_candidates_without_tags,
)
from PROMPT import get_master_prompt, process_cv
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# Import configuration
import config
from config import (
    DEFAULT_COMPANY_ID,
    DEFAULT_CANDIDATE_LIMIT
)

class ProcessingThread(QThread):
    """Thread for running the CV processing workflow without blocking the GUI."""

    progress_update = pyqtSignal(str)
    step_completed = pyqtSignal(str, int)  # step_name, step_number
    candidates_found = pyqtSignal(int)
    excel_generated = pyqtSignal(str, object)  # file_path, dataframe
    processing_completed = pyqtSignal(bool, str)

    def __init__(self, gui_config):
        super().__init__()
        self.gui_config = gui_config
        self.should_stop = False
        self.waiting_for_confirmation = False
        self.df_results = None

    def run(self):
        try:
            # Step 1: Retrieve CVs
            self.progress_update.emit("Step 1/5: Retrieving CVs from Recruitee...")
            self.step_completed.emit("CV Retrieval", 1)

            candidates = self.retrieve_cvs()
            if not candidates:
                self.processing_completed.emit(False, "No candidates found to process.")
                return

            self.candidates_found.emit(len(candidates))

            # Step 2: Download CVs
            self.progress_update.emit("Step 2/5: Downloading CV files...")
            self.step_completed.emit("CV Download", 2)

            downloaded_cvs = self.download_cvs(candidates)
            if not downloaded_cvs:
                self.processing_completed.emit(False, "Failed to download any CVs.")
                return

            # Step 3: OCR Processing
            self.progress_update.emit("Step 3/5: Processing CVs with OCR...")
            self.step_completed.emit("OCR Processing", 3)

            ocr_results = self.process_ocr(downloaded_cvs)
            if not ocr_results:
                self.processing_completed.emit(False, "OCR processing failed.")
                return

            # Step 4: AI Analysis
            self.progress_update.emit("Step 4/5: Analyzing CV content with AI...")
            self.step_completed.emit("AI Analysis", 4)

            analysis_results = self.analyze_cvs(ocr_results)
            if not analysis_results:
                self.processing_completed.emit(False, "AI analysis failed.")
                return

            # Step 5: Generate Excel
            self.progress_update.emit("Step 5/5: Generating Excel output...")
            self.step_completed.emit("Excel Generation", 5)

            excel_path = self.generate_excel(analysis_results)
            if not excel_path:
                self.processing_completed.emit(False, "Excel generation failed.")
                return

            self.excel_generated.emit(str(excel_path), self.df_results)

            # Wait for confirmation before upload
            if self.gui_config.get("upload_to_recruitee", False):
                self.waiting_for_confirmation = True
                while self.waiting_for_confirmation and not self.should_stop:
                    self.msleep(100)

                if self.should_stop:
                    self.processing_completed.emit(False, "Processing stopped by user.")
                    return

                # Upload to Recruitee
                self.progress_update.emit("Uploading results to Recruitee...")
                upload_success = self.upload_to_recruitee(analysis_results)

                if upload_success:
                    message = f"Successfully processed {len(analysis_results)} candidates and uploaded to Recruitee!"
                else:
                    message = f"Processed {len(analysis_results)} candidates but upload to Recruitee failed."
            else:
                message = f"Successfully processed {len(analysis_results)} candidates (upload disabled)."

            self.processing_completed.emit(True, message)

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.progress_update.emit(error_msg)
            self.processing_completed.emit(False, error_msg)

    def retrieve_cvs(self):
        """Retrieve CVs from Recruitee."""
        try:
            # Clean call without compatibility hack, relying on default behavior or config
            candidates = search_candidates_without_tags(
                self.gui_config["company_id"],
                self.gui_config["recruitee_api_key"]
            )

            # Limit the results to the configured limit
            if candidates and len(candidates) > self.gui_config["candidate_limit"]:
                candidates = candidates[: self.gui_config["candidate_limit"]]

            return candidates
        except Exception as e:
            self.progress_update.emit(f"Error retrieving CVs: {str(e)}")
            return None

    def download_cvs(self, candidates):
        """Download CV files using the existing CV_retrieve.py logic."""
        downloaded_cvs = []
        # Use centralized DOWNLOADED_CVS_DIR
        cv_dir = config.DOWNLOADED_CVS_DIR
        cv_dir.mkdir(exist_ok=True)

        for i, candidate in enumerate(candidates):
            if self.should_stop:
                break

            self.progress_update.emit(f"Downloading CV {i + 1}/{len(candidates)}...")

            try:
                # Use standard download_cv signature
                cv_path = download_cv(
                    candidate,
                    self.gui_config["recruitee_api_key"],
                    self.gui_config["company_id"],
                    cv_dir
                )
                if cv_path:
                    downloaded_cvs.append({"candidate": candidate, "cv_path": cv_path})
                time.sleep(self.gui_config["delay_seconds"])
            except Exception as e:
                self.progress_update.emit(
                    f"Error downloading CV for candidate {candidate.get('id')}: {str(e)}"
                )

        return downloaded_cvs

    def process_ocr(self, downloaded_cvs):
        """Process CVs with OCR using the existing ocr.py logic."""
        # Import the existing OCR functions
        from ocr import process_single_pdf

        ocr_results = []

        # Ensure directories exist
        config.OCR_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

        for i, cv_data in enumerate(downloaded_cvs):
            if self.should_stop:
                break

            self.progress_update.emit(
                f"OCR processing CV {i + 1}/{len(downloaded_cvs)}..."
            )

            try:
                cv_path = Path(cv_data["cv_path"])
                if cv_path.exists():
                    # Clean call to process_single_pdf
                    process_single_pdf(
                        cv_path, api_key=self.gui_config["mistral_api_key"]
                    )

                    # Read the generated markdown file from config dir
                    output_md_path = config.OCR_TEXTS_DIR / f"{cv_path.stem}.md"
                    if output_md_path.exists():
                        with open(output_md_path, "r", encoding="utf-8") as f:
                            markdown_text = f.read()

                        ocr_results.append(
                            {
                                "candidate": cv_data["candidate"],
                                "cv_path": cv_data["cv_path"],
                                "markdown_text": markdown_text,
                            }
                        )
                    else:
                        self.progress_update.emit(
                            f"OCR output file not found for {cv_path.name}"
                        )

                time.sleep(self.gui_config["delay_seconds"])
            except Exception as e:
                self.progress_update.emit(
                    f"Error in OCR for CV {cv_data['cv_path']}: {str(e)}"
                )

        return ocr_results

    def analyze_cvs(self, ocr_results):
        """Analyze CV content with AI using the existing PROMPT.py logic."""
        # Import the existing PROMPT functions
        from mistralai import Mistral

        client = Mistral(api_key=self.gui_config["mistral_api_key"])
        master_prompt = get_master_prompt()
        analysis_results = []

        for i, ocr_data in enumerate(ocr_results):
            if self.should_stop:
                break

            self.progress_update.emit(f"AI analysis CV {i + 1}/{len(ocr_results)}...")

            try:
                # Clean call without compatibility args, relying on client config
                result = process_cv(
                    client=client,
                    ocr_text=ocr_data["markdown_text"],
                    master_prompt_text=master_prompt
                )

                if result:
                    analysis_results.append(
                        {
                            "candidate": ocr_data["candidate"],
                            "cv_path": ocr_data["cv_path"],
                            "analysis": result,
                        }
                    )

                time.sleep(self.gui_config["delay_seconds"])
            except Exception as e:
                self.progress_update.emit(
                    f"Error in AI analysis for CV {ocr_data['cv_path']}: {str(e)}"
                )

        return analysis_results

    def generate_excel(self, analysis_results):
        """Generate Excel output with robust error handling."""
        # Use centralized OUTPUT_DIR
        output_dir = config.OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Prepare data for Excel
            excel_data = []
            for result in analysis_results:
                candidate = result["candidate"]
                analysis = result["analysis"]

                excel_data.append(
                    {
                        "Candidate ID": candidate.get("id", ""),
                        "Name": f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip(),
                        "Email": candidate.get("email", ""),
                        "Gender": analysis.get("gender", ""),
                        "Education Level": analysis.get("education_level", ""),
                        "Graduation Year": analysis.get("graduation_year", ""),
                        "Experience": analysis.get("experience", ""),
                        "Mother Tongue": analysis.get("mother_tong", ""),
                        "School": analysis.get("school", ""),
                        "Field of Study": analysis.get("field_of_study", ""),
                        "CV Path": result["cv_path"],
                    }
                )

            # Create DataFrame
            self.df_results = pd.DataFrame(excel_data)

            # Save to Excel with multiple fallback methods
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = output_dir / f"cv_analysis_results_{timestamp}.xlsx"

            # Add summary sheet
            summary_data = {
                "Metric": [
                    "Total Candidates",
                    "Successfully Analyzed",
                    "Failed Analysis",
                    "Processing Date",
                ],
                "Count": [
                    len(analysis_results),
                    len(self.df_results),
                    len(analysis_results) - len(self.df_results),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ],
            }
            summary_df = pd.DataFrame(summary_data)

            # Save Excel file
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                # Main results sheet
                self.df_results.to_excel(
                    writer, sheet_name="Analysis_Results", index=False
                )
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

            self.progress_update.emit(f"Excel file successfully created: {excel_path}")
            return excel_path

        except Exception as e:
            self.progress_update.emit(f"Critical error generating output: {str(e)}")
            # Last resort: save as simple text file
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                txt_path = output_dir / f"cv_analysis_results_{timestamp}.txt"

                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("CV Analysis Results\n")
                    f.write("=" * 50 + "\n\n")

                    for result in analysis_results:
                        candidate = result["candidate"]
                        analysis = result["analysis"]

                        f.write(f"Candidate ID: {candidate.get('id', 'N/A')}\n")
                        f.write(
                            f"Name: {candidate.get('first_name', '')} {candidate.get('last_name', '')}\n"
                        )
                        f.write(f"Email: {candidate.get('email', 'N/A')}\n")
                        f.write(f"Gender: {analysis.get('gender', 'N/A')}\n")
                        f.write(
                            f"Education Level: {analysis.get('education_level', 'N/A')}\n"
                        )
                        f.write(f"Experience: {analysis.get('experience', 'N/A')}\n")
                        f.write(f"School: {analysis.get('school', 'N/A')}\n")
                        f.write(
                            f"Field of Study: {analysis.get('field_of_study', 'N/A')}\n"
                        )
                        f.write("-" * 30 + "\n\n")

                self.progress_update.emit(f"Results saved as text file: {txt_path}")
                return txt_path

            except Exception as txt_error:
                self.progress_update.emit(
                    f"Failed to save any output format: {str(txt_error)}"
                )
                return None

    def upload_to_recruitee(self, analysis_results):
        """Upload results to Recruitee."""
        try:
            success_count = 0
            for result in analysis_results:
                if self.should_stop:
                    break

                candidate_id = result["candidate"]["id"]
                analysis = result["analysis"]

                # Prepare tags for upload
                tags = []
                for key, value in analysis.items():
                    if value and value != "N/A":
                        tags.append(value)

                # Upload tags to Recruitee
                headers = {
                    "Authorization": f"Bearer {self.gui_config['recruitee_api_key']}",
                    "Content-Type": "application/json",
                }

                url = f"https://api.recruitee.com/c/{self.gui_config['company_id']}/candidates/{candidate_id}/tags"

                response = requests.post(url, headers=headers, json={"tags": tags})
                if response.status_code == 200:
                    success_count += 1

                time.sleep(self.gui_config["delay_seconds"])

            self.progress_update.emit(
                f"Successfully uploaded tags for {success_count}/{len(analysis_results)} candidates"
            )
            return success_count > 0

        except Exception as e:
            self.progress_update.emit(f"Error uploading to Recruitee: {str(e)}")
            return False

    def stop(self):
        """Stop processing."""
        self.should_stop = True

    def confirm_upload(self):
        """Confirm to proceed with upload."""
        self.waiting_for_confirmation = False

    def cancel_upload(self):
        """Cancel the upload process."""
        self.should_stop = True
        self.waiting_for_confirmation = False


class CVProcessingGUI(QWidget):
    """Main GUI window for the CV Processing System."""

    def __init__(self):
        super().__init__()
        self.processing_thread = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Recruitee Tagger V3.0")
        self.setWindowIcon(QIcon("logo_domein_wit_abrikoos_01_rgb.jpg"))
        self.setFixedSize(900, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #4CAF50;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header with logo
        self.create_header(main_layout)

        # Tab widget for organization
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Configuration tab
        self.create_config_tab()

        # Processing tab
        self.create_processing_tab()

        # Results tab
        self.create_results_tab()

    def create_header(self, layout):
        """Create the header section with logo."""
        header_frame = QFrame()
        header_frame.setStyleSheet(
            "background-color: white; border-radius: 8px; margin: 5px;"
        )
        header_layout = QHBoxLayout(header_frame)

        # Logo
        try:
            pixmap = QPixmap("logo_domein_wit_abrikoos_01_rgb.jpg")
            logo_label = QLabel()
            logo_label.setPixmap(
                pixmap.scaled(
                    120,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            header_layout.addWidget(logo_label)
        except Exception:
            logo_label = QLabel("LOGO")
            logo_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #4CAF50;"
            )
            header_layout.addWidget(logo_label)

        # Title
        title_label = QLabel("Recruitee Tagger V3.0")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addWidget(header_frame)

    def create_config_tab(self):
        """Create the configuration tab."""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)

        # API Configuration Group
        api_group = QGroupBox("API Configuration")
        api_layout = QGridLayout(api_group)

        api_layout.addWidget(QLabel("Recruitee API Key:"), 0, 0)
        self.recruitee_key_input = QLineEdit()
        self.recruitee_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.recruitee_key_input.setPlaceholderText("Enter your Recruitee API key")
        api_layout.addWidget(self.recruitee_key_input, 0, 1)

        api_layout.addWidget(QLabel("Mistral API Key:"), 1, 0)
        self.mistral_key_input = QLineEdit()
        self.mistral_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.mistral_key_input.setPlaceholderText("Enter your Mistral API key")
        api_layout.addWidget(self.mistral_key_input, 1, 1)

        api_layout.addWidget(QLabel("Company ID:"), 2, 0)
        self.company_id_input = QLineEdit()
        self.company_id_input.setPlaceholderText("Enter your Recruitee Company ID")
        self.company_id_input.setText("24899")  # Default value
        api_layout.addWidget(self.company_id_input, 2, 1)

        layout.addWidget(api_group)

        # Processing Configuration Group
        processing_group = QGroupBox("Processing Configuration")
        processing_layout = QGridLayout(processing_group)

        processing_layout.addWidget(QLabel("Candidate Limit:"), 0, 0)
        self.candidate_limit_input = QSpinBox()
        self.candidate_limit_input.setRange(1, 100)
        self.candidate_limit_input.setValue(10)
        self.candidate_limit_input.setToolTip("Maximum number of candidates to process")
        processing_layout.addWidget(self.candidate_limit_input, 0, 1)

        layout.addWidget(processing_group)

        # Options Group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.upload_to_recruitee_checkbox = QCheckBox(
            "Upload results to Recruitee (uncheck for dry run)"
        )
        self.upload_to_recruitee_checkbox.setChecked(True)
        self.upload_to_recruitee_checkbox.setToolTip(
            "When unchecked, results will be processed but not uploaded"
        )
        options_layout.addWidget(self.upload_to_recruitee_checkbox)

        self.generate_excel_checkbox = QCheckBox("Generate Excel output")
        self.generate_excel_checkbox.setChecked(True)
        self.generate_excel_checkbox.setToolTip(
            "Generate an Excel file with analysis results"
        )
        options_layout.addWidget(self.generate_excel_checkbox)

        layout.addWidget(options_group)

        # Save/Load buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self.load_settings)
        button_layout.addWidget(load_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()
        self.tabs.addTab(config_widget, "Configuration")

    def create_processing_tab(self):
        """Create the processing tab."""
        processing_widget = QWidget()
        layout = QVBoxLayout(processing_widget)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; font-size: 14px; padding: 12px 24px; }"
        )
        self.start_btn.clicked.connect(self.start_processing)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Processing")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Step progress
        self.step_progress = QProgressBar()
        self.step_progress.setRange(0, 5)
        self.step_progress.setValue(0)
        self.step_progress.setVisible(False)
        progress_layout.addWidget(self.step_progress)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to start processing")
        self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_group)

        # Log section
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(250)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)

        layout.addWidget(log_group)

        # Confirmation section (initially hidden)
        self.confirmation_group = QGroupBox("Excel Generated - Confirm Upload")
        self.confirmation_group.setVisible(False)
        confirmation_layout = QVBoxLayout(self.confirmation_group)

        self.excel_path_label = QLabel("")
        self.excel_path_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        confirmation_layout.addWidget(self.excel_path_label)

        instruction_label = QLabel(
            "Please review the Excel file above and confirm if you want to proceed with uploading results to Recruitee."
        )
        instruction_label.setWordWrap(True)
        confirmation_layout.addWidget(instruction_label)

        confirmation_buttons = QHBoxLayout()

        self.open_excel_btn = QPushButton("Open Excel File")
        self.open_excel_btn.setStyleSheet("QPushButton { background-color: #2196F3; }")
        self.open_excel_btn.clicked.connect(self.open_excel_file)
        confirmation_buttons.addWidget(self.open_excel_btn)

        self.confirm_upload_btn = QPushButton("Confirm & Upload")
        self.confirm_upload_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; }"
        )
        self.confirm_upload_btn.clicked.connect(self.confirm_upload)
        confirmation_buttons.addWidget(self.confirm_upload_btn)

        self.cancel_upload_btn = QPushButton("Cancel Upload")
        self.cancel_upload_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; }"
        )
        self.cancel_upload_btn.clicked.connect(self.cancel_upload)
        confirmation_buttons.addWidget(self.cancel_upload_btn)

        confirmation_layout.addLayout(confirmation_buttons)

        layout.addWidget(self.confirmation_group)

        self.tabs.addTab(processing_widget, "Processing")

    def create_results_tab(self):
        """Create the results tab."""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)

        # Statistics section
        stats_group = QGroupBox("Processing Statistics")
        stats_layout = QGridLayout(stats_group)

        self.candidates_found_label = QLabel("Candidates Found: 0")
        stats_layout.addWidget(self.candidates_found_label, 0, 0)

        self.candidates_processed_label = QLabel("Candidates Processed: 0")
        stats_layout.addWidget(self.candidates_processed_label, 0, 1)

        self.last_run_label = QLabel("Last Run: Never")
        stats_layout.addWidget(self.last_run_label, 1, 0, 1, 2)

        layout.addWidget(stats_group)

        # Results display
        results_group = QGroupBox("Recent Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Processing results will appear here...")
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group)

        self.tabs.addTab(results_widget, "Results")

    def validate_configuration(self):
        """Validate the current configuration."""
        if not self.recruitee_key_input.text().strip():
            QMessageBox.warning(
                self, "Missing Configuration", "Please enter your Recruitee API key."
            )
            return False

        if not self.mistral_key_input.text().strip():
            QMessageBox.warning(
                self, "Missing Configuration", "Please enter your Mistral API key."
            )
            return False

        if not self.company_id_input.text().strip():
            QMessageBox.warning(
                self, "Missing Configuration", "Please enter your Company ID."
            )
            return False

        return True

    def start_processing(self):
        """Start the CV processing workflow."""
        if not self.validate_configuration():
            return

        # Prepare configuration
        gui_config = {
            "recruitee_api_key": self.recruitee_key_input.text().strip(),
            "mistral_api_key": self.mistral_key_input.text().strip(),
            "company_id": self.company_id_input.text().strip(),
            "candidate_limit": self.candidate_limit_input.value(),
            "delay_seconds": 2,
            "upload_to_recruitee": self.upload_to_recruitee_checkbox.isChecked(),
            "generate_excel": self.generate_excel_checkbox.isChecked(),
        }

        # Update UI state
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.step_progress.setVisible(True)
        self.step_progress.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Starting processing...")
        self.status_label.setStyleSheet("font-weight: bold; color: #ff9800;")

        # Clear previous log
        self.log_text.clear()
        self.log_message("Processing started...")

        # Hide confirmation group initially
        self.confirmation_group.setVisible(False)

        # Start processing thread
        self.processing_thread = ProcessingThread(gui_config)
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.step_completed.connect(self.update_step_progress)
        self.processing_thread.candidates_found.connect(self.update_candidates_found)
        self.processing_thread.excel_generated.connect(self.on_excel_generated)
        self.processing_thread.processing_completed.connect(self.processing_finished)
        self.processing_thread.start()

    def stop_processing(self):
        """Stop the current processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.log_message("Stopping processing...")
            self.status_label.setText("Stopping...")

    def update_progress(self, message):
        """Update the progress display."""
        self.status_label.setText(message)
        self.log_message(message)

    def update_step_progress(self, step_name, step_number):
        """Update the step progress bar."""
        self.step_progress.setValue(step_number)
        self.log_message(f"Completed: {step_name}")

    def update_candidates_found(self, count):
        """Update the candidates found count."""
        self.candidates_found_label.setText(f"Candidates Found: {count}")

    def processing_finished(self, success, message):
        """Handle processing completion."""
        # Update UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.step_progress.setVisible(False)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText("Processing completed successfully!")
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.status_label.setText("Processing failed!")
            self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")

        self.log_message(message)
        self.last_run_label.setText(
            f"Last Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Add to results
        self.results_text.append(
            f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---"
        )
        self.results_text.append(message)

        # Show completion message
        msg_type = QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning
        QMessageBox(msg_type, "Processing Complete", message, parent=self).exec()

    def log_message(self, message):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """Clear the processing log."""
        self.log_text.clear()

    def on_excel_generated(self, excel_path, df_results):
        """Handle Excel file generation."""
        self.current_excel_path = excel_path
        self.excel_path_label.setText(f"Excel file generated: {excel_path}")
        self.confirmation_group.setVisible(True)
        self.log_message(f"Excel output ready for review: {excel_path}")

        # Update processed count
        if df_results is not None:
            self.candidates_processed_label.setText(
                f"Candidates Processed: {len(df_results)}"
            )

    def open_excel_file(self):
        """Open the generated Excel file."""
        if hasattr(self, "current_excel_path") and os.path.exists(
            self.current_excel_path
        ):
            try:
                os.startfile(self.current_excel_path)  # Windows
            except Exception:
                try:
                    os.system(f'open "{self.current_excel_path}"')  # macOS
                except Exception:
                    try:
                        os.system(f'xdg-open "{self.current_excel_path}"')  # Linux
                    except Exception:
                        QMessageBox.information(
                            self,
                            "File Location",
                            f"Excel file saved at:\n{self.current_excel_path}",
                        )

    def confirm_upload(self):
        """Confirm to proceed with upload."""
        if self.processing_thread:
            self.confirmation_group.setVisible(False)
            self.log_message("Upload confirmed. Proceeding with Recruitee upload...")
            self.processing_thread.confirm_upload()

    def cancel_upload(self):
        """Cancel the upload process."""
        if self.processing_thread:
            self.confirmation_group.setVisible(False)
            self.log_message("Upload canceled by user.")
            self.processing_thread.cancel_upload()

    def save_settings(self):
        """Save current configuration to file including API keys."""
        settings = {
            "recruitee_api_key": self.recruitee_key_input.text(),
            "mistral_api_key": self.mistral_key_input.text(),
            "company_id": self.company_id_input.text(),
            "candidate_limit": self.candidate_limit_input.value(),
            "delay_seconds": 2,  # Fixed 2-second delay
            "upload_to_recruitee": self.upload_to_recruitee_checkbox.isChecked(),
            "generate_excel": self.generate_excel_checkbox.isChecked(),
        }

        try:
            # Save settings in the NEW folder
            settings_path = Path(__file__).parent / "cv_processing_settings.json"
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(
                self,
                "Settings Saved",
                f"Configuration saved successfully to:\n{settings_path}",
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Save Error", f"Failed to save settings: {str(e)}"
            )

    def load_settings(self):
        """Load configuration from file including API keys."""
        try:
            # Load settings from the NEW folder
            settings_path = Path(__file__).parent / "cv_processing_settings.json"
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    settings = json.load(f)

                # Load API keys
                self.recruitee_key_input.setText(settings.get("recruitee_api_key", ""))
                self.mistral_key_input.setText(settings.get("mistral_api_key", ""))

                # Load other settings
                self.company_id_input.setText(settings.get("company_id", "24899"))
                self.candidate_limit_input.setValue(settings.get("candidate_limit", 10))
                self.upload_to_recruitee_checkbox.setChecked(
                    settings.get("upload_to_recruitee", True)
                )
                self.generate_excel_checkbox.setChecked(
                    settings.get("generate_excel", True)
                )

                QMessageBox.information(
                    self,
                    "Settings Loaded",
                    f"Configuration loaded successfully from:\n{settings_path}",
                )
        except Exception as e:
            QMessageBox.warning(
                self, "Load Error", f"Failed to load settings: {str(e)}"
            )

    def closeEvent(self, event):
        """Handle window close event."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Processing is still running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_thread.stop()
                self.processing_thread.wait(3000)  # Wait up to 3 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look

    # Set application icon
    try:
        app.setWindowIcon(QIcon("logo_domein_wit_abrikoos_01_rgb.jpg"))
    except Exception:
        pass

    window = CVProcessingGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
