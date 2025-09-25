from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sys
import os
import shutil

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import db, Repository, ScanResult, UnderstandingScore, FileAnalysis, FunctionAnalysis
from app.analysis.scanner import CodeScanner
from dotenv import load_dotenv
import threading
import logging

# Load environment variables
load_dotenv()

# Create Flask app with correct template and static folder paths
app = Flask(__name__, 
           template_folder='app/templates',
           static_folder='app/static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///code_quality.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize code scanner
code_scanner = CodeScanner()

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/results/<int:repo_id>')
def results(repo_id):
    """Results page for a specific repository."""
    repository = Repository.query.get_or_404(repo_id)
    return render_template('results.html', repository=repository)

# API Routes
@app.route('/api/repositories', methods=['GET'])
def get_repositories():
    """Get all repositories."""
    try:
        repositories = Repository.query.order_by(Repository.created_at.desc()).all()
        return jsonify({
            'success': True,
            'repositories': [repo.to_dict() for repo in repositories]
        })
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories', methods=['POST'])
def add_repository():
    """Add a new repository."""
    try:
        data = request.get_json()
        github_url = data.get('github_url', '').strip()
        
        if not github_url:
            return jsonify({'success': False, 'error': 'GitHub URL is required'}), 400
        
        # Validate GitHub URL format
        if not github_url.startswith(('https://github.com/', 'http://github.com/')):
            return jsonify({'success': False, 'error': 'Invalid GitHub URL format'}), 400
        
        # Check if repository already exists
        existing_repo = Repository.query.filter_by(github_url=github_url).first()
        if existing_repo:
            return jsonify({'success': False, 'error': 'Repository already exists'}), 409
        
        # Extract repository name from URL
        repo_name = github_url.rstrip('/').split('/')[-1]
        if not repo_name:
            repo_name = github_url.rstrip('/').split('/')[-2] + '/' + github_url.rstrip('/').split('/')[-1]
        
        # Create new repository entry
        repository = Repository(
            github_url=github_url,
            name=repo_name,
            scan_status='pending'
        )
        
        db.session.add(repository)
        db.session.commit()
        
        logger.info(f"Added repository: {repo_name}")
        
        return jsonify({
            'success': True,
            'repository': repository.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding repository: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>', methods=['GET'])
def get_repository(repo_id):
    """Get a specific repository."""
    try:
        repository = Repository.query.get_or_404(repo_id)
        return jsonify({
            'success': True,
            'repository': repository.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching repository: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>/scan', methods=['POST'])
def start_scan(repo_id):
    """Start scanning a repository."""
    try:
        repository = Repository.query.get_or_404(repo_id)
        
        if repository.scan_status == 'scanning':
            return jsonify({'success': False, 'error': 'Scan already in progress'}), 409
        
        # Update status to scanning
        repository.scan_status = 'scanning'
        db.session.commit()
        
        # Start scanning in background thread
        thread = threading.Thread(target=perform_scan, args=(repo_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started scan for repository: {repository.name}")
        
        return jsonify({
            'success': True,
            'message': 'Scan started',
            'repository': repository.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>/results', methods=['GET'])
def get_scan_results(repo_id):
    """Get scan results for a repository."""
    try:
        repository = Repository.query.get_or_404(repo_id)
        
        # Get the latest scan result
        scan_result = ScanResult.query.filter_by(repository_id=repo_id)\
                                    .order_by(ScanResult.scan_date.desc())\
                                    .first()
        
        if not scan_result:
            return jsonify({'success': False, 'error': 'No scan results found'}), 404
        
        # Get understanding score
        understanding_score = UnderstandingScore.query.filter_by(scan_result_id=scan_result.id).first()
        
        result_data = {
            'repository': repository.to_dict(),
            'scan_result': scan_result.to_dict(),
            'understanding_score': understanding_score.to_dict() if understanding_score else None
        }
        
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching scan results: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>/detailed-results', methods=['GET'])
def get_detailed_scan_results(repo_id):
    """Get detailed scan results including file and function analysis."""
    try:
        repository = Repository.query.get_or_404(repo_id)
        
        # Get the latest scan result with all related data
        scan_result = ScanResult.query.filter_by(repository_id=repo_id)\
                                    .order_by(ScanResult.scan_date.desc())\
                                    .first()
        
        if not scan_result:
            return jsonify({'success': False, 'error': 'No scan results found'}), 404
        
        # Get understanding score
        understanding_score = UnderstandingScore.query.filter_by(scan_result_id=scan_result.id).first()
        
        # Get file analyses
        file_analyses = FileAnalysis.query.filter_by(scan_result_id=scan_result.id)\
                                         .order_by(FileAnalysis.priority_score.desc()).all()
        
        # Get function analyses for high-priority files
        function_analyses = []
        if file_analyses:
            high_priority_file_ids = [fa.id for fa in file_analyses[:5]]  # Top 5 files
            function_analyses = FunctionAnalysis.query.filter(
                FunctionAnalysis.file_analysis_id.in_(high_priority_file_ids)
            ).order_by(FunctionAnalysis.complexity_score.desc()).all()
        
        result_data = {
            'repository': repository.to_dict(),
            'scan_result': scan_result.to_dict(),
            'understanding_score': understanding_score.to_dict() if understanding_score else None,
            'file_analyses': [fa.to_dict() for fa in file_analyses],
            'function_analyses': [func.to_dict() for func in function_analyses],
            'summary': {
                'total_files': len(file_analyses),
                'high_priority_files': len([fa for fa in file_analyses if fa.improvement_priority in ['High', 'Critical']]),
                'functions_needing_attention': len([func for func in function_analyses if func.needs_refactoring])
            }
        }
        
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching detailed scan results: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e), 'details': 'Check server logs for more information'}), 500

@app.route('/api/repositories/<int:repo_id>/file-analysis', methods=['GET'])
def get_file_analysis(repo_id):
    """Get file-level analysis for a repository."""
    try:
        # Get the latest scan result
        scan_result = ScanResult.query.filter_by(repository_id=repo_id)\
                                    .order_by(ScanResult.scan_date.desc())\
                                    .first()
        
        if not scan_result:
            return jsonify({'success': False, 'error': 'No scan results found'}), 404
        
        # Get file analyses with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        file_analyses = FileAnalysis.query.filter_by(scan_result_id=scan_result.id)\
                                         .order_by(FileAnalysis.priority_score.desc())\
                                         .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'files': [fa.to_dict() for fa in file_analyses.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': file_analyses.total,
                    'pages': file_analyses.pages,
                    'has_next': file_analyses.has_next,
                    'has_prev': file_analyses.has_prev
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching file analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>', methods=['DELETE'])
def delete_repository(repo_id):
    """Delete a repository and all its data."""
    try:
        repository = Repository.query.get_or_404(repo_id)
        
        # Delete all related scan results (cascade will handle related data)
        db.session.delete(repository)
        db.session.commit()
        
        logger.info(f"Deleted repository: {repository.name}")
        
        return jsonify({
            'success': True,
            'message': f'Repository {repository.name} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting repository: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repositories/<int:repo_id>/function-analysis', methods=['GET'])
def get_function_analysis(repo_id):
    """Get function-level analysis for a repository."""
    try:
        # Get the latest scan result
        scan_result = ScanResult.query.filter_by(repository_id=repo_id)\
                                    .order_by(ScanResult.scan_date.desc())\
                                    .first()
        
        if not scan_result:
            return jsonify({'success': False, 'error': 'No scan results found'}), 404
        
        # Get function analyses through file analyses
        file_ids = [fa.id for fa in scan_result.file_analyses]
        
        # Filter parameters
        complexity_filter = request.args.get('min_complexity', type=int)
        needs_refactoring = request.args.get('needs_refactoring', type=bool)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        query = FunctionAnalysis.query.filter(FunctionAnalysis.file_analysis_id.in_(file_ids))
        
        if complexity_filter:
            query = query.filter(FunctionAnalysis.complexity_score >= complexity_filter)
        
        if needs_refactoring is not None:
            query = query.filter(FunctionAnalysis.needs_refactoring == needs_refactoring)
        
        function_analyses = query.order_by(FunctionAnalysis.complexity_score.desc())\
                                .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'functions': [func.to_dict() for func in function_analyses.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': function_analyses.total,
                    'pages': function_analyses.pages,
                    'has_next': function_analyses.has_next,
                    'has_prev': function_analyses.has_prev
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching function analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def perform_scan(repo_id):
    """Perform code analysis scan in background."""
    with app.app_context():
        try:
            repository = Repository.query.get(repo_id)
            if not repository:
                return
            
            logger.info(f"Starting analysis for repository: {repository.name}")
            
            # Detect primary language first
            primary_language = code_scanner.detect_primary_language(repository.github_url)
            repository.language = primary_language
            
            # Perform comprehensive analysis (this includes language detection)
            analysis_result = code_scanner.analyze_repository(repository.github_url)
            
            # If we have multi-language capability, enhance complexity analysis
            if hasattr(code_scanner, 'analyze_complexity_for_language') and primary_language != 'Unknown':
                try:
                    # Clone repo for multi-language analysis
                    temp_dir = code_scanner._clone_repository(repository.github_url)
                    if temp_dir:
                        try:
                            # Get enhanced complexity analysis for the specific language
                            enhanced_complexity = code_scanner.analyze_complexity_for_language(temp_dir, primary_language)
                            
                            # Update analysis results with language-specific metrics
                            analysis_result.update({
                                'complexity_score': enhanced_complexity.get('average_complexity', analysis_result.get('complexity_score', 0.0)),
                                'maintainability_index': enhanced_complexity.get('maintainability_index', analysis_result.get('maintainability_index', 0.0)),
                                'complexity_min': enhanced_complexity.get('complexity_min', 0.0),
                                'complexity_max': enhanced_complexity.get('complexity_max', 0.0),
                                'simple_functions': enhanced_complexity.get('simple_functions', 0),
                                'moderate_functions': enhanced_complexity.get('moderate_functions', 0),
                                'complex_functions': enhanced_complexity.get('complex_functions', 0),
                                'total_functions': enhanced_complexity.get('total_functions', analysis_result.get('total_functions', 0)),
                                'analysis_method': enhanced_complexity.get('analysis_method', f'{primary_language} analysis'),
                                'enhanced_analysis': True
                            })
                            
                            logger.info(f"Enhanced {primary_language} analysis completed using: {enhanced_complexity.get('analysis_method', 'unknown')}")
                            
                        finally:
                            # Clean up temporary directory
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            
                except Exception as e:
                    logger.warning(f"Enhanced language analysis failed, using default analysis: {str(e)}")
                    analysis_result['enhanced_analysis'] = False
            
            if analysis_result.get('error'):
                repository.scan_status = 'error'
                db.session.commit()
                logger.error(f"Analysis failed: {analysis_result['error']}")
                return
            
            # Update repository language with accurate detection
            repository.language = analysis_result.get('primary_language', 'Unknown')
            
            # Create enhanced scan result
            scan_result = ScanResult(
                repository_id=repository.id,
                # Enhanced Lines of Code Analysis
                total_lines=analysis_result.get('total_lines', 0),
                code_lines=analysis_result.get('code_lines', 0),
                comment_lines=analysis_result.get('comment_lines', 0),
                blank_lines=analysis_result.get('blank_lines', 0),
                comment_ratio=analysis_result.get('comment_ratio', 0.0),
                documentation_quality=analysis_result.get('documentation_quality', 'Unknown'),
                # Enhanced Complexity Analysis
                complexity_score=analysis_result.get('complexity_score', 0.0),
                complexity_min=analysis_result.get('complexity_min', 0.0),
                complexity_max=analysis_result.get('complexity_max', 0.0),
                simple_functions=analysis_result.get('simple_functions', 0),
                moderate_functions=analysis_result.get('moderate_functions', 0),
                complex_functions=analysis_result.get('complex_functions', 0),
                total_functions=analysis_result.get('total_functions', 0),
                # Enhanced Technical Debt
                maintainability_index=analysis_result.get('maintainability_index', 0.0),
                duplication_percentage=analysis_result.get('duplication_percentage', 0.0),
                technical_debt_minutes=analysis_result.get('technical_debt_minutes', 0),
                duplication_debt_minutes=analysis_result.get('duplication_debt_minutes', 0),
                complexity_debt_minutes=analysis_result.get('complexity_debt_minutes', 0),
                documentation_debt_minutes=analysis_result.get('documentation_debt_minutes', 0),
                long_function_debt_minutes=analysis_result.get('long_function_debt_minutes', 0),
                # Language Analysis
                primary_language=analysis_result.get('primary_language', 'Unknown'),
                language_distribution=analysis_result.get('language_distribution', '{}'),
                files_analyzed=analysis_result.get('files_analyzed', 0)
            )
            
            db.session.add(scan_result)
            db.session.flush()  # Get the scan_result.id
            
            # Save file analyses
            file_analyses = analysis_result.get('file_analyses', [])
            for file_data in file_analyses:
                file_analysis = FileAnalysis(
                    scan_result_id=scan_result.id,
                    file_path=file_data['file_path'],
                    file_name=file_data['file_name'],
                    language=file_data['language'],
                    lines_of_code=file_data['lines_of_code'],
                    complexity_score=file_data['complexity_score'],
                    duplication_percentage=file_data['duplication_percentage'],
                    maintainability_index=file_data['maintainability_index'],
                    function_count=file_data['function_count'],
                    comment_ratio=file_data['comment_ratio'],
                    improvement_priority=file_data['improvement_priority'],
                    priority_score=file_data['priority_score']
                )
                db.session.add(file_analysis)
            
            db.session.flush()  # Get file analysis IDs
            
            # Save function analyses (link to appropriate file analyses)
            function_analyses = analysis_result.get('function_analyses', [])
            file_analysis_map = {}
            
            # Create a map of file paths to file analysis IDs
            for file_analysis in scan_result.file_analyses:
                file_analysis_map[file_analysis.file_path] = file_analysis.id
            
            for func_data in function_analyses:
                file_analysis_id = file_analysis_map.get(func_data['file_path'])
                if file_analysis_id:
                    function_analysis = FunctionAnalysis(
                        file_analysis_id=file_analysis_id,
                        function_name=func_data['function_name'],
                        line_number=func_data['line_number'],
                        complexity_score=func_data['complexity_score'],
                        lines_of_code=func_data['lines_of_code'],
                        parameter_count=func_data['parameter_count'],
                        has_documentation=func_data['has_documentation'],
                        complexity_category=func_data['complexity_category'],
                        needs_refactoring=func_data['needs_refactoring']
                    )
                    db.session.add(function_analysis)
            
            # Calculate enhanced understanding score
            understanding_score_data = code_scanner.calculate_understanding_score({
                'complexity_score': scan_result.complexity_score,
                'maintainability_index': scan_result.maintainability_index,
                'duplication_percentage': scan_result.duplication_percentage,
                'technical_debt_minutes': scan_result.technical_debt_minutes,
                'comment_ratio': scan_result.comment_ratio,
                'total_functions': scan_result.total_functions,
                'complex_functions': scan_result.complex_functions
            })
            
            understanding_score = UnderstandingScore(
                scan_result_id=scan_result.id,
                readability_score=understanding_score_data['score'],
                difficulty_level=understanding_score_data['level'],
                base_score=understanding_score_data['base_score'],
                complexity_penalty=understanding_score_data['complexity_penalty'],
                duplication_penalty=understanding_score_data['duplication_penalty'],
                maintainability_bonus=understanding_score_data.get('maintainability_bonus', 0),
                documentation_bonus=understanding_score_data.get('documentation_bonus', 0)
            )
            
            db.session.add(understanding_score)
            
            # Update repository status
            repository.scan_status = 'completed'
            
            db.session.commit()
            
            logger.info(f"Analysis completed for repository: {repository.name}")
            
        except Exception as e:
            db.session.rollback()
            repository = Repository.query.get(repo_id)
            if repository:
                repository.scan_status = 'error'
                db.session.commit()
            logger.error(f"Error during scan: {str(e)}")

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

def create_tables():
    """Create database tables."""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)