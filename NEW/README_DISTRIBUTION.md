# Recruitee Tagger - Windows Distribution Guide

This guide explains how to generate and distribute the Windows executable (`.exe`) for this application using GitHub Actions.

## Prerequisites
1. This code must be hosted on a GitHub repository.
2. The repository must be public or have available Actions minutes (if private).

## How to Build
You do not need a Windows computer to build the app. The "Continuous Integration" (CI/CD) system handles it automatically.

1.  **Push Changes**:
    Commit and push your code changes to the `main` or `master` branch.
    ```bash
    git add .
    git commit -m "Update application code"
    git push origin main
    ```

2.  **Wait for Build**:
    - Go to your repository on GitHub.
    - Click the **Actions** tab.
    - Select the workflow named **Build Windows App**.
    - Monitor progress until completion (typically 2-5 minutes).

3.  **Download Executable**:
    - Select the completed workflow run.
    - Scroll to the **Artifacts** section at the bottom.
    - Click **RecruiteeTagger-Windows** to download the archive.
    - Extract the archive to find `RecruiteeTagger.exe`.

## How to Distribute
1.  **First Run**:
    - Extract the downloaded file.
    - Execute `RecruiteeTagger.exe`.
    - **Note**: As the application is not signed with a commercial certificate, Windows may display a "Windows protected your PC" warning.
    - Instruct users to select **More info** followed by **Run anyway**.

2.  **Configuration**:
    - On initial launch, users must enter their configuration (API Keys) or place a `cv_processing_settings.json` file in the same directory for pre-configuration.

## Troubleshooting
- **Build Failures**: Examine the Actions logs to identify any dependencies that failed to install.
- **Application Issues**: Execute the `.exe` from a Command Prompt (`cmd.exe`) to view diagnostic output.
