import os
import tempfile
import shutil
import subprocess
import math
from github import Github
from git import Repo
import logging
from radon.complexity import cc_visit
from radon.metrics import mi_visit
import pylint.lint
from pylint.reporters.text import TextReporter
from io import StringIO
import re
import json
import ast
from collections import Counter, defaultdict
from pathlib import Path

# Import the multi-language analyzer
try:
    from .multi_language_analyzer import MultiLanguageAnalyzer
except ImportError:
    try:
        from multi_language_analyzer import MultiLanguageAnalyzer
    except ImportError:
        from app.analysis.multi_language_analyzer import MultiLanguageAnalyzer

logger = logging.getLogger(__name__)

class CodeScanner:
    """Code analysis scanner for GitHub repositories."""
    
    def __init__(self):
        """Initialize the code scanner with GitHub token."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_client = None
        
        # Initialize multi-language analyzer
        self.multi_lang_analyzer = MultiLanguageAnalyzer()
        
        if self.github_token:
            self.github_client = Github(self.github_token)
    
    def analyze_repository(self, github_url):
        """
        Enhanced analysis of a GitHub repository for detailed code quality metrics.
        
        Args:
            github_url (str): GitHub repository URL
            
        Returns:
            dict: Comprehensive analysis results containing all metrics
        """
        try:
            # Extract owner and repo name from URL
            owner, repo_name = self._parse_github_url(github_url)
            
            # Clone repository to temporary directory
            temp_dir = self._clone_repository(github_url)
            
            if not temp_dir:
                return {'error': 'Failed to clone repository'}
            
            try:
                logger.info(f"Starting comprehensive analysis for {repo_name}")
                
                # Get repository information
                repo_info = self._get_repository_info(owner, repo_name)
                
                # Perform comprehensive analysis in order (some methods depend on others)
                
                # Step 1: Language Analysis (first to determine project type)
                language_results = self._analyze_language_distribution(temp_dir)
                self._cached_source_files = language_results.get('source_files', [])
                
                # Step 2: Enhanced Lines of Code Analysis
                lines_results = self._enhanced_lines_analysis(temp_dir)
                self._cached_total_lines = lines_results.get('total_lines', 0)
                
                # Step 3: Enhanced Complexity Analysis
                complexity_results = self._enhanced_complexity_analysis(temp_dir)
                self._cached_complex_functions = complexity_results.get('high_complexity_functions', [])
                
                # Step 4: Enhanced Maintainability Analysis
                maintainability_results = self._enhanced_maintainability_analysis(temp_dir)
                
                # Step 5: Enhanced Duplication Analysis
                duplication_results = self._enhanced_duplication_analysis(temp_dir)
                self._cached_duplication_pct = duplication_results.get('duplication_percentage', 0)
                
                # Step 6: Enhanced Technical Debt Calculation (depends on previous results)
                technical_debt_results = self._enhanced_technical_debt_analysis(temp_dir)
                
                # Step 7: File-Level Analysis
                file_analyses = self._analyze_files(temp_dir)
                
                # Step 8: Function-Level Analysis
                function_analyses = self._analyze_functions(temp_dir)
                
                # Combine all results
                analysis_results = {
                    **language_results,
                    **lines_results,
                    **complexity_results,
                    **maintainability_results,
                    **duplication_results,
                    **technical_debt_results,
                    'file_analyses': file_analyses,
                    'function_analyses': function_analyses
                }
                
                # Clean up cached data
                self._cleanup_cache()
                
                logger.info(f"Analysis completed for {repo_name}")
                return analysis_results
                
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Error analyzing repository {github_url}: {str(e)}")
            return {'error': str(e)}
    
    def analyze_complexity_for_language(self, repo_path, primary_language):
        """
        Analyze complexity for specific programming language using multi-language analyzer.
        
        Args:
            repo_path (str): Path to the repository
            primary_language (str): Primary programming language detected
            
        Returns:
            dict: Language-specific complexity and maintainability metrics
        """
        try:
            logger.info(f"Starting {primary_language} complexity analysis")
            
            # Use the multi-language analyzer
            result = self.multi_lang_analyzer.analyze_complexity_for_language(repo_path, primary_language)
            
            logger.info(f"Completed {primary_language} analysis using: {result.get('analysis_method', 'unknown method')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-language complexity analysis: {str(e)}")
            return self.multi_lang_analyzer.get_default_result(primary_language)
    
    def detect_primary_language(self, repo_path):
        """
        Detect the primary programming language in the repository.
        
        Args:
            repo_path (str): Path to the repository
            
        Returns:
            str: Primary programming language
        """
        try:
            # If we have a cloned repo, analyze the files
            if os.path.exists(repo_path) and os.path.isdir(repo_path):
                return self._analyze_language_distribution(repo_path).get('primary_language', 'Unknown')
            else:
                # If it's a GitHub URL, we need to clone it first
                if repo_path.startswith(('http', 'git')):
                    temp_dir = self._clone_repository(repo_path)
                    if temp_dir:
                        try:
                            primary_lang = self._analyze_language_distribution(temp_dir).get('primary_language', 'Unknown')
                            return primary_lang
                        finally:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                
                return 'Unknown'
                
        except Exception as e:
            logger.error(f"Error detecting primary language: {str(e)}")
            return 'Unknown'
    
    def _parse_github_url(self, github_url):
        """Extract owner and repository name from GitHub URL."""
        # Remove .git suffix if present
        url = github_url.rstrip('/').replace('.git', '')
        
        # Extract from URL like: https://github.com/owner/repo
        parts = url.split('/')
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        
        raise ValueError("Invalid GitHub URL format")
    
    def _clone_repository(self, github_url):
        """Clone repository to temporary directory."""
        try:
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Cloning repository to {temp_dir}")
            
            # Clone with depth 1 for faster cloning
            Repo.clone_from(github_url, temp_dir, depth=1)
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return None
    
    def _get_repository_info(self, owner, repo_name):
        """Get repository information from GitHub API."""
        try:
            if not self.github_client:
                return {'language': 'Unknown'}
            
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            return {
                'language': repo.language or 'Unknown',
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count
            }
            
        except Exception as e:
            logger.warning(f"Could not fetch repository info: {str(e)}")
            return {'language': 'Unknown'}
    
    def _enhanced_lines_analysis(self, repo_path):
        """Enhanced lines of code analysis with ratios and quality assessment."""
        try:
            total_lines = 0
            code_lines = 0
            comment_lines = 0
            blank_lines = 0
            
            # Use source files from language analysis if available
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for line in lines:
                        total_lines += 1
                        stripped_line = line.strip()
                        
                        if not stripped_line:
                            blank_lines += 1
                        elif self._is_comment_line(stripped_line, file_path):
                            comment_lines += 1
                        else:
                            code_lines += 1
                            
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {str(e)}")
                    continue
            
            # Calculate ratios and percentages
            comment_ratio = (comment_lines / max(total_lines, 1)) * 100
            code_percentage = (code_lines / max(total_lines, 1)) * 100
            comment_percentage = (comment_lines / max(total_lines, 1)) * 100
            blank_percentage = (blank_lines / max(total_lines, 1)) * 100
            
            # Determine documentation quality
            documentation_quality = self._assess_documentation_quality(comment_ratio, code_lines)
            
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'comment_ratio': round(comment_ratio, 1),
                'code_percentage': round(code_percentage, 1),
                'comment_percentage': round(comment_percentage, 1),
                'blank_percentage': round(blank_percentage, 1),
                'documentation_quality': documentation_quality
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced lines analysis: {str(e)}")
            return {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'comment_ratio': 0.0,
                'code_percentage': 0.0,
                'comment_percentage': 0.0,
                'blank_percentage': 0.0,
                'documentation_quality': 'Unknown'
            }

    def _assess_documentation_quality(self, comment_ratio, code_lines):
        """Assess documentation quality based on comment ratio and codebase size."""
        if code_lines < 100:  # Small codebase
            if comment_ratio >= 15:
                return 'Excellent'
            elif comment_ratio >= 8:
                return 'Good'
            elif comment_ratio >= 3:
                return 'Fair'
            else:
                return 'Poor'
        else:  # Larger codebase
            if comment_ratio >= 20:
                return 'Excellent'
            elif comment_ratio >= 12:
                return 'Good'
            elif comment_ratio >= 6:
                return 'Fair'
            else:
                return 'Poor'
    
    def _analyze_language_distribution(self, repo_path):
        """Enhanced language detection based on code volume, not file count."""
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JavaScript',
            '.tsx': 'TypeScript', '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cc': 'C++',
            '.cxx': 'C++', '.h': 'C/C++', '.hpp': 'C++', '.cs': 'C#', '.rb': 'Ruby',
            '.go': 'Go', '.rs': 'Rust', '.php': 'PHP', '.swift': 'Swift', '.kt': 'Kotlin',
            '.scala': 'Scala', '.m': 'Objective-C', '.mm': 'Objective-C++', '.r': 'R',
            '.R': 'R', '.pl': 'Perl', '.sh': 'Shell', '.bash': 'Shell', '.ps1': 'PowerShell',
            '.lua': 'Lua', '.dart': 'Dart', '.vue': 'Vue.js', '.svelte': 'Svelte'
        }
        
        # Config/markup files to exclude from primary language detection
        exclude_extensions = {'.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
                            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.md',
                            '.txt', '.log', '.gitignore', '.dockerignore'}
        
        language_lines = Counter()
        total_files = 0
        source_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'vendor', 'build', 'dist',
                'target', 'bin', 'obj', 'deps', '_build', '.git', '.svn'
            }]
            
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                
                # Only count source code files
                if ext_lower in language_map and ext_lower not in exclude_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len([line for line in f if line.strip()])
                        
                        language = language_map[ext_lower]
                        language_lines[language] += lines
                        source_files.append(file_path)
                        total_files += 1
                        
                    except Exception as e:
                        logger.warning(f"Could not read file {file_path}: {str(e)}")
                        continue
        
        # Calculate primary language and distribution
        total_code_lines = sum(language_lines.values())
        if total_code_lines == 0:
            return {
                'primary_language': 'Unknown',
                'language_distribution': '{}',
                'files_analyzed': 0
            }
        
        # Calculate percentages and find primary language
        language_distribution = {}
        primary_language = language_lines.most_common(1)[0][0] if language_lines else 'Unknown'
        
        for language, lines in language_lines.items():
            percentage = (lines / total_code_lines) * 100
            language_distribution[language] = {
                'lines': lines,
                'percentage': round(percentage, 1)
            }
        
        return {
            'primary_language': primary_language,
            'language_distribution': json.dumps(language_distribution),
            'files_analyzed': total_files,
            'source_files': source_files  # For use in other analysis methods
        }

    def _find_source_files(self, repo_path):
        """Find all source code files in the repository."""
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
            '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala',
            '.m', '.mm', '.r', '.R', '.pl', '.sh', '.bash', '.ps1', '.lua', '.dart',
            '.vue', '.svelte', '.elm', '.clj', '.cljs', '.ex', '.exs', '.fs', '.fsx',
            '.ml', '.mli', '.hs', '.lhs', '.pas', '.pp', '.inc', '.asm', '.s'
        }
        
        source_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'vendor', 'build', 'dist',
                'target', 'bin', 'obj', 'deps', '_build'
            }]
            
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in source_extensions:
                    source_files.append(file_path)
        
        return source_files
    
    def _is_comment_line(self, line, file_path):
        """Check if a line is a comment based on file extension."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Python, Ruby, Shell, R
        if ext in {'.py', '.rb', '.sh', '.bash', '.r', '.pl'}:
            return line.startswith('#')
        
        # JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Swift, Kotlin, Scala
        elif ext in {'.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx', 
                    '.h', '.hpp', '.cs', '.go', '.rs', '.swift', '.kt', '.scala'}:
            return line.startswith('//') or line.startswith('/*') or line.startswith('*')
        
        # PHP
        elif ext == '.php':
            return line.startswith('//') or line.startswith('#') or line.startswith('/*')
        
        # Lua
        elif ext == '.lua':
            return line.startswith('--')
        
        # Default
        return False
    
    def _enhanced_complexity_analysis(self, repo_path):
        """Enhanced cyclomatic complexity analysis with distribution and categorization."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            python_files = [f for f in source_files if f.endswith('.py')]
            
            if not python_files:
                return {
                    'complexity_score': 0.0,
                    'complexity_min': 0.0,
                    'complexity_max': 0.0,
                    'simple_functions': 0,
                    'moderate_functions': 0,
                    'complex_functions': 0,
                    'total_functions': 0,
                    'high_complexity_functions': []
                }
            
            all_complexities = []
            function_details = []
            simple_count = moderate_count = complex_count = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    # Calculate complexity using Radon
                    complexity_data = cc_visit(code)
                    
                    for item in complexity_data:
                        complexity = item.complexity
                        all_complexities.append(complexity)
                        
                        # Categorize by complexity
                        if complexity <= 5:
                            simple_count += 1
                            category = 'Simple'
                        elif complexity <= 10:
                            moderate_count += 1
                            category = 'Moderate'
                        else:
                            complex_count += 1
                            category = 'Complex'
                        
                        # Store function details for high complexity functions
                        if complexity > 10:
                            function_details.append({
                                'name': item.name,
                                'complexity': complexity,
                                'file': os.path.basename(file_path),
                                'line': item.lineno,
                                'category': category
                            })
                            
                except Exception as e:
                    logger.warning(f"Could not analyze complexity for {file_path}: {str(e)}")
                    continue
            
            total_functions = len(all_complexities)
            if total_functions == 0:
                return {
                    'complexity_score': 0.0,
                    'complexity_min': 0.0,
                    'complexity_max': 0.0,
                    'simple_functions': 0,
                    'moderate_functions': 0,
                    'complex_functions': 0,
                    'total_functions': 0,
                    'high_complexity_functions': []
                }
            
            avg_complexity = sum(all_complexities) / total_functions
            min_complexity = min(all_complexities)
            max_complexity = max(all_complexities)
            
            # Sort high complexity functions by complexity (descending)
            high_complexity_functions = sorted(function_details, 
                                             key=lambda x: x['complexity'], 
                                             reverse=True)[:10]  # Top 10 most complex
            
            return {
                'complexity_score': round(avg_complexity, 1),
                'complexity_min': round(min_complexity, 1),
                'complexity_max': round(max_complexity, 1),
                'simple_functions': simple_count,
                'moderate_functions': moderate_count,
                'complex_functions': complex_count,
                'total_functions': total_functions,
                'high_complexity_functions': high_complexity_functions
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced complexity analysis: {str(e)}")
            return {
                'complexity_score': 0.0,
                'complexity_min': 0.0,
                'complexity_max': 0.0,
                'simple_functions': 0,
                'moderate_functions': 0,
                'complex_functions': 0,
                'total_functions': 0,
                'high_complexity_functions': []
            }
    
    def _enhanced_maintainability_analysis(self, repo_path):
        """Enhanced maintainability analysis with detailed breakdown."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            python_files = [f for f in source_files if f.endswith('.py')]
            
            if not python_files:
                return {'maintainability_index': 0.0}
            
            mi_scores = []
            file_scores = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    # Calculate maintainability index using Radon
                    mi_data = mi_visit(code, multi=True)
                    
                    if mi_data is not None:
                        mi_scores.append(mi_data)
                        file_scores.append({
                            'file': os.path.basename(file_path),
                            'mi_score': round(mi_data, 1)
                        })
                    
                except Exception as e:
                    logger.warning(f"Could not analyze maintainability for {file_path}: {str(e)}")
                    continue
            
            if not mi_scores:
                return {'maintainability_index': 0.0}
            
            avg_mi = sum(mi_scores) / len(mi_scores)
            
            # Identify files that need attention (MI < 50)
            low_maintainability_files = [
                f for f in file_scores if f['mi_score'] < 50
            ]
            low_maintainability_files.sort(key=lambda x: x['mi_score'])
            
            return {
                'maintainability_index': round(avg_mi, 1),
                'low_maintainability_files': low_maintainability_files[:5]  # Top 5 worst files
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced maintainability analysis: {str(e)}")
            return {'maintainability_index': 0.0}
    
    def _enhanced_duplication_analysis(self, repo_path):
        """Enhanced duplication analysis with block detection and file tracking."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            
            if not source_files:
                return {'duplication_percentage': 0.0, 'duplicate_blocks': []}
            
            # Track line hashes and their locations
            line_locations = defaultdict(list)
            total_meaningful_lines = 0
            duplicate_lines = 0
            file_duplication = {}
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    file_duplicates = 0
                    file_total = 0
                    
                    for line_num, line in enumerate(lines, 1):
                        stripped_line = line.strip()
                        
                        # Only consider meaningful lines (not comments, not too short)
                        if (len(stripped_line) > 15 and 
                            not self._is_comment_line(stripped_line, file_path) and
                            not stripped_line.startswith(('import ', 'from ', '#', '//', '/*'))):
                            
                            total_meaningful_lines += 1
                            file_total += 1
                            line_hash = hash(stripped_line)
                            
                            location_info = {
                                'file': os.path.basename(file_path),
                                'line': line_num,
                                'content': stripped_line[:50] + '...' if len(stripped_line) > 50 else stripped_line
                            }
                            
                            if line_hash in line_locations:
                                duplicate_lines += 1
                                file_duplicates += 1
                                line_locations[line_hash].append(location_info)
                            else:
                                line_locations[line_hash] = [location_info]
                    
                    # Calculate file-level duplication percentage
                    if file_total > 0:
                        file_dup_pct = (file_duplicates / file_total) * 100
                        file_duplication[os.path.basename(file_path)] = round(file_dup_pct, 1)
                    
                except Exception as e:
                    logger.warning(f"Could not analyze duplication for {file_path}: {str(e)}")
                    continue
            
            # Find actual duplicate blocks (lines that appear in multiple locations)
            duplicate_blocks = []
            for line_hash, locations in line_locations.items():
                if len(locations) > 1:  # Appears in multiple places
                    duplicate_blocks.append({
                        'content': locations[0]['content'],
                        'occurrences': len(locations),
                        'locations': locations[:5]  # Show max 5 locations
                    })
            
            # Sort by most frequent duplicates
            duplicate_blocks.sort(key=lambda x: x['occurrences'], reverse=True)
            
            duplication_pct = (duplicate_lines / max(total_meaningful_lines, 1)) * 100
            
            # Find files with highest duplication
            high_duplication_files = sorted(
                [(file, pct) for file, pct in file_duplication.items() if pct > 15],
                key=lambda x: x[1], reverse=True
            )[:5]
            
            return {
                'duplication_percentage': round(duplication_pct, 1),
                'duplicate_blocks': duplicate_blocks[:10],  # Top 10 most duplicated blocks
                'high_duplication_files': high_duplication_files,
                'files_with_duplication': len([f for f in file_duplication.values() if f > 5])
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced duplication analysis: {str(e)}")
            return {'duplication_percentage': 0.0, 'duplicate_blocks': []}
    
    def _enhanced_technical_debt_analysis(self, repo_path):
        """Enhanced technical debt calculation with detailed breakdown."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            
            # Initialize debt components
            duplication_debt = 0
            complexity_debt = 0
            documentation_debt = 0
            long_function_debt = 0
            
            # Get data from previous analyses (stored in instance variables during analysis)
            duplication_pct = getattr(self, '_cached_duplication_pct', 0)
            total_lines = getattr(self, '_cached_total_lines', 0)
            complex_functions = getattr(self, '_cached_complex_functions', [])
            
            # Calculate duplication debt
            # Formula: Duplication % × Total Lines × 0.5 minutes per line
            if hasattr(self, '_cached_duplication_pct') and hasattr(self, '_cached_total_lines'):
                duplication_debt = int((duplication_pct / 100) * total_lines * 0.5)
            
            # Calculate complexity debt
            # Formula: Complex Functions × 15 minutes each
            if hasattr(self, '_cached_complex_functions'):
                complexity_debt = len(complex_functions) * 15
            
            # Calculate documentation and long function debt by analyzing files
            python_files = [f for f in source_files if f.endswith('.py')]
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    # Parse AST to analyze functions
                    try:
                        tree = ast.parse(code)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                # Check function length
                                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                                    func_length = node.end_lineno - node.lineno
                                    if func_length > 50:  # Long function threshold
                                        long_function_debt += 10  # 10 minutes per long function
                                
                                # Check documentation
                                has_docstring = (ast.get_docstring(node) is not None)
                                if not has_docstring:
                                    documentation_debt += 5  # 5 minutes per undocumented function
                                    
                    except SyntaxError:
                        # Skip files with syntax errors
                        continue
                        
                except Exception as e:
                    logger.warning(f"Could not analyze technical debt for {file_path}: {str(e)}")
                    continue
            
            # Calculate additional debt from code quality issues
            quality_debt = 0
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line in lines:
                        line_stripped = line.strip()
                        # Check for common code smells
                        if len(line_stripped) > 120:  # Very long lines
                            quality_debt += 1
                        if line_stripped.count('    ') > 6:  # Very deep nesting
                            quality_debt += 2
                        if 'TODO' in line_stripped or 'FIXME' in line_stripped:  # Explicit technical debt
                            quality_debt += 3
                            
                except Exception:
                    continue
            
            # Convert quality issues to minutes (1 minute per issue)
            quality_debt_minutes = quality_debt
            
            # Total technical debt
            total_debt = duplication_debt + complexity_debt + documentation_debt + long_function_debt + quality_debt_minutes
            
            return {
                'technical_debt_minutes': total_debt,
                'duplication_debt_minutes': duplication_debt,
                'complexity_debt_minutes': complexity_debt,
                'documentation_debt_minutes': documentation_debt,
                'long_function_debt_minutes': long_function_debt,
                'quality_debt_minutes': quality_debt_minutes,
                'debt_breakdown': {
                    'duplication': duplication_debt,
                    'complexity': complexity_debt,
                    'documentation': documentation_debt,
                    'long_functions': long_function_debt,
                    'quality_issues': quality_debt_minutes
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced technical debt analysis: {str(e)}")
            return {
                'technical_debt_minutes': 0,
                'duplication_debt_minutes': 0,
                'complexity_debt_minutes': 0,
                'documentation_debt_minutes': 0,
                'long_function_debt_minutes': 0,
                'quality_debt_minutes': 0,
                'debt_breakdown': {}
            }

    def _analyze_files(self, repo_path):
        """Analyze individual files and rank them by improvement priority."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            file_analyses = []
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Get file extension for language detection
                    _, ext = os.path.splitext(file_path)
                    language = self._get_language_from_extension(ext)
                    
                    # Analyze file metrics
                    file_metrics = self._analyze_single_file(file_path, content, language)
                    
                    # Calculate improvement priority score
                    priority_score = self._calculate_file_priority_score(file_metrics)
                    priority_level = self._get_priority_level(priority_score)
                    
                    file_analysis = {
                        'file_path': os.path.relpath(file_path, repo_path),
                        'file_name': os.path.basename(file_path),
                        'language': language,
                        'lines_of_code': file_metrics['lines_of_code'],
                        'complexity_score': file_metrics['complexity_score'],
                        'duplication_percentage': file_metrics['duplication_percentage'],
                        'maintainability_index': file_metrics['maintainability_index'],
                        'function_count': file_metrics['function_count'],
                        'comment_ratio': file_metrics['comment_ratio'],
                        'improvement_priority': priority_level,
                        'priority_score': priority_score
                    }
                    
                    file_analyses.append(file_analysis)
                    
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {str(e)}")
                    continue
            
            # Sort by priority score (highest first - most need attention)
            file_analyses.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return file_analyses[:20]  # Return top 20 files needing attention
            
        except Exception as e:
            logger.error(f"Error analyzing files: {str(e)}")
            return []

    def _analyze_functions(self, repo_path):
        """Analyze individual functions and identify problematic ones."""
        try:
            source_files = getattr(self, '_cached_source_files', None) or self._find_source_files(repo_path)
            python_files = [f for f in source_files if f.endswith('.py')]
            function_analyses = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Parse AST to extract functions
                    tree = ast.parse(content)
                    
                    # Also get complexity data from Radon
                    complexity_data = cc_visit(content)
                    complexity_map = {item.name: item.complexity for item in complexity_data}
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_name = node.name
                            line_number = node.lineno
                            
                            # Calculate function metrics
                            func_length = getattr(node, 'end_lineno', node.lineno) - node.lineno
                            param_count = len(node.args.args)
                            has_docstring = ast.get_docstring(node) is not None
                            complexity = complexity_map.get(func_name, 1)
                            
                            # Categorize complexity
                            if complexity <= 5:
                                complexity_category = 'Simple'
                                needs_refactoring = False
                            elif complexity <= 10:
                                complexity_category = 'Moderate'
                                needs_refactoring = False
                            else:
                                complexity_category = 'Complex'
                                needs_refactoring = True
                            
                            # Flag long functions for refactoring too
                            if func_length > 50:
                                needs_refactoring = True
                            
                            function_analysis = {
                                'file_path': os.path.relpath(file_path, repo_path),
                                'function_name': func_name,
                                'line_number': line_number,
                                'complexity_score': complexity,
                                'lines_of_code': func_length,
                                'parameter_count': param_count,
                                'has_documentation': has_docstring,
                                'complexity_category': complexity_category,
                                'needs_refactoring': needs_refactoring
                            }
                            
                            # Only store functions that need attention
                            if needs_refactoring or complexity > 8 or not has_docstring or func_length > 30:
                                function_analyses.append(function_analysis)
                    
                except (SyntaxError, Exception) as e:
                    logger.warning(f"Could not analyze functions in {file_path}: {str(e)}")
                    continue
            
            # Sort by complexity (highest first)
            function_analyses.sort(key=lambda x: x['complexity_score'], reverse=True)
            
            return function_analyses[:50]  # Return top 50 functions needing attention
            
        except Exception as e:
            logger.error(f"Error analyzing functions: {str(e)}")
            return []

    def _analyze_single_file(self, file_path, content, language):
        """Analyze metrics for a single file."""
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Count different types of lines
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif self._is_comment_line(stripped, file_path):
                comment_lines += 1
            else:
                code_lines += 1
        
        # Calculate complexity for Python files
        complexity_score = 0.0
        maintainability_index = 100.0
        function_count = 0
        
        if language == 'Python':
            try:
                complexity_data = cc_visit(content)
                if complexity_data:
                    complexities = [item.complexity for item in complexity_data]
                    complexity_score = sum(complexities) / len(complexities)
                    function_count = len(complexities)
                
                # Calculate maintainability index
                mi_data = mi_visit(content, multi=True)
                if mi_data is not None:
                    maintainability_index = mi_data
                    
            except Exception:
                pass
        
        # Simple duplication check within the file
        line_hashes = set()
        duplicate_lines = 0
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 15 and not self._is_comment_line(stripped, file_path):
                line_hash = hash(stripped)
                if line_hash in line_hashes:
                    duplicate_lines += 1
                else:
                    line_hashes.add(line_hash)
        
        duplication_pct = (duplicate_lines / max(code_lines, 1)) * 100
        comment_ratio = (comment_lines / max(total_lines, 1)) * 100
        
        return {
            'lines_of_code': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'complexity_score': round(complexity_score, 1),
            'maintainability_index': round(maintainability_index, 1),
            'duplication_percentage': round(duplication_pct, 1),
            'function_count': function_count,
            'comment_ratio': round(comment_ratio, 1)
        }

    def _calculate_file_priority_score(self, metrics):
        """Calculate priority score for file improvement (0-100, higher = more urgent)."""
        score = 0
        
        # High complexity penalty
        if metrics['complexity_score'] > 15:
            score += 30
        elif metrics['complexity_score'] > 10:
            score += 20
        elif metrics['complexity_score'] > 5:
            score += 10
        
        # Low maintainability penalty
        if metrics['maintainability_index'] < 30:
            score += 25
        elif metrics['maintainability_index'] < 50:
            score += 15
        elif metrics['maintainability_index'] < 70:
            score += 5
        
        # High duplication penalty
        if metrics['duplication_percentage'] > 30:
            score += 20
        elif metrics['duplication_percentage'] > 15:
            score += 10
        elif metrics['duplication_percentage'] > 5:
            score += 5
        
        # Poor documentation penalty
        if metrics['comment_ratio'] < 3:
            score += 10
        elif metrics['comment_ratio'] < 8:
            score += 5
        
        # Large file penalty (harder to maintain)
        if metrics['lines_of_code'] > 500:
            score += 10
        elif metrics['lines_of_code'] > 300:
            score += 5
        
        return min(100, score)

    def _get_priority_level(self, score):
        """Convert priority score to priority level."""
        if score >= 70:
            return 'Critical'
        elif score >= 50:
            return 'High'
        elif score >= 25:
            return 'Medium'
        else:
            return 'Low'

    def _get_language_from_extension(self, ext):
        """Get programming language from file extension."""
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', 
            '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cs': 'C#',
            '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
            '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala'
        }
        return language_map.get(ext.lower(), 'Unknown')

    def _cleanup_cache(self):
        """Clean up cached analysis data."""
        for attr in ['_cached_source_files', '_cached_total_lines', '_cached_complex_functions', '_cached_duplication_pct']:
            if hasattr(self, attr):
                delattr(self, attr)
    
    def calculate_understanding_score(self, metrics):
        """
        Understanding Score Algorithm as per README specifications.
        Multi-factor scoring (0-100 scale) with weighted components.
        
        Args:
            metrics (dict): Dictionary containing all analysis metrics
                          
        Returns:
            dict: Score, difficulty level, and scoring breakdown
        """
        try:
            # Extract metrics with defaults
            complexity = metrics.get('complexity_score', 0)
            maintainability = metrics.get('maintainability_index', 100)
            duplication = metrics.get('duplication_percentage', 0)
            tech_debt_hours = (metrics.get('technical_debt_minutes', 0) / 60)
            comment_ratio = metrics.get('comment_ratio', 0)
            
            # Start with base score
            base_score = 100
            
            # Complexity penalty (30% weight) - README specification
            complexity_penalty = 0
            if complexity > 20:
                complexity_penalty = 30
            elif complexity > 15:
                complexity_penalty = 20
            elif complexity > 10:
                complexity_penalty = 15
            
            # Maintainability impact (25% weight) - README specification
            maintainability_adjustment = 0
            if maintainability < 30:
                maintainability_adjustment = -25
            elif maintainability < 50:
                maintainability_adjustment = -18
            elif maintainability > 85:
                maintainability_adjustment = 5
            
            # Duplication penalty (20% weight) - README specification
            duplication_penalty = 0
            if duplication > 25:
                duplication_penalty = 25
            elif duplication > 15:
                duplication_penalty = 18
            elif duplication > 5:
                duplication_penalty = 10
            
            # Technical debt penalty (15% weight) - README specification
            tech_debt_penalty = 0
            if tech_debt_hours > 4:
                tech_debt_penalty = 15
            elif tech_debt_hours > 2:
                tech_debt_penalty = 10
            elif tech_debt_hours > 1:
                tech_debt_penalty = 5
            
            # Documentation impact (10% weight) - README specification
            documentation_adjustment = 0
            if comment_ratio < 3:
                documentation_adjustment = -10
            elif comment_ratio > 15:
                documentation_adjustment = 3
            elif comment_ratio > 8:
                documentation_adjustment = 1
            
            # Calculate final score as per README formula
            final_score = (base_score - complexity_penalty + maintainability_adjustment 
                          - duplication_penalty - tech_debt_penalty + documentation_adjustment)
            
            # Ensure score stays in valid range (0-100)
            final_score = max(0, min(100, final_score))
            
            # Determine difficulty level - README categories
            if final_score >= 85:
                level = 'Easy'
            elif final_score >= 65:
                level = 'Moderate' 
            elif final_score >= 40:
                level = 'Challenging'
            else:
                level = 'Difficult'
            
            # Separate positive and negative adjustments for cleaner display
            maintainability_bonus = max(0, maintainability_adjustment)
            maintainability_penalty = abs(min(0, maintainability_adjustment))
            documentation_bonus = max(0, documentation_adjustment)
            documentation_penalty = abs(min(0, documentation_adjustment))
            
            return {
                'score': int(final_score),
                'level': level,
                'base_score': base_score,
                'complexity_penalty': complexity_penalty,
                'duplication_penalty': duplication_penalty,
                'maintainability_bonus': maintainability_bonus,
                'documentation_bonus': documentation_bonus,
                'maintainability_penalty': maintainability_penalty,
                'documentation_penalty': documentation_penalty,
                'tech_debt_penalty': tech_debt_penalty,
                'scoring_details': {
                    'complexity': f"Avg {complexity:.1f} → -{complexity_penalty} pts (30% weight)",
                    'maintainability': f"MI {maintainability:.1f} → {maintainability_adjustment:+d} pts (25% weight)",
                    'duplication': f"{duplication:.1f}% → -{duplication_penalty} pts (20% weight)",
                    'technical_debt': f"{tech_debt_hours:.1f}h → -{tech_debt_penalty} pts (15% weight)",
                    'documentation': f"{comment_ratio:.1f}% → {documentation_adjustment:+d} pts (10% weight)"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating understanding score: {str(e)}")
            return {
                'score': 0, 
                'level': 'Difficult',
                'base_score': 100,
                'complexity_penalty': 0,
                'duplication_penalty': 0,
                'maintainability_bonus': 0,
                'documentation_bonus': 0,
                'tech_debt_penalty': 0,
                'scoring_details': {}
            }

    def _calculate_complexity_penalty(self, avg_complexity):
        """Calculate penalty based on average complexity."""
        if avg_complexity > 20:
            return 35  # Very high complexity
        elif avg_complexity > 15:
            return 25  # High complexity
        elif avg_complexity > 10:
            return 15  # Moderate-high complexity
        elif avg_complexity > 5:
            return 5   # Slightly above ideal
        else:
            return 0   # Good complexity

    def _calculate_duplication_penalty(self, duplication_pct):
        """Calculate penalty based on code duplication percentage."""
        if duplication_pct > 25:
            return 30  # Very high duplication
        elif duplication_pct > 20:
            return 25  # High duplication
        elif duplication_pct > 15:
            return 20  # Moderate-high duplication
        elif duplication_pct > 10:
            return 10  # Some duplication
        elif duplication_pct > 5:
            return 5   # Low duplication
        else:
            return 0   # Minimal duplication

    def _calculate_maintainability_bonus(self, maintainability_index):
        """Calculate bonus/penalty based on maintainability index."""
        if maintainability_index >= 85:
            return 10  # Excellent maintainability
        elif maintainability_index >= 70:
            return 5   # Good maintainability
        elif maintainability_index >= 50:
            return 0   # Average maintainability
        elif maintainability_index >= 30:
            return -10 # Below average (penalty)
        else:
            return -20 # Poor maintainability (penalty)

    def _calculate_documentation_bonus(self, comment_ratio):
        """Calculate bonus/penalty based on documentation quality."""
        if comment_ratio >= 25:
            return -5  # Too many comments (might indicate complex code)
        elif comment_ratio >= 15:
            return 8   # Excellent documentation
        elif comment_ratio >= 10:
            return 5   # Good documentation
        elif comment_ratio >= 5:
            return 2   # Adequate documentation
        elif comment_ratio >= 2:
            return -3  # Poor documentation (penalty)
        else:
            return -8  # Very poor documentation (penalty)

    def _calculate_tech_debt_penalty(self, tech_debt_minutes):
        """Calculate penalty based on technical debt."""
        if tech_debt_minutes > 240:  # > 4 hours
            return 25
        elif tech_debt_minutes > 120:  # > 2 hours
            return 15
        elif tech_debt_minutes > 60:   # > 1 hour
            return 8
        elif tech_debt_minutes > 30:   # > 30 minutes
            return 3
        else:
            return 0
    
    def _get_language_complexity_thresholds(self, language):
        """
        Get language-specific complexity thresholds as per README specifications.
        
        Returns:
            dict: Thresholds for simple, moderate, and complex categories
        """
        # README-based complexity thresholds by language
        thresholds = {
            'Python': {'simple': 5, 'moderate': 10, 'complex': 15},
            'JavaScript': {'simple': 6, 'moderate': 12, 'complex': 20},
            'TypeScript': {'simple': 6, 'moderate': 12, 'complex': 20},
            'Java': {'simple': 4, 'moderate': 8, 'complex': 12},
            'C': {'simple': 5, 'moderate': 10, 'complex': 15},
            'C++': {'simple': 5, 'moderate': 10, 'complex': 15},
            'C#': {'simple': 4, 'moderate': 8, 'complex': 12},
            'Go': {'simple': 5, 'moderate': 10, 'complex': 15},
            'Rust': {'simple': 4, 'moderate': 8, 'complex': 12},
            'PHP': {'simple': 6, 'moderate': 12, 'complex': 18},
            'Ruby': {'simple': 6, 'moderate': 12, 'complex': 18},
        }
        
        # Default thresholds for unknown languages
        default = {'simple': 5, 'moderate': 10, 'complex': 15}
        
        return thresholds.get(language, default)
    
    def _calculate_halstead_metrics(self, file_content, language='python'):
        """
        Calculate basic Halstead metrics as mentioned in README.
        
        Args:
            file_content (str): Source code content
            language (str): Programming language
            
        Returns:
            dict: Basic Halstead metrics for maintainability calculation
        """
        try:
            if not file_content.strip():
                return {'volume': 0, 'difficulty': 1, 'effort': 0}
                
            # Define operators and operands based on language
            operators = {
                'python': ['+', '-', '*', '/', '//', '%', '**', '==', '!=', '<', '>', '<=', '>=', 
                          'and', 'or', 'not', 'in', 'is', '=', '+=', '-=', '*=', '/='],
                'javascript': ['+', '-', '*', '/', '%', '==', '===', '!=', '!==', '<', '>', '<=', '>=',
                              '&&', '||', '!', '=', '+=', '-=', '*=', '/='],
                'java': ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!',
                        '=', '+=', '-=', '*=', '/=']
            }
            
            # Get language-specific operators or default to Python
            lang_operators = operators.get(language.lower(), operators['python'])
            
            # Count operators and operands (simplified approach)
            operator_count = 0
            unique_operators = set()
            
            for op in lang_operators:
                count = file_content.count(op)
                if count > 0:
                    operator_count += count
                    unique_operators.add(op)
            
            # Simple operand counting (identifiers, numbers, strings)
            operand_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b|\b\d+(?:\.\d+)?\b|"[^"]*"|\'[^\']*\''
            operands = re.findall(operand_pattern, file_content)
            unique_operands = set(operands)
            
            # Halstead metrics
            n1 = len(unique_operators)  # Number of distinct operators
            n2 = len(unique_operands)   # Number of distinct operands
            N1 = operator_count         # Total operators
            N2 = len(operands)          # Total operands
            
            # Avoid division by zero
            if n1 == 0 or n2 == 0:
                return {'volume': 0, 'difficulty': 1, 'effort': 0}
            
            # Calculate Halstead metrics
            vocabulary = n1 + n2
            length = N1 + N2
            
            volume = length * (math.log2(vocabulary) if vocabulary > 1 else 1)
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 1
            effort = difficulty * volume
            
            return {
                'volume': round(volume, 2),
                'difficulty': round(difficulty, 2), 
                'effort': round(effort, 2)
            }
            
        except Exception as e:
            logger.warning(f"Error calculating Halstead metrics: {str(e)}")
            return {'volume': 0, 'difficulty': 1, 'effort': 0}