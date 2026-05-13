import streamlit as st
import pandas as pd
import tempfile
import os

from ocr_utils import process_pdf


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Voter OCR Extractor",
    page_icon="📄",
    layout="centered"
)


# -----------------------------
# TITLE
# -----------------------------
st.title("📄 Voter OCR Extractor")

st.write(
    "Upload voter PDF and extract data into Excel format."
)


# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload PDF File",
    type=["pdf"]
)


# -----------------------------
# PROCESS BUTTON
# -----------------------------
if uploaded_file is not None:

    st.success("PDF uploaded successfully.")

    if st.button("Process PDF"):

        # INFO MESSAGE
        st.info("Processing PDF... Please wait.")

        # PROGRESS BAR
        progress_bar = st.progress(0)

        # STATUS TEXT
        status_text = st.empty()

        # SAVE TEMP PDF
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp_file:

            tmp_file.write(uploaded_file.read())

            temp_pdf_path = tmp_file.name

        try:

            # OCR PROCESS
            df = process_pdf(
                temp_pdf_path,
                progress_bar,
                status_text
            )

            # COMPLETE PROGRESS
            progress_bar.progress(100)

            status_text.text(
                "Processing completed."
            )

            if df.empty:

                st.warning(
                    "No voter data found."
                )

            else:

                st.success(
                    f"Extraction completed. "
                    f"{len(df)} records found."
                )

                # SHOW DATAFRAME
                st.dataframe(df)

                # CREATE EXCEL FILE
                excel_path = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".xlsx"
                ).name

                df.to_excel(
                    excel_path,
                    index=False
                )

                # DOWNLOAD BUTTON
                with open(excel_path, "rb") as file:

                    st.download_button(
                        label="⬇ Download Excel File",
                        data=file,
                        file_name="voter_data.xlsx",
                        mime=(
                            "application/"
                            "vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        )
                    )

                # DELETE EXCEL FILE
                os.remove(excel_path)

        except Exception as e:

            st.error(f"Error: {e}")

        finally:

            # DELETE TEMP PDF
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)