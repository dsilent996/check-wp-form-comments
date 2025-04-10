import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import time
import os
import uuid
import urllib3

# Menonaktifkan warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_comment_form(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10, verify=False)  # Tambahkan verify=False
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            comment_form_selectors = ['form#commentform', 'form.comment-form', 'form[id*="comment"]', 'form[class*="comment"]']
            for selector in comment_form_selectors:
                if soup.select(selector):
                    return "Ada Form Komentar"
            return "Tidak Ada Form Komentar"
        else:
            return f"Error {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def process_urls_parallel(url_list):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_comment_form, url_list))
    return results

def process_excel(file_path, output_folder):
    start_time = time.time()
    
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = df.columns.str.strip()
    
    if 'URL' not in df.columns:
        possible_url_col = [col for col in df.columns if 'url' in col.lower()]
        if possible_url_col:
            df.rename(columns={possible_url_col[0]: 'URL'}, inplace=True)
        else:
            st.error("Kolom 'URL' tidak ditemukan dalam file Excel. Pastikan nama kolom benar.")
            return None
    
    st.write(f"Memproses {len(df)} URL dengan multi-threading...")
    df['Status Form Komentar'] = process_urls_parallel(df['URL'].tolist())
    
    output_file = os.path.join(output_folder, f"hasil_pengecekan_{uuid.uuid4().hex}.xlsx")
    df.to_excel(output_file, index=False)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    st.success(f"Laporan selesai! Hasil disimpan di {output_file}")
    st.write(f"Waktu eksekusi: {elapsed_time:.2f} detik")
    
    return output_file

def main():
    st.title("Pengecekan Form Komentar pada Website")
    uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])
    
    output_folder = "temp_results"
    os.makedirs(output_folder, exist_ok=True)
    
    if uploaded_file is not None:
        for f in os.listdir(output_folder):
            file_path = os.path.join(output_folder, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        file_path = os.path.join(output_folder, f"uploaded_{uuid.uuid4().hex}.xlsx")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("Proses File"):
            output_file = process_excel(file_path, output_folder)
            if output_file:
                with open(output_file, "rb") as f:
                    st.download_button("Unduh Hasil", f, file_name="hasil_pengecekan.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                os.remove(output_file)
                os.remove(file_path)

if __name__ == "__main__":
    main()