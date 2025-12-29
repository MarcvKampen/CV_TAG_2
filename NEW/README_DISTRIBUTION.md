# Recruitee Tagger - Windows Distribution Guide

This guide explains how to generate and distribute the Windows executable (`.exe`) for this application using GitHub Actions.

## Prerequisites
1. This code must be hosted on a GitHub repository.
2. The repository must measure visibility (private repositories have limited Action minutes).

## How to Build
You do not need a Windows computer to build the app. The "Continuous Integration" (CI/CD) system handles it for you.

1.  **Push Changes**:
    Simply commit and push your code changes to the `main` or `master` branch.
    ```bash
    git add .
    git commit -m "Update application code"
    git push origin main
    ```

2.  **Wait for Build**:
    - Go to your repository on GitHub.
    - Click the **"Actions"** tab.
    - You will see a workflow named **"Build Windows App"** running.
    - It takes about 2-5 minutes to complete.

3.  **Download Executable**:
    - Once the workflow shows a green checkmark (Success), click on it.
    - Scroll down to the **"Artifacts"** section at the bottom.
    - Click on **"RecruiteeTagger-Windows"** to download the zip file.
    - Inside, you will find `RecruiteeTagger.exe`.

## How to Distribute
1.  **First Run**:
    - Unzip the downloaded file.
    - Double-click `RecruiteeTagger.exe`.
    - **Note**: Since this app is not "signed" with a paid certificate, Windows might show a "Windows protected your PC" warning.
    - Tell users to click **"More info"** -> **"Run anyway"**.

2.  **Configuration**:
    - On the first run, the user will need to enter their configuration (API Keys) or place a `cv_processing_settings.json` file in the same folder if you want to pre-configure it.

## Troubleshooting
- **Build Fails?** Check the "Actions" logs to see if a specific requirement failed to install.
- **App Crashes?** Run the `.exe` from a command prompt (`cmd.exe`) to see error messages.
