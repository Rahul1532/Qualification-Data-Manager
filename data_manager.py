import streamlit as st
import pandas as pd
import json
from typing import Set, List, Dict, Any

class DataManager:
    """Manages CSV data loading, filtering, and review state tracking."""
    
    def __init__(self):
        self.data = None
        self.reviewed_items = set()
        self._load_reviewed_state()
    
    def load_data(self, df: pd.DataFrame) -> None:
        """Load CSV data into the manager."""
        self.data = df.copy()
        # Ensure numeric score column
        if 'score' in self.data.columns:
            self.data['score'] = pd.to_numeric(self.data['score'], errors='coerce')
        else:
            # If no score column, create a default one
            self.data['score'] = 0.5
    
    def get_data(self) -> pd.DataFrame:
        """Get the loaded data."""
        return self.data.copy() if self.data is not None else pd.DataFrame()
    
    def mark_reviewed(self, row_index: int) -> None:
        """Mark a specific row as reviewed."""
        self.reviewed_items.add(row_index)
        self._save_reviewed_state()
    
    def unmark_reviewed(self, row_index: int) -> None:
        """Unmark a specific row as reviewed."""
        self.reviewed_items.discard(row_index)
        self._save_reviewed_state()
    
    def is_reviewed(self, row_index: int) -> bool:
        """Check if a row is marked as reviewed."""
        return row_index in self.reviewed_items
    
    def get_reviewed_items(self) -> Set[int]:
        """Get all reviewed item indices."""
        return self.reviewed_items.copy()
    
    def get_review_stats(self) -> Dict[str, int]:
        """Get review statistics."""
        total = len(self.data) if self.data is not None else 0
        reviewed = len(self.reviewed_items)
        return {
            'total': total,
            'reviewed': reviewed,
            'pending': total - reviewed,
            'review_percentage': (reviewed / total * 100) if total > 0 else 0
        }
    
    def get_score_distribution(self) -> Dict[str, int]:
        """Get score distribution statistics."""
        if self.data is None or 'score' not in self.data.columns:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        high_score = len(self.data[self.data['score'] > 0.8])
        medium_score = len(self.data[(self.data['score'] > 0.5) & (self.data['score'] <= 0.8)])
        low_score = len(self.data[self.data['score'] <= 0.5])
        
        return {
            'high': high_score,
            'medium': medium_score,
            'low': low_score
        }
    
    def filter_data(self, **filters) -> pd.DataFrame:
        """Apply filters to the data."""
        if self.data is None:
            return pd.DataFrame()
        
        filtered_df = self.data.copy()
        
        # Apply language filter
        if 'languages' in filters and filters['languages']:
            filtered_df = filtered_df[filtered_df['language'].isin(filters['languages'])]
        
        # Apply qualification filter
        if 'qualifications' in filters and filters['qualifications']:
            filtered_df = filtered_df[filtered_df['qualification_name'].isin(filters['qualifications'])]
        
        # Apply score range filter
        if 'score_min' in filters and 'score_max' in filters:
            filtered_df = filtered_df[
                (filtered_df['score'] >= filters['score_min']) & 
                (filtered_df['score'] <= filters['score_max'])
            ]
        
        # Apply review status filter
        if 'review_status' in filters:
            if filters['review_status'] == 'reviewed':
                filtered_df = filtered_df[filtered_df.index.isin(self.reviewed_items)]
            elif filters['review_status'] == 'not_reviewed':
                filtered_df = filtered_df[~filtered_df.index.isin(self.reviewed_items)]
        
        # Apply search filter
        if 'search_term' in filters and filters['search_term']:
            search_mask = filtered_df.astype(str).apply(
                lambda x: x.str.contains(filters['search_term'], case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[search_mask]
        
        return filtered_df
    
    def _save_reviewed_state(self) -> None:
        """Save reviewed items to session state."""
        # Convert set to list for JSON serialization
        if 'reviewed_items_json' not in st.session_state:
            st.session_state.reviewed_items_json = []
        st.session_state.reviewed_items_json = list(self.reviewed_items)
    
    def _load_reviewed_state(self) -> None:
        """Load reviewed items from session state."""
        if 'reviewed_items_json' in st.session_state:
            self.reviewed_items = set(st.session_state.reviewed_items_json)
        else:
            self.reviewed_items = set()
    
    def clear_reviewed_state(self) -> None:
        """Clear all reviewed items."""
        self.reviewed_items.clear()
        self._save_reviewed_state()
    
    def export_data_with_review_status(self, filtered_df: pd.DataFrame = None) -> pd.DataFrame:
        """Export data with review status included."""
        if filtered_df is not None:
            export_df = filtered_df.copy()
        else:
            export_df = self.data.copy() if self.data is not None else pd.DataFrame()
        
        if not export_df.empty:
            export_df['reviewed_status'] = export_df.index.isin(self.reviewed_items)
        
        return export_df
