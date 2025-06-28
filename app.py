import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import json

# Page configuration
st.set_page_config(
    page_title="Mapped_Data_Reviewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_data' not in st.session_state:
    st.session_state.current_data = None

if 'reviewed_items' not in st.session_state:
    st.session_state.reviewed_items = set()

def load_sample_data():
    """Load the sample CSV data"""
    try:
        df = pd.read_csv("attached_assets/mapped_quals_1751118898970.csv")
        return df
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
        return None

def apply_score_styling(score):
    """Apply color styling based on score"""
    if pd.isna(score):
        return "#f8f9fa"
    if score > 0.8:
        return "#d4edda"  # Light green
    else:
        return "#f8d7da"  # Light red

def main():
    st.title("📊 Mapped_Data_Reviewer")
    st.markdown("Upload and review mapped client master qualification CSV data with question-answer mappings, filtering, and review tracking.")
    
    # Sidebar for file upload and controls
    with st.sidebar:
        st.header("📁 Data Management")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload your CSV file containing question-answer mappings"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.current_data = df
                st.success(f"✅ Loaded {len(df)} records")
                
                # Display basic info
                st.write("**Dataset Info:**")
                st.write(f"- Rows: {len(df)}")
                st.write(f"- Columns: {len(df.columns)}")
                
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
                return
        
        # Clear reviewed items
        if st.session_state.current_data is not None:
            if st.button("🔄 Clear All Reviews", use_container_width=True):
                st.session_state.reviewed_items.clear()
                st.success("All review statuses cleared!")
                st.rerun()
    
    # Main content area
    if st.session_state.current_data is not None:
        df = st.session_state.current_data.copy()
        
        # Ensure score column is numeric
        if 'score' in df.columns:
            df['score'] = pd.to_numeric(df['score'], errors='coerce')
        
        # Filters section
        st.header("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Language filter
            languages = df['language'].unique().tolist() if 'language' in df.columns else []
            selected_languages = st.multiselect(
                "Filter by Client_Country_Name",
                options=languages,
                default=[]
            )
            
            # Score range filter
            if 'score' in df.columns:
                score_min = float(df['score'].min())
                score_max = float(df['score'].max())
                # Ensure min and max are different to avoid slider conflicts
                if score_min == score_max:
                    score_max = score_min + 0.01
                score_range = st.slider(
                    "Score Range",
                    min_value=score_min,
                    max_value=score_max,
                    value=(score_min, score_max),
                    step=0.001,
                    format="%.3f"
                )
            else:
                score_range = (0.0, 1.0)
        
        with col2:
            # Qualification filter
            qualifications = df['qualification_name'].unique().tolist() if 'qualification_name' in df.columns else []
            selected_qualifications = st.multiselect(
                "Filter by Client Qualification Name",
                options=qualifications,
                default=[]
            )
            
            # Review status filter
            review_status = st.selectbox(
                "Review Status",
                options=['All', 'Reviewed', 'Not Reviewed'],
                index=0
            )
        
        with col3:
            # Search filter
            search_term = st.text_input(
                "Search",
                value="",
                placeholder="Search across all fields..."
            )
            
            # Clear filters button
            if st.button("🔄 Clear All Filters", use_container_width=True):
                st.rerun()
        
        # Apply filters
        filtered_df = df.copy()
        
        # Language filter
        if selected_languages:
            filtered_df = filtered_df[filtered_df['language'].isin(selected_languages)]
        
        # Qualification filter
        if selected_qualifications:
            filtered_df = filtered_df[filtered_df['qualification_name'].isin(selected_qualifications)]
        
        # Score range filter
        if 'score' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['score'] >= score_range[0]) & 
                (filtered_df['score'] <= score_range[1])
            ]
        
        # Review status filter
        if review_status != 'All':
            if review_status == 'Reviewed':
                filtered_df = filtered_df[filtered_df.index.isin(st.session_state.reviewed_items)]
            else:  # Not Reviewed
                filtered_df = filtered_df[~filtered_df.index.isin(st.session_state.reviewed_items)]
        
        # Search filter
        if search_term:
            search_mask = filtered_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[search_mask]
        
        # Display results summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Filtered Records", len(filtered_df))
        with col3:
            reviewed_count = len(st.session_state.reviewed_items)
            st.metric("Reviewed Items", reviewed_count)
        with col4:
            if 'score' in df.columns:
                high_score_count = len(filtered_df[filtered_df['score'] > 0.8])
                st.metric("High Score (>0.8)", high_score_count)
            else:
                st.metric("High Score (>0.8)", "N/A")
        
        # Export buttons
        if len(filtered_df) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export all filtered data
                export_df = filtered_df.copy()
                export_df['reviewed_status'] = export_df.index.isin(st.session_state.reviewed_items)
                csv_data = export_df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Export All Filtered Data",
                    data=csv_data,
                    file_name="filtered_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Export only reviewed items
                reviewed_indices = [idx for idx in filtered_df.index if idx in st.session_state.reviewed_items]
                if reviewed_indices:
                    reviewed_df = filtered_df.loc[reviewed_indices].copy()
                    reviewed_df['reviewed_status'] = True
                    reviewed_csv = reviewed_df.to_csv(index=False)
                    
                    st.download_button(
                        label="✅ Export Reviewed Items",
                        data=reviewed_csv,
                        file_name="reviewed_items.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.button("✅ Export Reviewed Items", disabled=True, use_container_width=True, help="No reviewed items to export")
            
            with col3:
                # Export only non-reviewed items
                non_reviewed_indices = [idx for idx in filtered_df.index if idx not in st.session_state.reviewed_items]
                if non_reviewed_indices:
                    non_reviewed_df = filtered_df.loc[non_reviewed_indices].copy()
                    non_reviewed_df['reviewed_status'] = False
                    non_reviewed_csv = non_reviewed_df.to_csv(index=False)
                    
                    st.download_button(
                        label="⏳ Export Non-Reviewed Items",
                        data=non_reviewed_csv,
                        file_name="non_reviewed_items.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.button("⏳ Export Non-Reviewed Items", disabled=True, use_container_width=True, help="No non-reviewed items to export")
        
        # Data Table Display
        st.header("📋 Data Table")
        
        if len(filtered_df) > 0:
            # Pagination controls
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
            with col2:
                total_pages = max(1, (len(filtered_df) - 1) // items_per_page + 1)
                page = st.number_input(
                    f"Page (1-{total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )
            with col3:
                st.write(f"**Total:** {len(filtered_df)} records")
            
            # Calculate pagination indices
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(filtered_df))
            
            # Get page data
            page_data = filtered_df.iloc[start_idx:end_idx].copy()
            
            # Add selection checkboxes
            if 'selected_rows' not in st.session_state:
                st.session_state.selected_rows = set()
            
            # Prepare table data with review status and styling - reordered for better readability
            display_data = []
            
            for idx, (row_idx, row) in enumerate(page_data.iterrows()):
                # Check if reviewed
                is_reviewed = row_idx in st.session_state.reviewed_items
                
                # Create a dictionary for this row with logical column ordering
                row_data = {
                    'Select': row_idx in st.session_state.selected_rows,
                    'Row #': start_idx + idx + 1,
                    'Reviewed': '✅ Yes' if is_reviewed else '⏳ No',
                    'Score': f"{row.get('score', 0):.3f}" if pd.notna(row.get('score', 0)) else 'N/A',
                    'Language': row.get('language', 'N/A'),
                    # Qualification mapping side by side
                    'Original Qualification': str(row.get('qualification_name', 'N/A'))[:60] + '...' if len(str(row.get('qualification_name', 'N/A'))) > 60 else str(row.get('qualification_name', 'N/A')),
                    'Client Qualification': str(row.get('client_qualification_name', 'N/A'))[:60] + '...' if len(str(row.get('client_qualification_name', 'N/A'))) > 60 else str(row.get('client_qualification_name', 'N/A')),
                    # Question mapping side by side
                    'Original Question': str(row.get('questions', 'N/A'))[:80] + '...' if len(str(row.get('questions', 'N/A'))) > 80 else str(row.get('questions', 'N/A')),
                    'Client Question': str(row.get('client_questions', 'N/A'))[:80] + '...' if len(str(row.get('client_questions', 'N/A'))) > 80 else str(row.get('client_questions', 'N/A')),
                    # Answer mapping side by side
                    'Original Answer': str(row.get('qualificationAnswerDesc', 'N/A'))[:60] + '...' if len(str(row.get('qualificationAnswerDesc', 'N/A'))) > 60 else str(row.get('qualificationAnswerDesc', 'N/A')),
                    'Client Answer': str(row.get('client_answer_text', 'N/A'))[:60] + '...' if len(str(row.get('client_answer_text', 'N/A'))) > 60 else str(row.get('client_answer_text', 'N/A'))
                }
                
                # Add any additional columns not already included
                key_cols = ['language', 'score', 'qualification_name', 'client_qualification_name', 
                           'questions', 'client_questions', 'client_answer_text', 'qualificationAnswerDesc']
                for col in row.index:
                    if col not in key_cols and col not in row_data:
                        row_data[f'Extra: {col}'] = str(row[col])[:40] + '...' if len(str(row[col])) > 40 else str(row[col])
                
                display_data.append(row_data)
            
            # Convert to DataFrame for display
            table_df = pd.DataFrame(display_data)
            

            
            # Apply styling and display table - using newer map function
            styled_table = table_df.style.map(
                lambda x: 'background-color: #d4edda' if '✅' in str(x) else 
                         ('background-color: #fff3cd' if '⏳' in str(x) else ''),
                subset=['Reviewed']
            )
            
            # Apply score-based styling
            if 'Score' in table_df.columns:
                def score_style(val):
                    if val == 'N/A':
                        return 'background-color: #f8f9fa'
                    try:
                        score_val = float(val)
                        if score_val > 0.8:
                            return 'background-color: #d4edda; color: #155724'  # Green
                        else:
                            return 'background-color: #f8d7da; color: #721c24'  # Red
                    except:
                        return 'background-color: #f8f9fa'
                
                styled_table = styled_table.map(score_style, subset=['Score'])
            
            # Apply selection highlighting
            if 'Select' in table_df.columns:
                styled_table = styled_table.map(
                    lambda x: 'background-color: #cce5ff; font-weight: bold' if x else '',
                    subset=['Select']
                )
            
            # Use data_editor for built-in selection functionality
            edited_df = st.data_editor(
                table_df,
                use_container_width=True,
                height=500,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select rows for bulk actions",
                        width="small",
                    ),
                    "Original Qualification": st.column_config.TextColumn(
                        "Original Qualification",
                        width="medium",
                        disabled=True,
                    ),
                    "Client Qualification": st.column_config.TextColumn(
                        "Client Qualification", 
                        width="medium",
                        disabled=True,
                    ),
                    "Original Question": st.column_config.TextColumn(
                        "Original Question",
                        width="large",
                        disabled=True,
                    ),
                    "Client Question": st.column_config.TextColumn(
                        "Client Question",
                        width="large",
                        disabled=True,
                    ),
                    "Original Answer": st.column_config.TextColumn(
                        "Original Answer",
                        width="medium",
                        disabled=True,
                    ),
                    "Client Answer": st.column_config.TextColumn(
                        "Client Answer",
                        width="medium",
                        disabled=True,
                    ),
                    "Score": st.column_config.NumberColumn(
                        "Score",
                        format="%.3f",
                        width="small",
                        disabled=True,
                    ),
                    "Reviewed": st.column_config.TextColumn(
                        "Reviewed",
                        width="small",
                        disabled=True,
                    ),
                    "Row #": st.column_config.NumberColumn(
                        "Row #",
                        width="small",
                        disabled=True,
                    ),
                    "Language": st.column_config.TextColumn(
                        "Language",
                        width="small",
                        disabled=True,
                    )
                },
                disabled=["Row #", "Reviewed", "Language", "Score", "Original Qualification", "Client Qualification", "Original Question", "Client Question", "Original Answer", "Client Answer"],
                hide_index=True,
                key=f"data_editor_{page}"
            )
            
            # Update selection state based on edited dataframe and add bulk actions
            selected_indices = []
            for i, (row_idx, row) in enumerate(page_data.iterrows()):
                if i < len(edited_df) and edited_df.iloc[i]['Select']:
                    selected_indices.append(row_idx)
            
            # Bulk review actions below the table
            if len(selected_indices) > 0:
                st.subheader("🔍 Bulk Review Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"✅ Mark {len(selected_indices)} Selected as Reviewed", use_container_width=True):
                        for idx in selected_indices:
                            st.session_state.reviewed_items.add(idx)
                        st.success(f"Marked {len(selected_indices)} items as reviewed!")
                        st.rerun()
                
                with col2:
                    if st.button(f"↩️ Unmark {len(selected_indices)} Selected", use_container_width=True):
                        for idx in selected_indices:
                            st.session_state.reviewed_items.discard(idx)
                        st.success(f"Unmarked {len(selected_indices)} items!")
                        st.rerun()
                
                with col3:
                    st.write(f"**Selected:** {len(selected_indices)} of {len(page_data)} rows")
            
            elif st.session_state.get('show_bulk_help', True):
                st.info("💡 **Tip:** Use the checkboxes in the 'Select' column to choose rows for bulk review actions.")
                if st.button("Hide this tip"):
                    st.session_state.show_bulk_help = False
                    st.rerun()
            

            
            # Display pagination info
            st.markdown(f"📄 Showing items {start_idx + 1}-{end_idx} of {len(filtered_df)}")
            
        else:
            st.warning("No data matches the current filters.")
            
    else:
        # Welcome message when no data is loaded
        st.info("👆 Please upload a CSV file or load sample data using the sidebar to get started.")
        
        # Show example of expected format
        st.markdown("### Expected CSV Format")
        st.markdown("""
        Your CSV file should contain columns for question-answer mappings such as:
        - `language`: Language/country information
        - `questions`: Survey questions  
        - `qualification_name`: Qualification category
        - `client_answer_text`: Answer options
        - `score`: Numerical score (0-1 range)
        - Other columns will be displayed as additional information
        """)

if __name__ == "__main__":
    main()