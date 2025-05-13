import os
import re
import shutil
import fitz
import logging
from src.backend.core.config import COMPANY_CONFIGS

#Extracts specific pages from PDFs
async def data_extractor():
    try:
        all_success = []
        all_failed = []

        for company, config in COMPANY_CONFIGS.items():
            input_dir = config["input_dir"]
            output_dir = config["output_dir"]
            keyword_regex = config["keyword_regex"]

            os.makedirs(output_dir, exist_ok=True)
            success_pdfs = []
            failed_pdfs = []

            #Processing each file
            for filename in os.listdir(input_dir):
                if filename.lower().endswith(".pdf"):
                    try:
                        logging.info(f"[{company}] Processing file: {filename}")
                        input_path = os.path.join(input_dir, filename)
                        output_path = os.path.join(output_dir, filename)

                        #open pdf
                        doc = fitz.open(input_path)
                        found = False
                        for i in range(len(doc)):
                            page = doc.load_page(i)
                            text = page.get_text()
                            if re.search(keyword_regex, text, re.IGNORECASE):
                                #Save matched page to new PDF
                                new_doc = fitz.open()
                                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                                new_doc.save(output_path)
                                new_doc.close()
                                found = True
                                break
                        doc.close()

                        #If not found, copy entire file to output
                        if not found:
                            shutil.copy(input_path, output_path)

                        #Log result
                        (success_pdfs if found else failed_pdfs).append(filename)

                    except Exception as e:
                        logging.error(f"Error in processing files in data extraction: {e}")
                        failed_pdfs.append(filename)

            logging.info(f"[{company}] Success: {success_pdfs}")
            logging.info(f"[{company}] Failed: {failed_pdfs}")
            all_success.extend(success_pdfs)
            all_failed.extend(failed_pdfs)

        return {
            "success_pdfs": all_success,
            "failed_pdfs": all_failed
        }

    except Exception as e:
        logging.error(f"Error in Data extractor: {e}")
        return f"Error in Data extractor: {str(e)}"
