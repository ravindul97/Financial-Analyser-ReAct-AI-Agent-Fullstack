import os
import io
import re
import json
import logging
import pandas as pd
from collections import Counter
from google import genai
from src.backend.core.config import COMPANY_CONFIGS, GOOGLE_API_KEY

#Financial metrics to extract
target_metrics = [
    "Revenue",
    "COGS",
    "Gross Profit",
    "Operating Expenses",
    "Operating Income",
    "Net Income"
]

#Helper to standardize metric names
def standardize_metric(metric):
    try:
        replacements = {
            "Cost of Goods Sold": "COGS",
            "Cost of Sales": "COGS",
            "Operating Profit": "Operating Income",
            "Profit from Operations": "Operating Income",
            "Profit for the period": "Net Income",
            "Net Profit": "Net Income"
        }
        return replacements.get(metric.strip(), metric.strip())
    
    except Exception as e:
        logging.error(f"Error in standardize metric: {e}")
        raise ValueError(f"Error in standardize_metric: {e}")

#Extract datetime for sorting periods
def extract_date(period_str):
    try:
        return pd.to_datetime(period_str, format="%m/%Y")
    except Exception as e:
        logging.error(f"Error in extract date: {e}")
        return pd.NaT

#Output directory
os.makedirs("data/processed_csv", exist_ok=True)

async def create_dataset():
    try:
        #Loop through both companies
        client = genai.Client(api_key=GOOGLE_API_KEY)
        for company, config in COMPANY_CONFIGS.items():
            input_dir = config["input_dir"]
            output_csv = config["output_csv"]

            logging.info(f"\nProcessing {company} reports in {input_dir}")
            file_data = []

            for filename in os.listdir(input_dir):
                if filename.lower().endswith(".pdf"):
                    logging.info(f"Processing {filename}...")
                    file_path = os.path.join(input_dir, filename)

                    try:
                        #Upload PDF
                        with open(file_path, "rb") as f:
                            uploaded_file = client.files.upload(
                                file=io.BytesIO(f.read()),
                                config=dict(mime_type='application/pdf')
                            )

                        #System prompt
                        prompt = """
                        You are a senior financial data extraction assistant specializing in extracting accurate financial data from PDF statements.

                        Instructions:
                        1. Extract only the most recent "3 months ended" financial data.
                        2. Focus solely on the "Group" or "Consolidated" results, excluding any "Company" or standalone parent company columns.
                        3. Ensure you extract data from the most recent financial period, typically denoted in the heading, title, or footnotes.
                        4. Handle Negative Numbers:
                            Any numbers enclosed in parentheses MUST be converted into negative value.
                            Example: (3000) = -3000
                        5. Handling Currency Scales:
                            If values are labeled as Rs. '000 (thousands), multiply each value by 1,000.
                            If labeled as Rs. Mn or Rs. Millions, multiply each value by 1,000,000.
                            If labeled as Rs. Bn or Rs. Billions, multiply each value by 1,000,000,000.
                            If no currency unit is specified, assume values are in full rupees unless context suggests otherwise.
                        6. Key Metrics to Extract and Compute:
                            Revenue: Total revenue for the most recent period.
                            Cost of Goods Sold (COGS) or Cost of Sales: The direct costs attributable to goods produced or sold (Negative).
                            Gross Profit: Calculated as Revenue minus COGS.
                            Operating Expenses: The (negative) sum of "Distribution Costs" and "Administrative Expenses" only (ignore other expenses like marketing, interest, etc.).
                            Operating Income (or Profit from Operations): Gross Profit plus Other Operating Income minus Operating Expenses (excluding finance costs, taxes, and non-operating income).
                            Net Income (or Profit for the Period): The final profit or loss after tax, including discontinued operations if reported.
                        7. Output Requirements:
                            Your output must be a valid JSON object.
                            Ensure no commentary, extra symbols, or explanations are included.
                            Use null for any missing values.
                            The Period must be formatted as MM/YYYY based on the extracted date of the most recent period.

                        Output format example:
                        {
                        "Period": "MM/YYYY",
                        "Revenue": "1000000",
                        "COGS": "400000",
                        "Gross Profit": "600000",
                        "Operating Expenses": "150000",
                        "Operating Income": "450000",
                        "Net Income": "350000"
                        }
                        """


                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=[uploaded_file, prompt]
                        )

                        raw_text = response.text.strip()

                        #Clean code block formatting if any
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]

                        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                        if not json_match:
                            raise ValueError("No valid JSON object found in Gemini output.")

                        data = json.loads(json_match.group(0))
                        period = data.get("Period", "Unknown")
                        metrics = {standardize_metric(k): v for k, v in data.items() if k != "Period"}

                        logging.info(f"Extracted data for Period {period}: {metrics}")
                        file_data.append({
                            "filename": filename,
                            "period": period,
                            "data": metrics
                        })

                    except Exception as e:
                        logging.error(f"Skipping {filename} due to error: {e}")
                        continue

            #Analyze periods
            period_counts = Counter(entry["period"] for entry in file_data)
            for period, count in period_counts.items():
                if count > 1:
                    logging.info(f"Duplicate period '{period}' detected in {count} files.")
                if period == "Unknown":
                    logging.info("Some files returned 'Unknown' period.")

            #Get unique sorted periods
            all_periods = sorted({entry['period'] for entry in file_data if entry['period'] != "Unknown"}, key=extract_date)

            #Build final DataFrame
            final_df = pd.DataFrame({"Data Point Name": target_metrics})
            for period in all_periods:
                #Get first matching file entry for this period
                matching_entry = next((entry for entry in file_data if entry["period"] == period), None)
                period_values = [matching_entry["data"].get(metric, "") if matching_entry else "" for metric in target_metrics]
                final_df[period] = period_values

            final_df.to_csv(output_csv, index=False)
            logging.info(f"Saved to {output_csv}")

        return f"Succesful"

    except Exception as e:
        logging.error(f"Error in Dataset creation: {e}")
        return f"Error in Dataset creation: {str(e)}"
