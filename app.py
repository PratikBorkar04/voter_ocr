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
    layout="wide"
)


# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
    <style>

    .main {
        background-color: #f5f7fa;
    }

    .title {
        font-size: 42px;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 10px;
    }

    .subtitle {
        font-size: 18px;
        color: #6b7280;
        text-align: center;
        margin-bottom: 40px;
    }

    .box {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }

    .stButton > button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
        padding: 12px;
        border: none;
    }

    .stDownloadButton > button {
        width: 100%;
        background-color: #16a34a;
        color: white;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
        padding: 12px;
        border: none;
    }

    </style>
""", unsafe_allow_html=True)


# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    '<div class="title">📄 Voter OCR Extractor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload voter list PDFs and convert them into Excel files instantly.'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------
# MAIN CONTAINER
# -----------------------------
with st.container():

    st.markdown('<div class="box">', unsafe_allow_html=True)

    # FILE UPLOAD
    uploaded_file = st.file_uploader(
        "Upload PDF File",
        type=["pdf"]
    )

    # FILE NAME INPUT
    output_filename = st.text_input(
        "Enter Excel File Name",
        value="voter_data"
    )

    # PROCESS BUTTON
    if uploaded_file is not None:

        st.success("PDF uploaded successfully.")

        if st.button("🚀 Process PDF"):

            # SAFE FILENAME
            safe_filename = "".join(
                c for c in output_filename
                if c.isalnum() or c in (" ", "_", "-")
            ).strip()

            # INFO
            st.info("Processing PDF... Please wait.")

            # PROGRESS BAR
            progress_bar = st.progress(0)

            # STATUS
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

                # EMPTY CHECK
                if df.empty:

                    st.warning(
                        "No voter data found."
                    )

                else:

                    st.success(
                        f"✅ Extraction completed successfully. "
                        f"{len(df)} records extracted."
                    )

                    # DATAFRAME
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=500
                    )

                    # TEMP EXCEL
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".xlsx"
                    ) as excel_file:

                        excel_path = excel_file.name

                    # SAVE EXCEL
                    df.to_excel(
                        excel_path,
                        index=False
                    )

                    # DOWNLOAD
                    with open(excel_path, "rb") as file:

                        st.download_button(
                            label="⬇ Download Excel File",
                            data=file,
                            file_name=f"{safe_filename}.xlsx",
                            mime=(
                                "application/"
                                "vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet"
                            )
                        )

                    # DELETE EXCEL
                    os.remove(excel_path)

            except Exception as e:

                st.error(f"Error: {e}")

            finally:

                # DELETE TEMP PDF
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

    st.markdown('</div>', unsafe_allow_html=True)