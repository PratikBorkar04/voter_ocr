import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path, pdfinfo_from_path
import pandas as pd
import re
import gc
import time


# -----------------------------
# LANGUAGE DETECTION
# -----------------------------
def detect_language(text):

    # Hindi keywords
    if re.search(r'निर्वाचक|पिता|माता|गृह|उम्र', text):
        return "hindi"

    # Marathi keywords
    if re.search(r'नाव|वडिल|पती|घर|वय', text):
        return "marathi"

    return "english"


# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_text(val):

    if val:
        return val.replace('\n', ' ').strip()

    return None


# -----------------------------
# NORMALIZE GENDER
# -----------------------------
def normalize_gender(val):

    if not val:
        return None

    val = val.strip().lower()

    if val in ["male", "पुरुष"]:
        return "Male"

    elif val in ["female", "स्त्री", "महिला"]:
        return "Female"

    return val


# -----------------------------
# EXTRACT VOTER ID
# -----------------------------
def extract_voter_id(img_roi):

    h, w = img_roi.shape[:2]

    regions = [
        img_roi[int(h * 0.02):int(h * 0.25), int(w * 0.02):int(w * 0.45)],
        img_roi[int(h * 0.02):int(h * 0.25), int(w * 0.45):int(w * 0.98)],
        img_roi[int(h * 0.20):int(h * 0.40), int(w * 0.02):int(w * 0.60)]
    ]

    for region in regions:

        crop = cv2.resize(
            region,
            None,
            fx=4,
            fy=4,
            interpolation=cv2.INTER_CUBIC
        )

        crop = cv2.GaussianBlur(crop, (3, 3), 0)

        _, crop = cv2.threshold(
            crop,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        kernel = np.ones((2, 2), np.uint8)

        crop = cv2.dilate(crop, kernel, iterations=1)

        config = (
            '--psm 7 '
            '-c tessedit_char_whitelist='
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )

        text = pytesseract.image_to_string(
            crop,
            config=config,
            lang='eng'
        ).upper()

        text = text.replace(' ', '').replace('\n', '')

        match = re.search(r'[A-Z]{3}\d{7}', text)

        if match:
            return match.group(0)

    return None


# -----------------------------
# PARSE BODY DATA
# -----------------------------
def parse_body_data(text):

    lang = detect_language(text)

    # ---------------- ENGLISH ----------------
    if lang == "english":

        name = re.search(
            r'Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?=\n|Fathers|Husbands|House|Age|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        father = re.search(
            r'Father[’\'s]*\s*Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?=\n|House|Age|Husband|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        husband = re.search(
            r'Husband[’\'s]*\s*Name\s*[:\-]\s*([A-Za-z\s\.]+?)(?=\n|House|Age|Father|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        mother = None

        house = re.search(
            r'House\s*(?:No|Number)?\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
            text,
            re.IGNORECASE
        )

        age = re.search(
            r'Age\s*[:\-]?\s*(\d+)',
            text,
            re.IGNORECASE
        )

        gender = re.search(
            r'(Male|Female)',
            text,
            re.IGNORECASE
        )

    # ---------------- MARATHI ----------------
    elif lang == "marathi":

        name = re.search(
            r'नाव\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|वडिल|पती|घर|वय|$)',
            text
        )

        father = re.search(
            r'वडिलांचे\s*नाव\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|घर|वय|पती|$)',
            text
        )

        husband = re.search(
            r'पतीचे\s*नाव\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|घर|वय|वडिल|$)',
            text
        )

        mother = None

        house = re.search(
            r'घर\s*क्रमांक\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
            text
        )

        age = re.search(
            r'वय\s*[:\-]?\s*(\d+)',
            text
        )

        gender = re.search(
            r'(पुरुष|स्त्री|महिला)',
            text
        )

    # ---------------- HINDI ----------------
    else:

        name = re.search(
            r'निर्वाचक\s*का\s*नाम\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|पिता|पति|माता|गृह|उम्र|$)',
            text
        )

        father = re.search(
            r'पिता\s*का\s*नाम\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|पति|माता|गृह|उम्र|$)',
            text
        )

        husband = re.search(
            r'पति\s*का\s*नाम\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|पिता|माता|गृह|उम्र|$)',
            text
        )

        mother = re.search(
            r'माता\s*का\s*नाम\s*[:\-]?\s*([\u0900-\u097F\s]+?)(?=\n|पिता|पति|गृह|उम्र|$)',
            text
        )

        house = re.search(
            r'गृह\s*संख्या\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
            text
        )

        age = re.search(
            r'उम्र\s*[:\-]?\s*(\d+)',
            text
        )

        gender = re.search(
            r'(पुरुष|महिला)',
            text
        )

    return {
        "Name": clean_text(name.group(1)) if name else None,
        "Father Name": clean_text(father.group(1)) if father else None,
        "Husband Name": clean_text(husband.group(1)) if husband else None,
        "Mother Name": clean_text(mother.group(1)) if mother else None,
        "House Number": house.group(1).strip() if house else None,
        "Age": age.group(1) if age else None,
        "Gender": normalize_gender(gender.group(1)) if gender else None
    }


# -----------------------------
# PROCESS PDF
# -----------------------------
def process_pdf(
    pdf_path,
    progress_bar=None,
    status_text=None
):

    all_data = []

    info = pdfinfo_from_path(pdf_path)

    total_pages = info["Pages"]

    for page in range(1, total_pages + 1):

        # -----------------------------
        # PROGRESS UPDATE
        # -----------------------------
        if progress_bar:

            progress = int((page / total_pages) * 100)

            progress_bar.progress(progress)

            time.sleep(0.1)

        if status_text:

            status_text.text(
                f"Processing page {page} of {total_pages}..."
            )

        try:

            images = convert_from_path(
                pdf_path,
                dpi=350,
                first_page=page,
                last_page=page
            )

            img = images[0]

            img_cv = cv2.cvtColor(
                np.array(img),
                cv2.COLOR_RGB2BGR
            )

            gray = cv2.cvtColor(
                img_cv,
                cv2.COLOR_BGR2GRAY
            )

            thresh = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                15,
                3
            )

            cnts = cv2.findContours(
                thresh,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            cnts = cnts[0] if len(cnts) == 2 else cnts[1]

            bboxes = [cv2.boundingRect(c) for c in cnts]

            cnts = [
                c for _, c in sorted(
                    zip(bboxes, cnts),
                    key=lambda b: (b[0][1] // 100, b[0][0])
                )
            ]

            for c in cnts:

                x, y, w, h = cv2.boundingRect(c)

                ratio = w / h

                if (
                    500 < w < 1200 and
                    250 < h < 600 and
                    1.5 < ratio < 4.5
                ):

                    roi = gray[y:y+h, x:x+w]

                    # EXTRACT VOTER ID
                    voter_id = extract_voter_id(roi)

                    # OCR FULL TEXT
                    full_text = pytesseract.image_to_string(
                        roi,
                        config='--psm 6',
                        lang='eng+mar+hin'
                    )

                    # SKIP DELETED
                    if "DELETED" in full_text.upper():
                        continue

                    # PARSE DATA
                    data = parse_body_data(full_text)

                    data["Voter ID"] = voter_id

                    # SAVE VALID RECORDS
                    if data["Name"] or data["Voter ID"]:
                        all_data.append(data)

            # -----------------------------
            # MEMORY CLEANUP
            # -----------------------------
            del images
            del img
            del img_cv
            del gray
            del thresh

            gc.collect()

        except Exception as e:

            print(f"Error processing page {page}: {e}")

    # -----------------------------
    # CREATE DATAFRAME
    # -----------------------------
    df = pd.DataFrame(all_data)

    return df