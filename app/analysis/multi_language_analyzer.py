# Multi-Language Code Complexity and Maintainability Analyzer
import subprocess
import json
import re
import math
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class MultiLanguageAnalyzer:
    """
    Advanced multi-language code complexity and maintainability analyzer
    Supports Python, JavaScript, Java, C/C++, C#, Go, Rust, PHP, Ruby, TypeScript
    """
    
    def __init__(self):
        self.complexity_analyzers = {
            'Python': self.analyze_python_complexity,
            'JavaScript': self.analyze_javascript_complexity,
            'TypeScript': self.analyze_typescript_complexity,
            'Java': self.analyze_java_complexity,
            'C++': self.analyze_cpp_complexity,
            'C': self.analyze_cpp_complexity,  # Same as C++
            'C#': self.analyze_csharp_complexity,
            'Go': self.analyze_go_complexity,
            'Rust': self.analyze_rust_complexity,
            'PHP': self.analyze_php_complexity,
            'Ruby': self.analyze_ruby_complexity
        }
    
    def analyze_complexity_for_language(self, repo_path: str, primary_language: str) -> Dict[str, Any]:
        """
        Main entry point for language-specific complexity analysis
        Returns standardized complexity metrics regardless of language
        """
        try:
            if primary_language in self.complexity_analyzers:
                result = self.complexity_analyzers[primary_language](repo_path)
            else:
                result = self.analyze_universal_complexity(repo_path, primary_language)
            
            # Ensure consistent return format
            return self._standardize_result(result, primary_language)
            
        except Exception as e:
            print(f"Error analyzing {primary_language}: {e}")
            return self.get_default_result(primary_language)
    
    def _standardize_result(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Standardize the result format across all languages"""
        return {
            'average_complexity': result.get('average_complexity', 0.0),
            'maintainability_index': result.get('maintainability_index', 0.0),
            'complexity_distribution': result.get('complexity_distribution', {'simple': 0, 'moderate': 0, 'complex': 0}),
            'total_functions': result.get('total_functions', 0),
            'analysis_method': result.get('analysis_method', f'{language} analysis'),
            'complexity_min': result.get('complexity_min', 0.0),
            'complexity_max': result.get('complexity_max', 0.0),
            'simple_functions': result.get('complexity_distribution', {}).get('simple', 0),
            'moderate_functions': result.get('complexity_distribution', {}).get('moderate', 0),
            'complex_functions': result.get('complexity_distribution', {}).get('complex', 0)
        }
    
    # ===============================
    # PYTHON COMPLEXITY (Using Radon)
    # ===============================
    def analyze_python_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Python complexity using Radon library"""
        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
        except ImportError:
            print("Radon not installed, falling back to regex analysis")
            return self.analyze_python_regex_complexity(repo_path)
        
        total_complexity = 0
        function_count = 0
        complexity_scores = []
        maintainability_scores = []
        complexity_distribution = {'simple': 0, 'moderate': 0, 'complex': 0}
        
        python_files = self._get_files_by_extension(repo_path, ['.py'])
        
        for python_file in python_files:
            try:
                with open(python_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # Cyclomatic Complexity
                complexity_blocks = cc_visit(code)
                for block in complexity_blocks:
                    complexity = block.complexity
                    complexity_scores.append(complexity)
                    total_complexity += complexity
                    function_count += 1
                    
                    if complexity <= 5:
                        complexity_distribution['simple'] += 1
                    elif complexity <= 10:
                        complexity_distribution['moderate'] += 1
                    else:
                        complexity_distribution['complex'] += 1
                
                # Maintainability Index
                try:
                    mi_data = mi_visit(code, multi=True)
                    for item in mi_data:
                        if hasattr(item, 'mi'):
                            maintainability_scores.append(item.mi)
                except:
                    pass
                    
            except Exception:
                continue
        
        avg_complexity = total_complexity / max(function_count, 1)
        avg_maintainability = sum(maintainability_scores) / max(len(maintainability_scores), 1)
        
        return {
            'average_complexity': avg_complexity,
            'maintainability_index': avg_maintainability,
            'complexity_distribution': complexity_distribution,
            'total_functions': function_count,
            'complexity_min': min(complexity_scores) if complexity_scores else 0,
            'complexity_max': max(complexity_scores) if complexity_scores else 0,
            'analysis_method': 'Radon (Python AST analysis)'
        }
    
    # ===================================
    # JAVASCRIPT COMPLEXITY (Using ESLint)
    # ===================================
    def analyze_javascript_complexity(self, repo_path: str) -> Dict[str, Any]:
        """JavaScript complexity using ESLint or regex fallback"""
        
        # Try ESLint first
        eslint_result = self._try_eslint_analysis(repo_path)
        if eslint_result:
            return eslint_result
        
        # Fallback to regex analysis
        return self.analyze_javascript_regex_complexity(repo_path)
    
    def _try_eslint_analysis(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Try to use ESLint for JavaScript complexity analysis"""
        try:
            # Create temporary ESLint config
            eslint_config = {
                "rules": {
                    "complexity": ["error", {"max": 1}]
                },
                "parserOptions": {
                    "ecmaVersion": 2020,
                    "sourceType": "module"
                },
                "env": {
                    "node": True,
                    "browser": True,
                    "es6": True
                }
            }
            
            config_path = Path(repo_path) / '.eslintrc.temp.json'
            with open(config_path, 'w') as f:
                json.dump(eslint_config, f)
            
            # Run ESLint
            cmd = ['npx', 'eslint', '--format', 'json', '--config', str(config_path), repo_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Clean up
            if config_path.exists():
                config_path.unlink()
            
            if result.stdout:
                eslint_data = json.loads(result.stdout)
                return self._parse_eslint_complexity(eslint_data)
                
        except Exception:
            pass
        
        return None
    
    def _parse_eslint_complexity(self, eslint_data: List[Dict]) -> Dict[str, Any]:
        """Parse ESLint output for complexity metrics"""
        complexity_scores = []
        
        for file_result in eslint_data:
            for message in file_result.get('messages', []):
                if message.get('ruleId') == 'complexity':
                    # Extract complexity from message
                    complexity_match = re.search(r'complexity of (\d+)', message['message'])
                    if complexity_match:
                        complexity = int(complexity_match.group(1))
                        complexity_scores.append(complexity)
        
        if not complexity_scores:
            return None
        
        return self._calculate_complexity_metrics(complexity_scores, 'ESLint complexity analysis')
    
    def analyze_javascript_regex_complexity(self, repo_path: str) -> Dict[str, Any]:
        """JavaScript complexity using regex patterns"""
        
        js_files = self._get_files_by_extension(repo_path, ['.js', '.jsx', '.ts', '.tsx'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', 
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\btry\b',
            r'\?\s*:', r'\|\|', r'&&', r'\bdo\b'
        ]
        
        function_patterns = [
            r'function\s+\w+\s*\(',
            r'\w+\s*:\s*function\s*\(',
            r'\w+\s*=\s*function\s*\(',
            r'\w+\s*=\s*\([^)]*\)\s*=>',
            r'const\s+\w+\s*=\s*\([^)]*\)\s*=>'
        ]
        
        complexity_scores = self._analyze_files_with_patterns(
            js_files, complexity_keywords, function_patterns
        )
        
        maintainability = self._calculate_js_maintainability(js_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'JavaScript regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # =============================
    # JAVA COMPLEXITY (Using PMD or regex)
    # =============================
    def analyze_java_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Java complexity using PMD or regex fallback"""
        
        # Try PMD first
        pmd_result = self._try_pmd_analysis(repo_path)
        if pmd_result:
            return pmd_result
        
        # Fallback to regex
        return self.analyze_java_regex_complexity(repo_path)
    
    def _try_pmd_analysis(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Try to use PMD for Java complexity analysis"""
        try:
            cmd = [
                'pmd', 'check',
                '-R', 'category/java/design.xml/CyclomaticComplexity',
                '-d', repo_path,
                '-f', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                pmd_data = json.loads(result.stdout)
                return self._parse_pmd_complexity(pmd_data)
                
        except Exception:
            pass
        
        return None
    
    def analyze_java_regex_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Java complexity using regex patterns"""
        
        java_files = self._get_files_by_extension(repo_path, ['.java'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b',
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\btry\b',
            r'\?\s*:', r'\|\|', r'&&', r'\bdo\b'
        ]
        
        method_pattern = r'(public|private|protected)?\s*(static\s+)?\w+\s+\w+\s*\([^)]*\)\s*{'
        
        complexity_scores = self._analyze_files_with_patterns(
            java_files, complexity_keywords, [method_pattern]
        )
        
        maintainability = self._calculate_java_maintainability(java_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'Java regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ============================
    # C/C++ COMPLEXITY
    # ============================
    def analyze_cpp_complexity(self, repo_path: str) -> Dict[str, Any]:
        """C/C++ complexity using cppcheck or regex fallback"""
        
        # Try cppcheck first
        cppcheck_result = self._try_cppcheck_analysis(repo_path)
        if cppcheck_result:
            return cppcheck_result
        
        # Fallback to regex
        return self.analyze_cpp_regex_complexity(repo_path)
    
    def _try_cppcheck_analysis(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Try to use cppcheck for C/C++ analysis"""
        try:
            cmd = [
                'cppcheck',
                '--enable=all',
                '--xml',
                '--xml-version=2',
                repo_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stderr:  # cppcheck outputs to stderr
                return self._parse_cppcheck_results(result.stderr)
                
        except Exception:
            pass
        
        return None
    
    def analyze_cpp_regex_complexity(self, repo_path: str) -> Dict[str, Any]:
        """C/C++ complexity using regex patterns"""
        
        cpp_files = self._get_files_by_extension(repo_path, ['.cpp', '.c', '.cc', '.cxx', '.h', '.hpp'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b',
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\btry\b',
            r'\?\s*:', r'\|\|', r'&&', r'\bdo\b'
        ]
        
        function_pattern = r'(\w+::\w+|\w+)\s*\([^)]*\)\s*{'
        
        complexity_scores = self._analyze_files_with_patterns(
            cpp_files, complexity_keywords, [function_pattern]
        )
        
        maintainability = self._calculate_cpp_maintainability(cpp_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'C/C++ regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===========================
    # GO COMPLEXITY
    # ===========================
    def analyze_go_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Go complexity using gocyclo or regex fallback"""
        
        # Try gocyclo first
        gocyclo_result = self._try_gocyclo_analysis(repo_path)
        if gocyclo_result:
            return gocyclo_result
        
        # Fallback to regex
        return self.analyze_go_regex_complexity(repo_path)
    
    def _try_gocyclo_analysis(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Try to use gocyclo for Go complexity analysis"""
        try:
            cmd = ['gocyclo', '-avg', repo_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                return self._parse_gocyclo_results(result.stdout)
                
        except Exception:
            pass
        
        return None
    
    def analyze_go_regex_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Go complexity using regex patterns"""
        
        go_files = self._get_files_by_extension(repo_path, ['.go'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bfor\b', r'\bswitch\b',
            r'\bcase\b', r'\bselect\b', r'&&', r'\|\|'
        ]
        
        function_pattern = r'func\s+(\w+|\(\w+\s+\*?\w+\))\s+\w+\s*\([^)]*\)\s*{'
        
        complexity_scores = self._analyze_files_with_patterns(
            go_files, complexity_keywords, [function_pattern]
        )
        
        maintainability = self._calculate_go_maintainability(go_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'Go regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # C# COMPLEXITY
    # ===============================
    def analyze_csharp_complexity(self, repo_path: str) -> Dict[str, Any]:
        """C# complexity using regex patterns"""
        
        cs_files = self._get_files_by_extension(repo_path, ['.cs'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bforeach\b',
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\btry\b',
            r'\?\s*:', r'\|\|', r'&&', r'\bdo\b'
        ]
        
        method_pattern = r'(public|private|protected|internal)?\s*(static\s+)?(virtual\s+)?(override\s+)?\w+\s+\w+\s*\([^)]*\)\s*{'
        
        complexity_scores = self._analyze_files_with_patterns(
            cs_files, complexity_keywords, [method_pattern]
        )
        
        maintainability = self._calculate_csharp_maintainability(cs_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'C# regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # RUST COMPLEXITY
    # ===============================
    def analyze_rust_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Rust complexity using clippy or regex fallback"""
        
        # Try clippy first
        clippy_result = self._try_clippy_analysis(repo_path)
        if clippy_result:
            return clippy_result
        
        # Fallback to regex
        return self.analyze_rust_regex_complexity(repo_path)
    
    def _try_clippy_analysis(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Try to use cargo clippy for Rust analysis"""
        try:
            cmd = [
                'cargo', 'clippy',
                '--message-format', 'json',
                '--', '-W', 'clippy::cognitive_complexity'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  cwd=repo_path, timeout=120)
            
            if result.stdout:
                return self._parse_clippy_results(result.stdout)
                
        except Exception:
            pass
        
        return None
    
    def analyze_rust_regex_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Rust complexity using regex patterns"""
        
        rust_files = self._get_files_by_extension(repo_path, ['.rs'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bloop\b',
            r'\bmatch\b', r'\|\|', r'&&', r'=>'
        ]
        
        function_pattern = r'fn\s+\w+\s*\([^)]*\)\s*{'
        
        complexity_scores = self._analyze_files_with_patterns(
            rust_files, complexity_keywords, [function_pattern]
        )
        
        maintainability = self._calculate_rust_maintainability(rust_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'Rust regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # PHP COMPLEXITY
    # ===============================
    def analyze_php_complexity(self, repo_path: str) -> Dict[str, Any]:
        """PHP complexity using regex patterns"""
        
        php_files = self._get_files_by_extension(repo_path, ['.php'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bforeach\b',
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\btry\b',
            r'\?\s*:', r'\|\|', r'&&', r'\bdo\b'
        ]
        
        function_pattern = r'(public|private|protected)?\s*function\s+\w+\s*\('
        
        complexity_scores = self._analyze_files_with_patterns(
            php_files, complexity_keywords, [function_pattern]
        )
        
        maintainability = self._calculate_php_maintainability(php_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'PHP regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # RUBY COMPLEXITY
    # ===============================
    def analyze_ruby_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Ruby complexity using regex patterns"""
        
        ruby_files = self._get_files_by_extension(repo_path, ['.rb'])
        
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\belsif\b', r'\bwhile\b', r'\bfor\b',
            r'\bcase\b', r'\bwhen\b', r'\band\b', r'\bor\b', r'\bunless\b'
        ]
        
        function_pattern = r'def\s+\w+'
        
        complexity_scores = self._analyze_files_with_patterns(
            ruby_files, complexity_keywords, [function_pattern]
        )
        
        maintainability = self._calculate_ruby_maintainability(ruby_files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, 'Ruby regex analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # TYPESCRIPT COMPLEXITY
    # ===============================
    def analyze_typescript_complexity(self, repo_path: str) -> Dict[str, Any]:
        """TypeScript complexity (same as JavaScript for now)"""
        return self.analyze_javascript_complexity(repo_path)
    
    # ===============================
    # UNIVERSAL COMPLEXITY ANALYZER
    # ===============================
    def analyze_universal_complexity(self, repo_path: str, language: str) -> Dict[str, Any]:
        """Universal complexity analyzer for any language"""
        
        LANGUAGE_CONFIG = {
            'Python': {'extensions': ['.py'], 'keywords': [r'\bif\b', r'\belif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bexcept\b'], 'function_pattern': r'def\s+\w+\s*\('},
            'JavaScript': {'extensions': ['.js', '.jsx'], 'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b', r'\bcase\b'], 'function_pattern': r'function\s+\w+\s*\('},
            'Java': {'extensions': ['.java'], 'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b'], 'function_pattern': r'(public|private|protected)?\s*\w+\s+\w+\s*\('},
            'C++': {'extensions': ['.cpp', '.c', '.h'], 'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b'], 'function_pattern': r'\w+\s*\([^)]*\)\s*{'},
            'C#': {'extensions': ['.cs'], 'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b'], 'function_pattern': r'(public|private|protected)?\s*\w+\s+\w+\s*\('},
            'Go': {'extensions': ['.go'], 'keywords': [r'\bif\b', r'\belse\b', r'\bfor\b'], 'function_pattern': r'func\s+\w+\s*\('},
            'Rust': {'extensions': ['.rs'], 'keywords': [r'\bif\b', r'\belse\b', r'\bmatch\b'], 'function_pattern': r'fn\s+\w+\s*\('},
            'PHP': {'extensions': ['.php'], 'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b'], 'function_pattern': r'function\s+\w+\s*\('},
            'Ruby': {'extensions': ['.rb'], 'keywords': [r'\bif\b', r'\belse\b', r'\bcase\b'], 'function_pattern': r'def\s+\w+'}
        }
        
        config = LANGUAGE_CONFIG.get(language, {
            'extensions': ['.txt'],
            'keywords': [r'\bif\b', r'\belse\b', r'\bwhile\b', r'\bfor\b'],
            'function_pattern': r'\w+\s*\('
        })
        
        files = self._get_files_by_extension(repo_path, config['extensions'])
        complexity_scores = self._analyze_files_with_patterns(
            files, config['keywords'], [config['function_pattern']]
        )
        
        maintainability = self._calculate_universal_maintainability(files, complexity_scores)
        
        result = self._calculate_complexity_metrics(complexity_scores, f'Universal {language} analysis')
        result['maintainability_index'] = maintainability
        
        return result
    
    # ===============================
    # HELPER METHODS
    # ===============================
    def _get_files_by_extension(self, repo_path: str, extensions: List[str]) -> List[Path]:
        """Get all files with specified extensions"""
        files = []
        for ext in extensions:
            files.extend(Path(repo_path).rglob(f'*{ext}'))
        
        return [f for f in files if f.is_file() and not self._should_ignore_file(f)]
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored (node_modules, .git, etc.)"""
        ignore_patterns = [
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'build', 'dist', 'target', '.pytest_cache', 'vendor'
        ]
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _analyze_files_with_patterns(self, files: List[Path], complexity_keywords: List[str], function_patterns: List[str]) -> List[float]:
        """Analyze files using regex patterns"""
        complexity_scores = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find functions
                functions = []
                for pattern in function_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    functions.extend(matches)
                
                # Calculate complexity for each function
                for func_match in functions:
                    func_content = self._extract_function_content(content, func_match.start())
                    
                    # Base complexity
                    complexity = 1
                    
                    # Add complexity for each keyword
                    for keyword in complexity_keywords:
                        complexity += len(re.findall(keyword, func_content, re.IGNORECASE))
                    
                    complexity_scores.append(float(complexity))
                    
            except Exception:
                continue
        
        return complexity_scores
    
    def _extract_function_content(self, content: str, start_pos: int) -> str:
        """Extract function content using brace matching or heuristics"""
        brace_count = 0
        func_content = ""
        in_function = False
        
        for i, char in enumerate(content[start_pos:]):
            func_content += char
            
            if char == '{':
                brace_count += 1
                in_function = True
            elif char == '}' and in_function:
                brace_count -= 1
                if brace_count == 0:
                    break
            elif not in_function and (char == '\n' and len(func_content) > 200):
                # For languages without braces, estimate function end
                break
        
        return func_content
    
    def _calculate_complexity_metrics(self, complexity_scores: List[float], analysis_method: str) -> Dict[str, Any]:
        """Calculate standard complexity metrics from scores"""
        if not complexity_scores:
            return {
                'average_complexity': 0.0,
                'complexity_distribution': {'simple': 0, 'moderate': 0, 'complex': 0},
                'total_functions': 0,
                'complexity_min': 0.0,
                'complexity_max': 0.0,
                'analysis_method': analysis_method
            }
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        distribution = {'simple': 0, 'moderate': 0, 'complex': 0}
        for score in complexity_scores:
            if score <= 5:
                distribution['simple'] += 1
            elif score <= 10:
                distribution['moderate'] += 1
            else:
                distribution['complex'] += 1
        
        return {
            'average_complexity': avg_complexity,
            'complexity_distribution': distribution,
            'total_functions': len(complexity_scores),
            'complexity_min': min(complexity_scores),
            'complexity_max': max(complexity_scores),
            'analysis_method': analysis_method
        }
    
    # Language-specific maintainability calculators
    def _calculate_js_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for JavaScript"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Simplified MI for JavaScript
        mi = 100 - (avg_complexity * 3) - (max(0, avg_file_size - 100) / 20)
        return max(0.0, min(100.0, mi))
    
    def _calculate_java_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for Java"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Java-specific MI calculation
        mi = 100 - (avg_complexity * 4) - (max(0, avg_file_size - 150) / 15)
        return max(0.0, min(100.0, mi))
    
    def _calculate_cpp_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for C/C++"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # C/C++ specific MI calculation
        mi = 100 - (avg_complexity * 5) - (max(0, avg_file_size - 120) / 25)
        return max(0.0, min(100.0, mi))
    
    def _calculate_go_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for Go"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Go-specific MI calculation (Go prefers simpler functions)
        mi = 100 - (avg_complexity * 6) - (max(0, avg_file_size - 80) / 30)
        return max(0.0, min(100.0, mi))
    
    def _calculate_csharp_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for C#"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # C# specific MI calculation
        mi = 100 - (avg_complexity * 4) - (max(0, avg_file_size - 200) / 12)
        return max(0.0, min(100.0, mi))
    
    def _calculate_rust_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for Rust"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Rust-specific MI calculation
        mi = 100 - (avg_complexity * 3.5) - (max(0, avg_file_size - 100) / 25)
        return max(0.0, min(100.0, mi))
    
    def _calculate_php_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for PHP"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # PHP-specific MI calculation
        mi = 100 - (avg_complexity * 3.5) - (max(0, avg_file_size - 120) / 20)
        return max(0.0, min(100.0, mi))
    
    def _calculate_ruby_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Calculate maintainability index for Ruby"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Ruby-specific MI calculation
        mi = 100 - (avg_complexity * 3) - (max(0, avg_file_size - 150) / 18)
        return max(0.0, min(100.0, mi))
    
    def _calculate_universal_maintainability(self, files: List[Path], complexity_scores: List[float]) -> float:
        """Universal maintainability calculation"""
        if not files or not complexity_scores:
            return 0.0
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_file_size = self._calculate_avg_file_size(files)
        
        # Generic MI calculation
        mi = 100 - (avg_complexity * 4) - (max(0, avg_file_size - 100) / 20)
        return max(0.0, min(100.0, mi))
    
    def _calculate_avg_file_size(self, files: List[Path]) -> float:
        """Calculate average file size in lines"""
        total_lines = 0
        file_count = 0
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    file_count += 1
            except:
                continue
        
        return total_lines / max(file_count, 1)
    
    def get_default_result(self, language: str) -> Dict[str, Any]:
        """Get default result when analysis fails"""
        return {
            'average_complexity': 0.0,
            'maintainability_index': 0.0,
            'complexity_distribution': {'simple': 0, 'moderate': 0, 'complex': 0},
            'total_functions': 0,
            'complexity_min': 0.0,
            'complexity_max': 0.0,
            'simple_functions': 0,
            'moderate_functions': 0,
            'complex_functions': 0,
            'analysis_method': f'Default {language} analysis (failed)'
        }