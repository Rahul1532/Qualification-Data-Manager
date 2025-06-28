import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Tuple
import io

def apply_score_styling(score: float) -> Dict[str, str]:
    """Apply color styling based on score value."""
    if score > 0.8:
        return {
            'background-color': '#d4edda',
            'border-color': '#c3e6cb',
            'color': '#155724'
        }
    elif score > 0.5:
        return {
            'background-color': '#fff3cd',
            'border-color': '#ffeaa7',
            'color': '#856404'
        }
    else:
        return {
            'background-color': '#f8d7da',
            'border-color': '#f5c6cb',
            'color': '#721c24'
        }

def create_filters(df: pd.DataFrame) -> Dict[str, Any]:
    """Create filter controls and return filter values."""
    filters = {}
    
    # Create filter columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Language filter
        languages = df['language'].unique().tolist() if 'language' in df.columns else []
        filters['languages'] = st.multiselect(
            "Filter by Language",
            options=languages,
            default=[],
            help="Select one or more languages to filter"
        )
        
        # Score range filter
        if 'score' in df.columns:
            score_min = float(df['score'].min())
            score_max = float(df['score'].max())
            filters['score_range'] = st.slider(
                "Score Range",
                min_value=score_min,
                max_value=score_max,
                value=(score_min, score_max),
                step=0.01,
                help="Filter by score range"
            )
        else:
            filters['score_range'] = (0.0, 1.0)
    
    with col2:
        # Qualification filter
        qualifications = df['qualification_name'].unique().tolist() if 'qualification_name' in df.columns else []
        filters['qualifications'] = st.multiselect(
            "Filter by Qualification",
            options=qualifications,
            default=[],
            help="Select one or more qualifications to filter"
        )
        
        # Review status filter
        filters['review_status'] = st.selectbox(
            "Review Status",
            options=['All', 'Reviewed', 'Not Reviewed'],
            index=0,
            help="Filter by review status"
        )
    
    with col3:
        # Search filter
        filters['search_term'] = st.text_input(
            "Search",
            value="",
            placeholder="Search across all fields...",
            help="Search for text in any column"
        )
        
        # Clear filters button
        if st.button("🔄 Clear All Filters", use_container_width=True):
            # Reset filters by rerunning the app
            for key in st.session_state.keys():
                if key.startswith('filter_'):
                    del st.session_state[key]
            st.rerun()
    
    return filters

def export_filtered_data(df: pd.DataFrame, reviewed_items: set) -> str:
    """Export filtered data as CSV string with review status."""
    export_df = df.copy()
    export_df['reviewed_status'] = export_df.index.isin(reviewed_items)
    
    # Convert to CSV string
    output = io.StringIO()
    export_df.to_csv(output, index=False)
    return output.getvalue()

def get_color_for_score(score: float) -> str:
    """Get background color for score value."""
    if score > 0.8:
        return "#d4edda"  # Light green
    elif score > 0.5:
        return "#fff3cd"  # Light yellow
    else:
        return "#f8d7da"  # Light red

def get_border_color_for_score(score: float) -> str:
    """Get border color for score value."""
    if score > 0.8:
        return "#c3e6cb"  # Green border
    elif score > 0.5:
        return "#ffeaa7"  # Yellow border
    else:
        return "#f5c6cb"  # Red border

def format_score_display(score: float) -> str:
    """Format score for display with appropriate styling."""
    if pd.isna(score):
        return "N/A"
    return f"{score:.4f}"

def validate_csv_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate CSV structure and return validation results."""
    # Updated required columns based on the actual CSV structure
    required_columns = ['language', 'questions', 'qualification_name', 'client_answer_text', 'score']
    missing_columns = []
    warnings = []
    
    # Check for required columns
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(f"Missing required column: {col}")
    
    # Check for score column validation
    if 'score' in df.columns:
        try:
            score_series = pd.to_numeric(df['score'], errors='coerce')
            if score_series.isna().any():
                warnings.append("Some score values could not be converted to numbers.")
        except Exception as e:
            warnings.append(f"Error processing score column: {str(e)}")
    
    # Check for other expected columns
    expected_columns = [
        'lang_id', 'language_id', 'client_questions', 'qualification_id', 
        'client_qualification_name', 'client_qualification_id', 'client_answer_id',
        'preCode', 'qualificationAnswerDesc', 'qualificationAnswerId'
    ]
    
    missing_optional = [col for col in expected_columns if col not in df.columns]
    if missing_optional:
        warnings.append(f"Optional columns not found: {', '.join(missing_optional)}")
    
    is_valid = len(missing_columns) == 0
    
    return is_valid, missing_columns + warnings

def get_summary_stats(df: pd.DataFrame, reviewed_items: set) -> Dict[str, Any]:
    """Get summary statistics for the dataset."""
    stats = {
        'total_records': len(df),
        'reviewed_records': len([idx for idx in df.index if idx in reviewed_items]),
        'languages': df['language'].nunique() if 'language' in df.columns else 0,
        'qualifications': df['qualification_name'].nunique() if 'qualification_name' in df.columns else 0,
    }
    
    if 'score' in df.columns:
        score_series = pd.to_numeric(df['score'], errors='coerce')
        stats.update({
            'avg_score': score_series.mean(),
            'min_score': score_series.min(),
            'max_score': score_series.max(),
            'high_scores': len(score_series[score_series > 0.8]),
            'low_scores': len(score_series[score_series <= 0.5])
        })
    
    stats['review_percentage'] = (stats['reviewed_records'] / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
    
    return stats

def create_score_histogram(df: pd.DataFrame):
    """Create a histogram of score distribution using Streamlit's built-in chart."""
    if 'score' in df.columns:
        score_series = pd.to_numeric(df['score'], errors='coerce').dropna()
        if not score_series.empty:
            st.bar_chart(score_series.value_counts().sort_index())
    else:
        st.info("No score data available for histogram.")
