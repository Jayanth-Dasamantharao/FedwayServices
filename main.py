import streamlit as st
import json
import os

# Load data from subsections.json
with open('subsections.json', 'r') as f:
    data = json.load(f)

# Base directory where your images are located
image_base_dir = "output_images"  # Adjust this to where your images folder is located

# Clean and format content for proper bullet points
def format_content(content):
    # Replace bullet point Unicode with actual bullet point and fix common spacing issues
    content = content.replace("\uf0b7", "•")  # Bullet point replacement
    content = content.replace(" o ", "\n   • ")  # Adjust sub-bullets (optional)
    
    # Remove any unnecessary spaces between words
    content = content.replace("  ", " ").replace(" .", ".").replace(" ,", ",")
    
    # Split by lines at bullet points for cleaner formatting
    formatted_content = content.split("•")
    
    # Return cleaned-up bullet points
    return formatted_content

# Function to display content and images
def display_subsection(subsection):
    # Display subsection heading
    st.subheader(subsection["subsection-name"])
    
    # Display content with proper bullet point formatting
    content_list = format_content(subsection["content"])
    
    image_counter = 0  # To track which image to display after 2 bullet points
    
    for i, bullet in enumerate(content_list):
        if bullet.strip():
            st.write(f"• {bullet.strip()}")  # Ensure each bullet point is displayed on a new line
            
            # Display image after every 2 bullet points
            if (i + 1) % 2 == 0 and image_counter < len(subsection["images"]):
                image_path = subsection["images"][image_counter]
                full_image_path = os.path.join(image_base_dir, os.path.basename(image_path))
                
                if os.path.exists(full_image_path):
                    st.image(full_image_path, caption=os.path.basename(image_path))
                    image_counter += 1
                else:
                    st.write(f"Image not found: {full_image_path}")


# def main():
#     st.title("Fedway Services - Text and Image Retrieval")

#     pdf_path = '/Users/jayanthdasamantharao/EliteUS/imageandtext/POET_Everyday_Instructions.pdf'
    
#     # User input
#     query = st.text_input("Ask a question about everyday instructions:")
#     if query:
#         subsection_found = False
#         for subsection in data:
#             if query.lower() == subsection["subsection-name"].lower():
#                 display_subsection(subsection)
#                 subsection_found = True
#                 break
#             if not subsection_found:
#                 st.write("No matching subsection found. Please try again.")

if __name__ == '__main__':
    st.title("Fedway Services - Text and Image Retrieval")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about everyday instructions:"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        if prompt:
            subsection_found = False
            for subsection in data:
                if prompt.lower() == subsection["subsection-name"].lower():
                    display_subsection(subsection)
                    subsection_found = True
                    st.session_state.messages.append({"role": "assistant", "content": "Done"})
                    break
                if not subsection_found:
                    #st.session_state.messages.append({"role": "assistant", "content": "No matching subsection found. Please try again."})
                    st.write("No matching subsection found. Please try again.")
