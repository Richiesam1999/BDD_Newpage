import streamlit as st
import requests
from typing import Optional

# API Configuration
API_URL = "http://localhost:8000"  # Change this if your API runs on a different port/URL


def generate_tests(url: str) -> Optional[dict]:
    """Call the API to generate BDD tests"""
    try:
        response = requests.post(
            f"{API_URL}/generate",
            json={"url": url},
            timeout=300  # 5 minutes timeout for long-running analysis
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


st.title("BDD Test Generator")
st.markdown("Enter a URL to automatically generate BDD test scenarios")

url = st.text_input("Enter URL", placeholder="https://example.com")

if st.button("Generate Tests", type="primary"):
    if not url:
        st.warning("Please enter a URL")
    elif not url.startswith(('http://', 'https://')):
        st.error("URL must start with http:// or https://")
    else:
        with st.spinner("Analyzing page and generating BDD tests... This may take a few minutes."):
            result = generate_tests(url)
            
            if result:
                if result.get("success"):
                    st.success("✅ Tests generated successfully!")
                    
                    # Display the feature file content
                    st.subheader("Generated Feature File")
                    st.code(result.get("feature_content", ""), language="gherkin")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download .feature file",
                        data=result.get("feature_content", ""),
                        file_name=result.get("filename", "feature.feature"),
                        mime="text/plain"
                    )
                    
                    # Show metadata
                    with st.expander("Details"):
                        st.write(f"**URL:** {result.get('url')}")
                        st.write(f"**Filename:** {result.get('filename')}")
                        st.write(f"**Message:** {result.get('message')}")
                else:
                    st.error(f"❌ Generation failed: {result.get('message', 'Unknown error')}")