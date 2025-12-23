import streamlit as st
import requests
import pandas as pd
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="NPI Lookup", page_icon="🏥", layout="centered")

st.title("🏥 NPI Registry Search")
st.markdown("Paste a list of NPI numbers below to verify doctors instantly.")

# --- INPUT ---
with st.form("lookup_form"):
    raw_text = st.text_area("Paste NPIs (Space or Enter separated):", height=150)
    submitted = st.form_submit_button("🔍 Run Search")

if submitted and raw_text:
    # 1. CLEAN DATA
    raw_list = raw_text.replace(',', ' ').split()
    clean_npi_list = [x.strip() for x in raw_list if x.strip().isdigit() and len(x.strip()) == 10]
    clean_npi_list = list(set(clean_npi_list)) # Remove duplicates

    if not clean_npi_list:
        st.error("❌ No valid 10-digit NPIs found.")
    else:
        st.success(f"Processing {len(clean_npi_list)} unique NPIs...")
        
        # 2. SETUP PROGRESS
        progress_bar = st.progress(0)
        results = []
        url = "https://npiregistry.cms.hhs.gov/api/?version=2.1"

        # 3. RUN LOOP
        for i, npi in enumerate(clean_npi_list):
            try:
                response = requests.get(url, params={'number': npi})
                data = response.json()
                
                # Default values
                row = {
                    "NPI": npi, 
                    "Name": "❌ Not Found", 
                    "Phone": "---", 
                    "Status": "Invalid"
                }

                if data.get('result_count', 0) > 0:
                    provider = data['results'][0]
                    basic = provider.get('basic', {})
                    
                    # Name Logic
                    full_name = f"{basic.get('first_name','')} {basic.get('last_name','')} {basic.get('credential','')}"
                    row["Name"] = full_name.strip()
                    row["Status"] = "Active"
                    
                    # Phone Logic
                    phone = "Not Found"
                    addresses = provider.get('addresses', [])
                    for addr in addresses:
                        if addr.get('address_purpose') == 'LOCATION':
                            phone = addr.get('telephone_number', 'Not Found')
                            break
                    if phone == "Not Found":
                        for addr in addresses:
                            if addr.get('address_purpose') == 'MAILING':
                                phone = addr.get('telephone_number', 'Not Found')
                                break
                    row["Phone"] = phone

                results.append(row)
            
            except Exception as e:
                results.append({"NPI": npi, "Name": "Error", "Phone": str(e), "Status": "Error"})
            
            # Update Bar
            progress_bar.progress((i + 1) / len(clean_npi_list))
            time.sleep(0.05) # Tiny pause

        # 4. SHOW RESULTS
        st.divider()
        df = pd.DataFrame(results)
        
        # Display interactive table
        st.dataframe(df, use_container_width=True)

        # CSV Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name='npi_results.csv',
            mime='text/csv',
        )
