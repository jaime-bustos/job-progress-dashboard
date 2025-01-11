import pandas as pd
from typing import List, Dict
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans

class JobAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # capture single words and pairs
            min_df=2,  # ignore terms that appear in less than 2 documents
            max_df=0.9  # ignore terms that appear in more than 90% of documents
        )
        
    def get_job_title_column(self, df: pd.DataFrame) -> str:
        """Find the job title column in the dataframe."""
        title_columns = ['Job Title', 'JobTitle', 'Position', 'Title', 'Role', 'Job']
        for col in title_columns:
            if col in df.columns:
                return col
        return None

    def extract_common_roles(self, titles: List[str], n_clusters=5) -> Dict[str, int]:
        """Extract common role patterns from job titles using TF-IDF and clustering."""
        if not titles:
            return {}
            
        # clean and prepare titles
        cleaned_titles = [str(title).lower() for title in titles if pd.notna(title)]
        if not cleaned_titles:
            return {}

        try:
            # create TF-IDF matrix
            tfidf_matrix = self.vectorizer.fit_transform(cleaned_titles)
            
            # perform clustering to identify role groups
            kmeans = KMeans(n_clusters=min(n_clusters, len(cleaned_titles)), random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # get the most common terms in each cluster
            feature_names = self.vectorizer.get_feature_names_out()
            
            # define partial role terms that need a second word
            # these are terms that are common in job titles but not complete role names
            # you can add more terms here if your industry is different
            partial_role_terms = {
                # Tech roles
                'data', 'software', 'systems', 'cloud', 'web', 'it',
                # Business/Finance roles
                'financial', 'business', 'investment', 'finance', 'account',
                # Management/Admin roles
                'senior', 'junior', 'lead', 'project', 'product', 'program',
                # Academic/Research roles
                'research', 'teaching', 'academic', 'adjunct',
                # Creative roles
                'digital', 'content', 'creative', 'marketing',
                # General prefixes
                'associate', 'assistant', 'staff', 'principal'
            }
            
            cluster_terms = {}
            for i in range(kmeans.n_clusters):
                cluster_docs = tfidf_matrix[clusters == i]
                if cluster_docs.shape[0] > 0:
                    avg_tfidf = cluster_docs.mean(axis=0).A1
                    top_indices = avg_tfidf.argsort()[-3:][::-1]  # get top 3 terms
                    # only take the most significant term as the role name
                    top_term = feature_names[top_indices[0]]
                    # if it's a partial role name, try to combine with next term
                    if top_term in partial_role_terms:
                        next_term = feature_names[top_indices[1]]
                        top_term = f"{top_term} {next_term}"
                    cluster_terms[top_term] = (clusters == i).sum()
            
            return cluster_terms
            
        except Exception as e:
            print(f"Error in role extraction: {e}")
            return {}

    def analyze_job_trends(self, df: pd.DataFrame) -> List[str]:
        """Analyze job titles to identify trends and common roles."""
        
        # get job title column
        job_title_col = self.get_job_title_column(df)
        if job_title_col is None:
            return ["Job title analysis not available - Please ensure your Excel file has a column for job titles."]
        
        # get job titles
        job_titles = df[job_title_col].tolist()
        
        # extract common roles
        role_counts = self.extract_common_roles(job_titles)
        
        return self._generate_insights(role_counts, len(job_titles))

    def _generate_insights(self, role_counts: Dict[str, int], total_jobs: int) -> List[str]:
        """Generate insights based on role counts."""
        insights = []
        
        if not role_counts:
            return ["No clear role patterns detected in your job applications."]
            
        # sort roles by frequency
        sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
        
        # generate primary role insight
        primary_role = sorted_roles[0]
        primary_percentage = (primary_role[1] / total_jobs) * 100
        insights.append(
            f"Your job search is primarily focused on roles involving {primary_role[0]} "
            f"({primary_role[1]} applications, {primary_percentage:.1f}% of your search)."
        )
        
        # generate secondary roles insight
        if len(sorted_roles) > 1:
            secondary_roles = sorted_roles[1:3]  # get next 2 most common roles
            roles_text = " and ".join([
                f"{role} ({count} applications)" 
                for role, count in secondary_roles
            ])
            insights.append(f"You're also exploring roles involving {roles_text}.")
        
        # add trend analysis if enough data
        if total_jobs >= 10:
            diverse_search = len(role_counts) / total_jobs
            if diverse_search > 0.5:
                insights.append("Your job search appears quite diverse across different roles.")
            elif diverse_search < 0.2:
                insights.append("Your job search is very focused on specific role types.")
        
        return insights

    def get_role_distribution(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get the distribution of different roles as percentages."""
        job_title_col = self.get_job_title_column(df)
        if job_title_col is None:
            return {}
            
        job_titles = df[job_title_col].tolist()
        role_counts = self.extract_common_roles(job_titles)
        
        total = sum(role_counts.values())
        if total == 0:
            return {}
            
        return {role: (count/total)*100 for role, count in role_counts.items()}
