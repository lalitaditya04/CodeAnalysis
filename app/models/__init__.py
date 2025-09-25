"""
Database models for the Code Quality Dashboard.
Enhanced with comprehensive metrics and multi-language support.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Repository(db.Model):
    """Repository model for storing GitHub repository information."""
    
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    github_url = db.Column(db.String(500), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), default='Unknown')
    scan_status = db.Column(db.String(20), default='pending')  # pending, scanning, completed, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_results = db.relationship('ScanResult', backref='repository', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert repository to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'github_url': self.github_url,
            'name': self.name,
            'language': self.language,
            'scan_status': self.scan_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'latest_scan': self.scan_results.order_by(ScanResult.scan_date.desc()).first().to_dict() if self.scan_results.first() else None
        }

class ScanResult(db.Model):
    """Enhanced scan result model with comprehensive metrics."""
    
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enhanced Lines of Code Analysis
    total_lines = db.Column(db.Integer, default=0)
    code_lines = db.Column(db.Integer, default=0)
    comment_lines = db.Column(db.Integer, default=0)
    blank_lines = db.Column(db.Integer, default=0)
    comment_ratio = db.Column(db.Float, default=0.0)
    documentation_quality = db.Column(db.String(20), default='Unknown')
    
    # Enhanced Complexity Analysis
    complexity_score = db.Column(db.Float, default=0.0)
    complexity_min = db.Column(db.Float, default=0.0)
    complexity_max = db.Column(db.Float, default=0.0)
    simple_functions = db.Column(db.Integer, default=0)
    moderate_functions = db.Column(db.Integer, default=0)
    complex_functions = db.Column(db.Integer, default=0)
    total_functions = db.Column(db.Integer, default=0)
    
    # Enhanced Technical Debt
    maintainability_index = db.Column(db.Float, default=0.0)
    duplication_percentage = db.Column(db.Float, default=0.0)
    technical_debt_minutes = db.Column(db.Integer, default=0)
    duplication_debt_minutes = db.Column(db.Integer, default=0)
    complexity_debt_minutes = db.Column(db.Integer, default=0)
    documentation_debt_minutes = db.Column(db.Integer, default=0)
    long_function_debt_minutes = db.Column(db.Integer, default=0)
    
    # Language Analysis
    primary_language = db.Column(db.String(50), default='Unknown')
    language_distribution = db.Column(db.Text, default='{}')  # JSON string
    files_analyzed = db.Column(db.Integer, default=0)
    
    # Relationships
    understanding_scores = db.relationship('UnderstandingScore', backref='scan_result', lazy='dynamic', cascade='all, delete-orphan')
    file_analyses = db.relationship('FileAnalysis', backref='scan_result', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert scan result to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'repository_id': self.repository_id,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            
            # Lines of Code
            'total_lines': self.total_lines,
            'code_lines': self.code_lines,
            'comment_lines': self.comment_lines,
            'blank_lines': self.blank_lines,
            'comment_ratio': self.comment_ratio,
            'documentation_quality': self.documentation_quality,
            
            # Complexity
            'complexity_score': self.complexity_score,
            'complexity_min': self.complexity_min,
            'complexity_max': self.complexity_max,
            'simple_functions': self.simple_functions,
            'moderate_functions': self.moderate_functions,
            'complex_functions': self.complex_functions,
            'total_functions': self.total_functions,
            
            # Technical Debt
            'maintainability_index': self.maintainability_index,
            'duplication_percentage': self.duplication_percentage,
            'technical_debt_minutes': self.technical_debt_minutes,
            'technical_debt_hours': round(self.technical_debt_minutes / 60, 1),
            'duplication_debt_minutes': self.duplication_debt_minutes,
            'complexity_debt_minutes': self.complexity_debt_minutes,
            'documentation_debt_minutes': self.documentation_debt_minutes,
            'long_function_debt_minutes': self.long_function_debt_minutes,
            
            # Language
            'primary_language': self.primary_language,
            'language_distribution': json.loads(self.language_distribution) if self.language_distribution else {},
            'files_analyzed': self.files_analyzed,
            
            # Calculated fields
            'complexity_category': self._get_complexity_category(),
            'maintainability_category': self._get_maintainability_category(),
            'duplication_category': self._get_duplication_category()
        }
    
    def _get_complexity_category(self):
        """Get complexity category based on README specifications."""
        if self.complexity_score <= 5:
            return 'Simple'
        elif self.complexity_score <= 10:
            return 'Moderate' 
        elif self.complexity_score <= 20:
            return 'Complex'
        else:
            return 'Very Complex'
    
    def _get_maintainability_category(self):
        """Get maintainability category based on MI score."""
        if self.maintainability_index >= 85:
            return 'Excellent'
        elif self.maintainability_index >= 70:
            return 'Good'
        elif self.maintainability_index >= 50:
            return 'Moderate'
        else:
            return 'Poor'
    
    def _get_duplication_category(self):
        """Get duplication category based on percentage."""
        if self.duplication_percentage <= 5:
            return 'Low'
        elif self.duplication_percentage <= 15:
            return 'Moderate'
        elif self.duplication_percentage <= 25:
            return 'High'
        else:
            return 'Very High'

class UnderstandingScore(db.Model):
    """Enhanced understanding score model with detailed breakdown."""
    
    __tablename__ = 'understanding_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_result_id = db.Column(db.Integer, db.ForeignKey('scan_results.id'), nullable=False)
    
    # Enhanced Understanding Metrics
    readability_score = db.Column(db.Integer, default=0)  # 0-100
    difficulty_level = db.Column(db.String(20), default='Unknown')  # Easy, Moderate, Challenging, Difficult
    
    # Scoring Breakdown
    base_score = db.Column(db.Integer, default=100)
    complexity_penalty = db.Column(db.Integer, default=0)
    duplication_penalty = db.Column(db.Integer, default=0)
    maintainability_bonus = db.Column(db.Integer, default=0)
    documentation_bonus = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert understanding score to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'scan_result_id': self.scan_result_id,
            'readability_score': self.readability_score,
            'difficulty_level': self.difficulty_level,
            'base_score': self.base_score,
            'complexity_penalty': self.complexity_penalty,
            'duplication_penalty': self.duplication_penalty,
            'maintainability_bonus': self.maintainability_bonus,
            'documentation_bonus': self.documentation_bonus,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'score_breakdown': {
                'base': self.base_score,
                'complexity_impact': -self.complexity_penalty,
                'duplication_impact': -self.duplication_penalty,
                'maintainability_impact': self.maintainability_bonus,
                'documentation_impact': self.documentation_bonus
            }
        }

class FileAnalysis(db.Model):
    """File-level analysis model with improvement prioritization."""
    
    __tablename__ = 'file_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_result_id = db.Column(db.Integer, db.ForeignKey('scan_results.id'), nullable=False)
    
    # File Information
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), default='Unknown')
    
    # File Metrics
    lines_of_code = db.Column(db.Integer, default=0)
    complexity_score = db.Column(db.Float, default=0.0)
    duplication_percentage = db.Column(db.Float, default=0.0)
    maintainability_index = db.Column(db.Float, default=0.0)
    function_count = db.Column(db.Integer, default=0)
    comment_ratio = db.Column(db.Float, default=0.0)
    
    # Improvement Priority
    improvement_priority = db.Column(db.String(20), default='Low')  # Low, Medium, High, Critical
    priority_score = db.Column(db.Float, default=0.0)  # 0-100
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    function_analyses = db.relationship('FunctionAnalysis', backref='file_analysis', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert file analysis to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'scan_result_id': self.scan_result_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'language': self.language,
            'lines_of_code': self.lines_of_code,
            'complexity_score': self.complexity_score,
            'duplication_percentage': self.duplication_percentage,
            'maintainability_index': self.maintainability_index,
            'function_count': self.function_count,
            'comment_ratio': self.comment_ratio,
            'improvement_priority': self.improvement_priority,
            'priority_score': self.priority_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self):
        """Generate improvement recommendations based on metrics."""
        recommendations = []
        
        if self.complexity_score > 15:
            recommendations.append("Consider breaking down complex functions into smaller, more manageable pieces")
        
        if self.duplication_percentage > 15:
            recommendations.append("Refactor duplicate code blocks to improve maintainability")
        
        if self.maintainability_index < 50:
            recommendations.append("Review and improve code structure and documentation")
        
        if self.comment_ratio < 5:
            recommendations.append("Add more documentation and comments to improve code readability")
        
        if self.lines_of_code > 500:
            recommendations.append("Consider splitting large file into smaller, focused modules")
        
        return recommendations

class FunctionAnalysis(db.Model):
    """Function-level analysis model for detailed code review."""
    
    __tablename__ = 'function_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    file_analysis_id = db.Column(db.Integer, db.ForeignKey('file_analyses.id'), nullable=False)
    
    # Function Information
    function_name = db.Column(db.String(200), nullable=False)
    line_number = db.Column(db.Integer, default=0)
    
    # Function Metrics
    complexity_score = db.Column(db.Float, default=0.0)
    lines_of_code = db.Column(db.Integer, default=0)
    parameter_count = db.Column(db.Integer, default=0)
    has_documentation = db.Column(db.Boolean, default=False)
    
    # Analysis Results
    complexity_category = db.Column(db.String(20), default='Simple')  # Simple, Moderate, Complex
    needs_refactoring = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert function analysis to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'file_analysis_id': self.file_analysis_id,
            'function_name': self.function_name,
            'line_number': self.line_number,
            'complexity_score': self.complexity_score,
            'lines_of_code': self.lines_of_code,
            'parameter_count': self.parameter_count,
            'has_documentation': self.has_documentation,
            'complexity_category': self.complexity_category,
            'needs_refactoring': self.needs_refactoring,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'improvement_suggestions': self._generate_improvement_suggestions()
        }
    
    def _generate_improvement_suggestions(self):
        """Generate specific improvement suggestions for the function."""
        suggestions = []
        
        if self.complexity_score > 15:
            suggestions.append("High complexity - consider breaking into smaller functions")
        
        if self.lines_of_code > 50:
            suggestions.append("Long function - consider splitting into multiple functions")
        
        if self.parameter_count > 5:
            suggestions.append("Too many parameters - consider using object parameters or builder pattern")
        
        if not self.has_documentation:
            suggestions.append("Add docstring to explain function purpose and parameters")
        
        if self.needs_refactoring:
            suggestions.append("Function identified for refactoring - review implementation")
        
        return suggestions