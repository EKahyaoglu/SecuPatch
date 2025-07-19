"""
SecuPatch
Author: Eren Kahyaoglu

Description:
    Streamlit-based dashboard that checks for server patch compliance.
    Users are expected to upload a YAML path manifest (.yaml/.yml) and a CSV log of patches (.csv) applied.
    The app evaluates which servers are compliant or non-compliant based on the inputs.
    The output will show results in visualizations and allows the user to download a compliance report (in PDF).
"""

import yaml
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import StringIO


def load_patch_manifest(file_obj):
    """
    Load the patch manifest from a YAML (.yaml/.yml) file.

    Args:
        file_obj: File-like object containing YAML content.

    Returns:
        dict: Dictionary mapping server names to required patch IDs.
    """
    # Parse YAML content from file-like object
    return yaml.safe_load(file_obj)


def parse_log_file(file_obj):
    """
    Parse the uploaded CSV file and extract server patch log data.

    Args:
        file_obj: File-like object containing CSV content.

    Returns:
        list: List of dictionaries representing a server patch log.
    """
    logs = []

    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(file_obj)

    # Error Handling for CSV
    expected_columns = {"server", "patch", "timestamp"}
    if not expected_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns.\nFound: {df.columns.tolist()}")

    # Iterate over rows in DF to extract & format patch log information
    for _, row in df.iterrows():
        logs.append(
            {
                "server": row["server"],    # Server Name
                "patch": row["patch"],      # Applied Patch ID
                "timestamp": datetime.strptime(row["timestamp"], "%Y-%m-%d"),   # Converts timestamp string to datetime object
            }
        )

    return logs


def evaluate_compliance(patch_manifest, logs):
    """
    Evaluate compliance by comparing patch logs against the patch manifest.

    Args:
        patch_manifest (dict): Dictionary of server: required_patch pairs.
        logs (list): List of log entries from the CSV.

    Returns:
        dict: Dictionary mapping each server to 'Compliant' or 'Non-Compliant'.
    """
    compliance = {}     # Compliance status for each server
    scores = []         # Scores for each server
    breakdown = []      # Breakdown of compliance per server

    for server, required_patch in patch_manifest.items():
        # Find all logs for the current server
        matching_logs = [log for log in logs if log["server"] == server]

        # Determine if required patch was applied
        has_required_patch = any(log["patch"] == required_patch for log in matching_logs)

        # Calculate compliance score (0-100)
        score = 0
        
        if has_required_patch:
            # Base score for having required patch
            score = 60
            
            # Bonus points for patch recency (up to 25 points)
            if matching_logs:
                latest_date = max(log["timestamp"] for log in matching_logs)
                days_since_2024 = (latest_date - datetime(2024, 1, 1)).days
                if days_since_2024 > 150:  # Recent patches (after ~May 2024)
                    score += 25
                elif days_since_2024 > 90:  # Moderately recent
                    score += 15
                else:  # Older patches
                    score += 5
            
            # Bonus points for patch management activity (up to 15 points)
            patch_count = len(matching_logs)
            if patch_count >= 3:
                score += 15
            elif patch_count >= 2:
                score += 10
            else:
                score += 5
                
        else:
            # Partial credit for having some patches, even if not the required one
            if matching_logs:
                patch_count = len(matching_logs)
                if patch_count >= 3:
                    score = 30  # Shows active patch management
                elif patch_count >= 2:
                    score = 20
                else:
                    score = 10
            # If no patches at all, score remains 0

        # Ensure score doesn't exceed 100
        score = min(score, 100)

        # Determine compliance status based on score
        if score >= 80:
            compliance[server] = "Compliant"
        elif score >= 40:
            compliance[server] = "Partially Compliant"
        else:
            compliance[server] = "Non-Compliant"

        scores.append({"server": server, "score": score})

        # Find most recent patch date (If no logs exist, mark as "N/A")
        latest_patch_date = max((log["timestamp"] for log in matching_logs), default="N/A")
        breakdown.append({
            "server": server,
            "required_patch": required_patch,
            "status": compliance[server],
            "latest_patch_date": latest_patch_date if latest_patch_date != "N/A" else "N/A"
        })

    return compliance, pd.DataFrame(scores), pd.DataFrame(breakdown)


def generate_summary_text(compliance):
    """
    Generate a plain-text summary of compliant, partially compliant, and non-compliant servers.

    Args:
        compliance (dict): Dictionary of server compliance statuses.

    Returns:
        str: A formatted compliance summary string.
    """
    compliant = [s for s, status in compliance.items() if status == "Compliant"]
    partially_compliant = [s for s, status in compliance.items() if status == "Partially Compliant"]
    non_compliant = [s for s, status in compliance.items() if status == "Non-Compliant"]

    # Format results into compliance summary string
    summary = "--- COMPLIANCE SUMMARY ---\n"
    summary += f"Compliant Servers ({len(compliant)}): {compliant}\n"
    summary += f"Partially Compliant Servers ({len(partially_compliant)}): {partially_compliant}\n"
    summary += f"Non-Compliant Servers ({len(non_compliant)}): {non_compliant}\n"
    return summary


def main():
    """
    Main function that boots the Streamlit UI for SecuPatch.

    Allows users to upload a YAML manifest and a CSV log, evaluate compliance,
    and displays a summary of results.
    """
    st.title("🛡️ SecuPatch")

    st.markdown(
        """
    Upload a YAML patch manifest and a CSV log file to check for compliance.
    - The YAML file should contain server: required_patch entries.
    - The CSV file should have columns: server, patch, timestamp (YYYY-MM-DD).
    """
    )
    # Information & Upload Fields
    company = st.text_input("Enter your company/school name:")
    reviewer = st.text_input("Enter your name (Reviewer):")
    yaml_file = st.file_uploader("Upload Patch Manifest (.yml/.yaml)", type=["yml", "yaml"])
    csv_file = st.file_uploader("Upload System Logs (.csv)", type=["csv"])

    if yaml_file and csv_file:
        try:
            patch_manifest = yaml.safe_load(yaml_file)
            logs = parse_log_file(csv_file)
            compliance, score_df, breakdown_df = evaluate_compliance(patch_manifest, logs)
            summary = generate_summary_text(compliance)
            st.text(summary)

            # Show Compliance Scores
            st.subheader("Compliance Scores by Server")
            st.bar_chart(score_df.set_index("server"))

            # Create Pie Chart
            pie_df = score_df.copy()
            pie_df["status"] = pie_df["score"].apply(lambda x: "Compliant" if x == 100 else "Non-Compliant")
            pie_summary = pie_df["status"].value_counts().reset_index()
            pie_summary.columns = ["status", "count"]
            pie_chart = px.pie(pie_summary, names="status", values="count", title="Compliance Status")
            st.plotly_chart(pie_chart)

            # Create Drill-down dashboard
            st.subheader("Drill-down Server Patch Details")
            for _, row in breakdown_df.iterrows():
                with st.expander(f"{row['server']} - {row['status']}"):
                    st.write(f"Required Patch: {row['required_patch']}")
                    st.write(f"Latest Patch Date: {row['latest_patch_date']}")

            # Create Export & Download Button
            st.subheader("Download Compliance Report")
            report_df = breakdown_df.copy()
            report_df["company"] = company
            report_df["reviewer"] = reviewer
            report_df["report_generated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            csv_buffer = StringIO()
            report_df.to_csv(csv_buffer, index=False)
            st.download_button("Download CSV Report", csv_buffer.getvalue(), "secupatch_compliance_report.csv", "text/csv")

        except Exception as e:
            st.error(f"Error during analysis: {e}")


if __name__ == "__main__":
    main()
