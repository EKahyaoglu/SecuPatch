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


def load_patch_manifest(file_path):
    """
    Load the patch manifest from a YAML (.yaml/.yml) file.

    Args:
        file_path: File-like object containing YAML content.

    Returns:
        dict: Dictionary mapping server names to required patch IDs.
    """
    # Open YAML file and parse its contents into a dict
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def parse_log_file(file_path):
    """
    Parse the uploaded CSV file and extract server patch log data.

    Args:
        file_path: Path to the CSV log file.

    Returns:
        list: List of dictionaries representing a server patch log.
    """
    logs = []

    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)

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
        matched = any(log["patch"] == required_patch for log in matching_logs)

        # Mark server as compliant/non-compliant
        compliance[server] = "Compliant" if matched else "Non-Compliant"

        # Assign score (100: Compliant, 0: Non-Compliant)
        score = 100 if matched else 0
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
    Generate a plain-text summary of compliant and non-compliant servers.

    Args:
        compliance (dict): Dictionary of server compliance statuses.

    Returns:
        str: A formatted compliance summary string.
    """
    compliant = [s for s, status in compliance.items() if status == "Compliant"]
    non_compliant = [s for s, status in compliance.items() if status == "Non-Compliant"]

    # Format results into compliance summary string
    summary = "--- COMPLIANCE SUMMARY ---\n"
    summary += f"Compliant Servers ({len(compliant)}): {compliant}\n"
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
    yaml_file = st.file_uploader("Upload Patch Manifest (.yml/.yaml)", type=["yml"])
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
