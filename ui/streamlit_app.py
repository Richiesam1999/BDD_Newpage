import streamlit as st

st.title("BDD Test Generator")
url = st.text_input("Enter URL")

if st.button("Generate Tests"):
    with st.spinner("Analyzing page..."):
        result = analyze_and_generate(url)
        st.success("Tests generated!")
        st.download_button("Download .feature file", result)