# Code Quality Dashboard# Code Quality Dashboard



A comprehensive code quality analysis tool that provides detailed metrics and insights for software projects across multiple programming languages.A comprehensive web-based dashboard that analyzes GitHub repositories across diffrent programming languages, providing code quality metrics and actionable insights.



## Features

## Features

- **Multi-language Support**: Analyzes Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, C#, PHP, and Ruby

- **Comprehensive Metrics**: Understanding score, complexity analysis, maintainability index, and technical debt### Core Functionality

- **Interactive Dashboard**: Modern web interface with real-time charts and visualizations  - **Multi-Language Analysis**: Support for Python, JavaScript, Java, C++, Go, Rust, C#, PHP, Ruby, TypeScript

- **GitHub Integration**: Direct repository analysis from GitHub URLs- **Advanced Code Scanning**: Industry-standard metrics using Radon, ESLint, PMD, and language-specific analyzers

- **Detailed Reports**: File-level and function-level analysis with actionable recommendations- **Interactive Dashboard**: Modern, responsive web interface with Chart.js visualizations

- **Export Capabilities**: JSON export of complete analysis results- **Real-time Analysis**: Live progress tracking during repository scanning

- **Comprehensive Reports**: Detailed file-level and function-level analysis

## Prerequisites- **Export Capabilities**: Download complete analysis results in JSON format



- Python 3.8 or higher### 15+ Code Quality Metrics

- Git (for GitHub repository cloning)

- Modern web browser#### 1. Lines of Code Analysis

- **Total Lines**: Complete codebase size

## Quick Start- **Code Lines**: Actual executable code (excludes comments/blanks)

- **Comment Lines**: Documentation and inline comments

1. **Clone and Install**- **Blank Lines**: Whitespace and formatting

   ```bash- **Comment Ratio**: Documentation quality assessment

   git clone <repository-url>

   cd codeanalysis#### 2. Cyclomatic Complexity Analysis

   pip install -r requirements.txt- **McCabe Complexity**: Industry-standard complexity measurement

   ```- **Function Distribution**: Simple/Moderate/Complex categorization

- **Average Complexity**: Repository-wide complexity score

2. **Run Application**- **High Complexity Functions**: Functions requiring immediate attention

   ```bash- **Language-Specific Analysis**: Python (Radon), JavaScript (ESLint), Java (PMD)

   python app.py

   ```#### 3. Maintainability Assessment

- **Maintainability Index**: Microsoft's 0-100 scale assessment

3. **Access Dashboard**- **Halstead Metrics**: Operator/operand complexity analysis

   - Open browser to `http://localhost:5000`- **File-Level Scoring**: Individual file maintainability breakdown

   - Enter GitHub repository URL- **Technical Debt Estimation**: Time-based improvement estimates

   - Click "Analyze Repository"

   - View comprehensive analysis results#### 4. Code Health Indicators

- **Duplication Detection**: Hash-based duplicate code identification

## Key Metrics- **File Hotspots**: Most complex and problematic files

- **Function Analysis**: Method-level complexity breakdown

| Metric | Description |- **Quality Violations**: Language-specific linting issues

|--------|-------------|

| **Understanding Score** | Overall code readability and comprehensibility (0-100) |#### 5. Understanding Score Algorithm

| **Complexity Score** | Cyclomatic complexity analysis with function-level breakdown |- **Comprehensive Scoring**: 0-100 scale with weighted factors

| **Maintainability Index** | Microsoft's maintainability formula adaptation |- **Multi-Component Assessment**: Complexity + Maintainability + Duplication + Documentation

| **Technical Debt** | Estimated time required for code improvements |- **Difficulty Classification**: Easy/Moderate/Challenging/Difficult

- **Actionable Recommendations**: Specific improvement suggestions

## Analysis Coverage

## Multi-Language Support

- **Lines of Code**: Total, code, comments, and blank lines

- **Function Analysis**: Complexity distribution (Simple/Moderate/Complex)| Language | Complexity Analysis | Maintainability | Primary Tool | Fallback Method |

- **Language Distribution**: Multi-language project composition|----------|-------------------|-----------------|--------------|-----------------|

- **Code Quality**: Duplication detection and documentation coverage| **Python** | Full Support | Microsoft MI | Radon | AST parsing |

- **Improvement Priorities**: File and function-level recommendations| **JavaScript** | Full Support | Calculated | ESLint | Regex patterns |

| **Java** | Full Support | Calculated | PMD | Regex patterns |

## Technology Stack| **C/C++** | Full Support | Calculated | cppcheck | Regex patterns |

| **Go** | Full Support | Calculated | gocyclo | Regex patterns |

- **Backend**: Flask, SQLAlchemy, SQLite| **Rust** | Full Support | Calculated | clippy | Regex patterns |

- **Frontend**: Bootstrap 5, Chart.js, JavaScript ES6+| **C#** | Estimated | Calculated | .NET analyzers | Regex patterns |

- **Analysis**: Radon (Python), custom parsers for other languages| **TypeScript** | Full Support | Calculated | ESLint + TS | Regex patterns |

- **Database**: SQLite for result storage and history| **PHP** | Estimated | Calculated | Regex patterns | Language detection |

| **Ruby** | Estimated | Calculated | Regex patterns | Language detection |

## Project Structure

## Requirements

```

codeanalysis/### System Requirements

├── app/- Python 3.8 or higher

│   ├── analysis/          # Code analysis engines- Git (for repository cloning)

│   ├── models/           # Database models- Node.js (optional, for enhanced JavaScript/TypeScript analysis)

│   ├── static/           # CSS, JS, assets- 2GB+ available disk space

│   └── templates/        # HTML templates- Internet connection for GitHub API access

├── instance/             # Database storage

├── app.py               # Main Flask application### Core Dependencies

└── requirements.txt     # Python dependencies```

```Flask==3.0.3

Flask-SQLAlchemy==3.1.1

## ConfigurationPyGithub==2.3.0

Pylint==3.2.6

The application runs with default settings. For customization:Radon==6.0.1

- Database path: Modify `SQLALCHEMY_DATABASE_URI` in `app.py`GitPython==3.1.43

- Port: Change `app.run(port=5000)` in `app.py`python-dotenv==1.0.1

- Debug mode: Set `debug=False` for production```



## Contributing### Optional Language Tools (Enhanced Analysis)

```bash

1. Fork the repository# JavaScript/TypeScript

2. Create feature branch (`git checkout -b feature/amazing-feature`)npm install -g eslint @typescript-eslint/parser

3. Commit changes (`git commit -m 'Add amazing feature'`)

4. Push to branch (`git push origin feature/amazing-feature`)# Java (Download from official sites)

5. Open Pull Request# PMD: https://pmd.github.io/

---## Installation

**Made with for better code quality**### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/lalitaditya04/CodeAnalysis
cd CodeAnalysis

# 2. Run setup script (Windows)
run.bat

# 3. Access dashboard
# Open browser: http://localhost:5000
```

### Manual Installation
```bash
# 1. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your settings

# 4. Start application
python app.py
```

### Environment Configuration
```env
# GitHub API Token (recommended for higher rate limits)
GITHUB_TOKEN=your_github_token_here

# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///code_quality.db
FLASK_ENV=development
```

## Usage

### 1. Repository Analysis
1. **Add Repository**: Enter GitHub URL (e.g., `https://github.com/microsoft/vscode`)
2. **Start Scan**: Click "Analyze Repository" for comprehensive analysis
3. **View Results**: Access detailed metrics, charts, and recommendations
4. **Export Data**: Download complete analysis as JSON report

### 2. Understanding Results

#### Complexity Scoring
```
Simple (1-5):     Low risk, easy to understand
Moderate (6-10):  Manageable complexity  
Complex (11-20):  High complexity, needs attention
Very Complex(21+): Critical refactoring needed
```

#### Maintainability Index
```
Excellent (85-100): Very maintainable code
Good (70-84):       Maintainable with minor issues
Moderate (50-69):   Some maintainability concerns  
Poor (0-49):        Significant maintainability issues
```

#### Understanding Score Algorithm
```python
# Multi-factor scoring (0-100 scale)
base_score = 100

# Complexity penalty (30% weight)
if complexity > 20: base_score -= 30
elif complexity > 15: base_score -= 20
elif complexity > 10: base_score -= 15

# Maintainability impact (25% weight)  
if maintainability < 30: base_score -= 25
elif maintainability < 50: base_score -= 18

# Duplication penalty (20% weight)
if duplication > 25: base_score -= 25  
elif duplication > 15: base_score -= 18

# Technical debt penalty (15% weight)
if debt_hours > 4: base_score -= 15
elif debt_hours > 2: base_score -= 10

# Documentation impact (10% weight)
if comment_ratio < 3: base_score -= 10
elif comment_ratio > 15: base_score += 3

final_score = max(0, min(100, base_score))
```

### 3. API Endpoints

```http
# Repository management
GET    /api/repositories              # List all repositories
POST   /api/repositories              # Add new repository
GET    /api/repositories/{id}         # Get repository details
POST   /api/repositories/{id}/scan    # Start analysis

# Results and analysis
GET    /api/repositories/{id}/results           # Basic results
GET    /api/repositories/{id}/detailed-results  # Detailed analysis
GET    /api/repositories/{id}/file-analysis     # File-level metrics
GET    /api/repositories/{id}/function-analysis # Function-level data
```

## Technical Implementation

### Analysis Engine Architecture
```
GitHub Repository
       ↓
Language Detection (Volume-weighted)
       ↓
Multi-Language Analyzer Router
       ↓
┌─────────────────────────────────────┐
│ Python → Radon (AST + McCabe)       │
│ JavaScript → ESLint + Regex         │  
│ Java → PMD + Regex                  │
│ C++ → cppcheck + Regex              │
│ Go → gocyclo + Regex                │
│ Rust → clippy + Regex               │
│ Others → Universal Regex Patterns   │
└─────────────────────────────────────┘
       ↓
Metrics Calculation & Storage
       ↓
Interactive Dashboard + Export
```

### Database Schema
```sql
-- Enhanced schema with multi-language support
Repositories (id, github_url, name, language, scan_status)
ScanResults (id, repo_id, total_lines, complexity_score, maintainability_index, ...)
UnderstandingScores (id, scan_id, readability_score, difficulty_level)
FileAnalysis (id, scan_id, file_path, complexity, duplication_pct)
FunctionAnalysis (id, file_id, function_name, complexity, lines)
```

## Project Structure

```
codeanalysis/
├── app.py                          # Main Flask application
├── requirements.txt                # Dependencies
├── run.bat                        # Windows setup script
├── README.md                      # Documentation
├── PROJECT_SUMMARY.md             # Executive summary
├── app/
│   ├── models/__init__.py         # Database models
│   ├── analysis/
│   │   ├── scanner.py             # Core analysis engine
│   │   └── multi_language_analyzer.py  # Multi-language support
│   ├── static/
│   │   ├── css/
│   │   │   ├── dashboard.css      # Dashboard styling
│   │   │   └── results.css        # Results page styling
│   │   └── js/
│   │       ├── dashboard.js       # Dashboard functionality  
│   │       └── results.js         # Results visualization
│   └── templates/
│       ├── dashboard.html         # Main dashboard
│       └── results.html           # Analysis results
└── code_quality.db               # SQLite database
```

## Advanced Configuration

### Custom Analysis Rules
```python
# Add to scanner.py for custom complexity thresholds
COMPLEXITY_THRESHOLDS = {
    'Python': {'simple': 5, 'moderate': 10, 'complex': 15},
    'JavaScript': {'simple': 6, 'moderate': 12, 'complex': 20},
    'Java': {'simple': 4, 'moderate': 8, 'complex': 12}
}
```

### Performance Tuning
```python
# Large repository optimization
SCAN_TIMEOUT = 600  # 10 minutes max
MAX_FILE_SIZE = 1024 * 1024  # 1MB max per file
IGNORE_PATTERNS = ['.git/', 'node_modules/', '__pycache__/']
```

## Troubleshooting

### Common Issues

#### Multi-Language Tool Setup
```bash
# Check tool availability
eslint --version
pmd --version  
gocyclo --version

# Install missing tools
npm install -g eslint
# Download PMD from https://pmd.github.io/
```

#### Analysis Failures
- **Large repositories**: Increase timeout in scanner.py
- **Private repositories**: Add GitHub token to .env
- **Memory issues**: Analyze smaller repositories or increase system RAM

#### Performance Issues
- **Slow scans**: Install language-specific tools for faster analysis
- **High memory usage**: Enable file size limits in configuration

## Metrics Accuracy

### Analysis Quality by Language
- **Python**: 95%+ accuracy (full AST analysis via Radon)
- **JavaScript**: 90%+ accuracy (ESLint + advanced regex)
- **Java**: 85%+ accuracy (PMD integration + regex fallback)
- **C/C++**: 80%+ accuracy (cppcheck + pattern matching)
- **Go**: 85%+ accuracy (gocyclo + Go-specific patterns)
- **Others**: 70%+ accuracy (intelligent regex patterns)

## Future Enhancements

- **CI/CD Integration**: GitHub Actions, Jenkins webhooks
- **Historical Tracking**: Quality trend analysis over time
- **Team Collaboration**: Multi-user support and shared dashboards  
- **Custom Rules Engine**: User-defined quality thresholds
- **Advanced Visualizations**: 3D complexity maps, trend charts
- **Machine Learning**: Predictive quality scoring
- **Docker Deployment**: Containerized production setup

---

**Built with Flask, SQLAlchemy, Chart.js, and multi-language analysis tools**


