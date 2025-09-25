# CodeAnalysis

A comprehensive code quality analysis tool that provides detailed metrics and insights for software projects across multiple programming languages.

## Features

- Multi-language support: Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, C#, PHP, Ruby
- GitHub repository integration with direct URL analysis
- Interactive web dashboard with real-time visualizations
- Comprehensive metrics: complexity analysis, maintainability index, technical debt
- File-level and function-level analysis with actionable recommendations
- JSON export capabilities for complete analysis results

## Requirements

- Python 3.8 or higher
- Git (for GitHub repository cloning)
- Modern web browser

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/CodeAnalysis.git
   cd CodeAnalysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open browser to `http://localhost:5000`

## Usage

1. Enter a GitHub repository URL in the dashboard
2. Click "Analyze Repository" to start the analysis
3. View comprehensive results including:
   - Understanding Score (0-100 readability assessment)
   - Cyclomatic Complexity analysis
   - Maintainability Index
   - Technical Debt estimation
   - Lines of Code breakdown
   - File and function level metrics

## Key Metrics

**Understanding Score**: Overall code readability and comprehensibility (0-100 scale)
**Complexity Score**: McCabe cyclomatic complexity with function-level breakdown
**Maintainability Index**: Microsoft's maintainability formula adaptation
**Technical Debt**: Estimated time required for code improvements

## Technology Stack

- Backend: Flask, SQLAlchemy, SQLite
- Frontend: Bootstrap 5, Chart.js, JavaScript
- Analysis: Radon (Python), custom parsers for other languages
- Database: SQLite for result storage

## Project Structure

```
CodeAnalysis/
├── app.py                 # Main Flask application
├── requirements.txt       # Dependencies
├── app/
│   ├── analysis/         # Code analysis engines
│   ├── models/           # Database models
│   ├── static/           # CSS, JS assets
│   └── templates/        # HTML templates
├── instance/             # Database storage
└── run.bat
```

## Language Support

| Language | Analysis Tool | Accuracy |
|----------|---------------|----------|
| Python | Radon | 95%+ |
| JavaScript | Custom parser | 90%+ |
| TypeScript | Custom parser | 90%+ |
| Java | Pattern matching | 85%+ |
| C/C++ | Pattern matching | 80%+ |
| Go | Pattern matching | 85%+ |
| Others | Heuristic analysis | 70%+ |

## Configuration

Default settings work out of the box. For customization:
- Database: Modify `SQLALCHEMY_DATABASE_URI` in `app.py`
- Port: Change `app.run(port=5000)` in `app.py`
- Debug: Set `debug=False` for production

## API Endpoints

- `GET /api/repositories` - List all repositories
- `POST /api/repositories` - Add new repository
- `GET /api/repositories/{id}/detailed-results` - Get analysis results
- `POST /api/repositories/{id}/scan` - Start analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

