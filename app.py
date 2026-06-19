import streamlit as st
import requests
import pandas as pd
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="NPI Lookup", page_icon="🏥")

st.title("🏥 NPI Registry Search")
st.markdown("Paste a list of NPI numbers below to verify doctors instantly.")

# --- THE INPUT FORM ---
with st.form("lookup_form"):
    # We use st.text_area, NOT input()
    raw_text = st.text_area("Paste NPIs (Space or Enter separated):", height=150)
    submitted = st.form_submit_button("🔍 Run Search")

# --- THE LOGIC ---
if submitted and raw_text:
    # Clean Data
    raw_list = raw_text.replace(',', ' ').split()
    clean_npi_list = [x.strip() for x in raw_list if x.strip().isdigit() and len(x.strip()) == 10]
    clean_npi_list = list(set(clean_npi_list))

    if not clean_npi_list:
        st.error("❌ No valid 10-digit NPIs found.")
    else:
        st.success(f"Processing {len(clean_npi_list)} unique NPIs...")
        
        progress_bar = st.progress(0)
        results = []
        url = "https://npiregistry.cms.hhs.gov/api/?version=2.1"

        for i, npi in enumerate(clean_npi_list):
            try:
                response = requests.get(url, params={'number': npi})
                data = response.json()
                
                row = {"NPI": npi, "Name": "❌ Not Found", "Phone": "---", "Status": "Invalid"}

                if data.get('result_count', 0) > 0:
                    provider = data['results'][0]
                    basic = provider.get('basic', {})
                    name = f"{basic.get('first_name','')} {basic.get('last_name','')} {basic.get('credential','')}"
                    row["Name"] = name.strip()
                    row["Status"] = "Active"
                    
                    phone = "Not Found"
                    for addr in provider.get('addresses', []):
                        if addr.get('address_purpose') == 'LOCATION':
                            phone = addr.get('telephone_number', 'Not Found')
                            break
                    if phone == "Not Found":
                         for addr in provider.get('addresses', []):
                            if addr.get('address_purpose') == 'MAILING':
                                phone = addr.get('telephone_number', 'Not Found')
                                break
                    row["Phone"] = phone

                results.append(row)
            
            except Exception as e:
                results.append({"NPI": npi, "Name": "Error", "Phone": str(e)})
            
            progress_bar.progress((i + 1) / len(clean_npi_list))
            time.sleep(0.05)

        # Show Results
        st.divider()
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download CSV", csv, "npi_results.csv", "text/csv")

with st.sidebar:
    st.markdown("---")
    st.subheader("Support the Build")
    st.write("If this tool saves you time, consider leaving a tip.")
    st.link_button("☕ Tip via Venmo", "https://venmo.com/u/aydenzosche")
