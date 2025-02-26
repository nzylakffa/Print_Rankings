import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import numpy as np
import base64

# ✅ Public Google Sheets (No Credentials Needed)
SHEET_URLS = {
    "HPPR Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=593850694",
    "PPR Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=2116955188#gid=2116955188",
    "Standard Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=1886253811#gid=1886253811",
    "3 WR HPPR Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=2128569716",
    "3 WR PPR Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=496321386#gid=496321386",
    "PPR SuperFlex Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=1099594593#gid=1099594593",
    "TE Premium Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=866813728#gid=866813728",
    "PPR 6 Point Pass TD Rankings": "https://docs.google.com/spreadsheets/d/1O7XxafNJnvAQHvsPS93hX5BIMqphEfyjovGfdWNM5Ow/gviz/tq?tqx=out:csv&gid=1095986422#gid=1095986422"
}

# ✅ Columns to Keep (For Full Rankings)
COLUMNS_TO_KEEP = [
    "Rank", "ADP", "Player Name", "Team", "Pos",
    "Pos Rank", "Tier", "Proj", "Value", "Auction Value",
    "Risk Rank", "Rookie"
]

# ✅ Position-Based Colors (Swapped QB and WR)
POS_COLORS = {
    "QB": (255, 218, 185),  # Light Orange
    "RB": (144, 238, 144),  # Light Green
    "WR": (173, 216, 230),  # Light Blue
    "TE": (221, 160, 221),  # Light Purple
    "K": (255, 255, 153),   # Light Yellow
    "DST": (211, 211, 211)  # Light Gray
}

st.markdown("<h1 style='text-align: center;'>Download Rankings as PDF</h1>", unsafe_allow_html=True)

# ✅ **Color Coding Selection**
color_option = st.selectbox("Would you like color coding?", ["Yes", "No"])
use_colors = color_option == "Yes"

# ✅ Function to generate a PDF (Portrait Mode)
def generate_pdf(title, df, last_updated, is_top_200=False):
    pdf = FPDF(orientation="P" if not is_top_200 else "L", unit="mm", format="A4")  
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    # ✅ Header: HPPR Rankings or One Page Top 200
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, ln=True, align="C")
    
    # ✅ Add Image (Top Right Corner)
    image_path = "ffa_red.png"  # Local path
    pdf.image(image_path, x=147, y=-2, w=35)  # Adjust X, Y, and width as needed
    pdf.image(image_path, x=27, y=-2, w=35)  # Adjust X, Y, and width as needed

    # ✅ Sub-header: Last Updated (Smaller Font, Only for Full Rankings)
    if not is_top_200:
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 4, f"Last Updated: {last_updated}", ln=True, align="C")
    pdf.ln(2)

    # ✅ Set optimized column widths
    total_width = 190 if not is_top_200 else 275  
    min_width = 7  
    max_width = 35  

    # 🔹 Determine column widths based on content length
    content_widths = {
        col: max(df[col].astype(str).apply(len).max(), len(col)) * 1.5
        for col in df.columns
    }

    # 🔹 Reduce space for small columns
    small_columns = ["ADP", "Tier", "Pos", "Proj", "Value"]
    for col in small_columns:
        if col in content_widths:
            content_widths[col] = min_width  

    # 🔹 Normalize widths to fit within total_width
    total_content_width = sum(content_widths.values())
    scale_factor = total_width / total_content_width if total_content_width > total_width else 1

    col_widths = {col: max(min_width, min(max_width, int(width * scale_factor))) for col, width in content_widths.items()}

    # ✅ Ensure total width is exactly max width by distributing extra space
    remaining_space = total_width - sum(col_widths.values())
    while remaining_space > 0:
        for col in col_widths:
            col_widths[col] += 1
            remaining_space -= 1
            if remaining_space == 0:
                break

    # ✅ Draw table headers
    pdf.set_fill_color(200, 200, 200)  
    pdf.set_text_color(0, 0, 0)  
    pdf.set_font("Arial", "B", 9)

    for col in df.columns:
        pdf.cell(col_widths[col], 6, col, border=1, ln=0, align="C", fill=True)
    pdf.ln()

    # ✅ Draw table rows with color coding by "Pos"
    pdf.set_font("Arial", "", 8)

    for _, row in df.iterrows():
        pos = row["Pos"]
        color = POS_COLORS.get(pos, (255, 255, 255)) if use_colors else (255, 255, 255)  # Apply color if enabled  

        pdf.set_fill_color(*color)  
        pdf.set_text_color(0, 0, 0)  

        for col in df.columns:
            text = str(row[col])[:20]  

            # ✅ Special Highlight for Rookie Column (ONLY for Full Rankings)
            if col == "Rookie" and text == "Rookie" and not is_top_200:
                pdf.set_fill_color(255, 255, 153)  

            pdf.cell(col_widths[col], 6, text, border=1, ln=0, align="C", fill=True)

            if col == "Rookie" and not is_top_200:
                pdf.set_fill_color(*color)  

        pdf.ln()

    return pdf.output(dest="S").encode("latin1")
        
# ✅ Function to generate the One Page Top 200 PDF (Now With Full-Row Color Coding)
def generate_top_200_pdf(title, df):
    pdf = FPDF(orientation="P", unit="mm", format="A4")  # Portrait mode
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    
    # ✅ Header: One Page Top 200
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 6, title, ln=True, align="C")
    pdf.ln(1)
    
    # ✅ Add Image (Top Right Corner)
    image_path = "ffa_red.png"  # Local path
    pdf.image(image_path, x=152, y=-1, w=35)  # Adjust X, Y, and width as needed
    pdf.image(image_path, x=22, y=-1, w=35)  # Adjust X, Y, and width as needed
    
    # ✅ Sub-header: Last Updated (Smaller Font, Only for Full Rankings)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 4, f"Last Updated: {last_updated}", ln=True, align="C")
    pdf.ln(2)

    # ✅ Convert ADP to Integer (Fix Decimal Issue)
    df["ADP"] = pd.to_numeric(df["ADP"], errors="coerce").fillna(0).astype(int)  # Convert to int, handle NaNs

    # ✅ Define layout: 3 vertical sections with proper alignment
    num_rows = len(df)
    split_sizes = [67, 67, 66]  # **Ensuring first two get 67 rows, last one gets 66**
    col_headers = ["Rank", "ADP", "Player Name", "Team", "Pos"]
    
    # ✅ **Tighter Column Widths**
    col_widths = [8, 7, 27, 8, 7]  
    start_x_positions = [10, 75, 140]  # Start X positions for each column section

    pdf.set_font("Arial", "B", 7)  # **Increased Header Font Size**
    pdf.set_fill_color(200, 200, 200)  # Light gray header background

    # ✅ Draw headers once for all three columns
    for start_x in start_x_positions:
        pdf.set_x(start_x)
        for col_name, width in zip(col_headers, col_widths):
            pdf.cell(width, 4, col_name, border=1, ln=0, align="C", fill=True)
    pdf.ln()

    # ✅ Adjust row font to fit 200 players correctly
    pdf.set_font("Arial", "", 6)

    # ✅ Fix Alignment: Print all 3 columns before `pdf.ln()`
    for i in range(max(split_sizes)):  # Iterate through max rows (67)
        for col_index in range(3):  # Loop through 3 sections
            if i < split_sizes[col_index]:  # Ensure we're within the valid row range
                row_index = i + sum(split_sizes[:col_index])  # Compute correct row index
                if row_index < num_rows:
                    row = df.iloc[row_index]
                    pos = row["Pos"]
                    color = POS_COLORS.get(pos, (255, 255, 255)) if use_colors else (255, 255, 255)  # Apply color if enabled

                    # ✅ Set full-row background color
                    pdf.set_fill_color(*color)
                    pdf.set_text_color(0, 0, 0)  # Black text for readability

                    pdf.set_x(start_x_positions[col_index])  # **Ensure correct X position for each section**
                    for col_name, width in zip(col_headers, col_widths):
                        text = str(row[col_name])[:20]  # Truncate long text
                        pdf.cell(width, 4, text, border=1, ln=0, align="C", fill=True)  # **Fill full row color**

                    pdf.set_fill_color(255, 255, 255)  # ✅ Reset fill color for next row

        pdf.ln()  # ✅ **Now, only call `pdf.ln()` after printing all three columns**

    return pdf.output(dest="S").encode("latin1")

def get_pdf_download_link(pdf_data, filename, text):
    """Generates a direct download link for a file to prevent Streamlit from re-running."""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;">{text}</a>'
    return href


col1, col2 = st.columns([1, 1])  # Equal column widths

with col1:
    st.header("Multi Page Rankings")

    for title, url in SHEET_URLS.items():
        try:
            df = pd.read_csv(url)  

            if "Ovr Rank" in df.columns:
                df.rename(columns={"Ovr Rank": "Rank"}, inplace=True)

            df_filtered = df[[col for col in COLUMNS_TO_KEEP if col in df.columns]].head(250)  
            last_updated = df["Last Updated"].dropna().unique()[0] if "Last Updated" in df.columns else "Unknown"
            df_filtered["Rookie"] = df_filtered["Rookie"].replace(np.nan, "").astype(str)

            pdf_data = generate_pdf(title, df_filtered, last_updated)

            # 🔹 Direct download link to prevent re-run
            st.markdown(get_pdf_download_link(pdf_data, f"{title}.pdf", f"⏬ {title}"), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error loading {title}: {e}")
            
with col2:
    st.header("One Page Top 200")

    for title, url in SHEET_URLS.items():
        try:
            df = pd.read_csv(url)

            if "Ovr Rank" in df.columns:
                df.rename(columns={"Ovr Rank": "Rank"}, inplace=True)

            df_top_200 = df[["Rank", "ADP", "Player Name", "Team", "Pos"]].head(200)
            top_200_pdf = generate_top_200_pdf(f"{title}", df_top_200)

            # 🔹 Direct download link to prevent re-run
            st.markdown(get_pdf_download_link(top_200_pdf, f"Top_200_{title}.pdf", f"⏬ {title}"), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error loading {title}: {e}")
