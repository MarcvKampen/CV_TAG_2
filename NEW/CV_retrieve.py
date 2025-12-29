"""
Recruitee API Module for CV Retrieval.

Handles searching for candidates and downloading their CVs.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests

from config import DOWNLOADED_CVS_DIR


def search_candidates_without_tags(company_id: str, api_key: str, base_url: str = None) -> list | None:
    """
    Search for candidates created in the last year that have no tags.

    Args:
        company_id: Recruitee company ID
        api_key: Recruitee API key
        base_url: Optional base URL (for compatibility)

    Returns:
        List of candidate dictionaries, or None on error
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    actual_base_url = base_url if base_url else f"https://api.recruitee.com/c/{company_id}"

    one_year_ago = datetime.now() - timedelta(days=365)
    start_date = one_year_ago.strftime("%Y-%m-%d")

    filters = {
        "query": f"created_at:>{start_date}",
        "filters_json": json.dumps([{"field": "tags", "has_none": True}]),
    }

    try:
        print(f"Searching for candidates created since {start_date} without tags...")
        response = requests.post(
            f"{actual_base_url}/search/new/candidates",
            headers=headers,
            params={"limit": 200},
            json=filters,
        )
        response.raise_for_status()

        candidates = response.json().get("hits", [])
        print(f"Found {len(candidates)} candidates without tags.")

        if not candidates:
            return []

        # Sort by creation date (most recent first)
        candidates.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        return candidates

    except requests.exceptions.RequestException as e:
        print(f"Error searching candidates: {e}")
        if e.response is not None:
            print(f"Status: {e.response.status_code}, Response: {e.response.text}")
        return None


def get_candidate_details(candidate_id: str, api_key: str, company_id: str) -> dict | None:
    """Get detailed candidate information including CV URL."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"https://api.recruitee.com/c/{company_id}/candidates/{candidate_id}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("candidate", {})
    except requests.exceptions.RequestException as e:
        print(f"Error getting candidate details for {candidate_id}: {e}")
        return None


def get_cv_url_from_candidate(candidate_details: dict) -> str | None:
    """Extract CV URL from candidate details."""
    if not candidate_details:
        return None

    # Check multiple possible CV URL fields
    cv_url = (
        candidate_details.get("cv_url")
        or candidate_details.get("cv_original_url")
        or candidate_details.get("cv_original_file")
    )

    # Look in files array for any PDF
    if not cv_url:
        for file in candidate_details.get("files", []):
            if file.get("url") and file.get("url", "").lower().endswith(".pdf"):
                cv_url = file["url"]
                break

    return cv_url


def download_cv(candidate_data: dict, api_key: str, company_id: str, save_dir: Path) -> Path | None:
    """
    Download a candidate's CV and return the file path.

    Args:
        candidate_data: Candidate dictionary with at least 'id' field
        api_key: Recruitee API key
        company_id: Recruitee company ID
        save_dir: Directory to save the CV file to

    Returns:
        Path to downloaded CV, or None on failure
    """
    try:
        candidate_id = candidate_data.get("id")
        if not candidate_id:
            print("No candidate ID found.")
            return None

        # Ensure save_dir exists
        save_dir.mkdir(parents=True, exist_ok=True)

        candidate_details = get_candidate_details(candidate_id, api_key, company_id)
        if not candidate_details:
            print(f"Could not get details for candidate {candidate_id}")
            return None

        cv_url = get_cv_url_from_candidate(candidate_details)
        if not cv_url:
            print(f"No CV found for candidate {candidate_id}")
            return None

        print(f"Downloading CV from: {cv_url}")
        response = requests.get(cv_url, stream=True)
        response.raise_for_status()

        first_name = candidate_details.get("first_name", "Unknown")
        last_name = candidate_details.get("last_name", "Unknown")

        # Clean filename
        filename = f"CV_{candidate_id}_{first_name}_{last_name}.pdf"
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filepath = save_dir / filename

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"CV saved to: {filepath}")
        return filepath

    except requests.exceptions.RequestException as e:
        print(f"Error downloading CV: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during CV download: {e}")
        return None
