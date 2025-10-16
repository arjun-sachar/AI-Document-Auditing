#!/usr/bin/env python3
"""Quick start script for AI Document Auditing System."""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_conda():
    """Check if conda is available."""
    try:
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Conda detected: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠ Conda not found. You can still use pip to install dependencies.")
    return False


def setup_conda_environment():
    """Setup conda environment."""
    print("\n=== Setting up Conda Environment ===")
    
    try:
        # Check if environment already exists
        result = subprocess.run([
            'conda', 'env', 'list', '--json'
        ], capture_output=True, text=True)
        
        import json
        envs = json.loads(result.stdout)['envs']
        env_paths = [env.split('/')[-1] for env in envs]
        
        if 'ai-doc-env' in env_paths:
            print("✓ Conda environment 'ai-doc-env' already exists")
            print("Updating dependencies...")
        else:
            # Create environment with Python 3.11
            print("Creating conda environment with Python 3.11...")
            subprocess.run([
                'conda', 'create', '-n', 'ai-doc-env', 'python=3.11', '-y'
            ], check=True)
            
            print("✓ Conda environment 'ai-doc-env' created successfully")
        
        # Install dependencies using pip in the conda environment
        print("Installing dependencies in conda environment...")
        subprocess.run([
            'conda', 'run', '-n', 'ai-doc-env', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        
        print("✓ Dependencies installed successfully in conda environment")
        print("\nTo activate the environment, run:")
        print("  conda activate ai-doc-env")
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating conda environment: {e}")
        return False
    except Exception as e:
        print(f"Error checking conda environments: {e}")
        # Try to create environment anyway
        try:
            print("Creating conda environment with Python 3.11...")
            subprocess.run([
                'conda', 'create', '-n', 'ai-doc-env', 'python=3.11', '-y'
            ], check=True)
            
            print("Installing dependencies in conda environment...")
            subprocess.run([
                'conda', 'run', '-n', 'ai-doc-env', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True)
            
            print("✓ Conda environment setup completed successfully")
            return True
            
        except subprocess.CalledProcessError as e2:
            print(f"Error creating conda environment: {e2}")
            return False
    
    return True


def setup_pip_environment():
    """Setup pip environment."""
    print("\n=== Setting up Pip Environment ===")
    
    try:
        print("Installing dependencies...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        e
        print("✓ Dependencies installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    
    return True


def setup_spacy_model(use_conda=False):
    """Download required spaCy model."""
    print("\n=== Setting up spaCy Model ===")
    
    try:
        if use_conda:
            # Use conda environment
            subprocess.run([
                'conda', 'run', '-n', 'ai-doc-env', 'python', '-m', 'spacy', 'download', 'en_core_web_sm'
            ], check=True)
        else:
            # Use current Python
            subprocess.run([
                sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'
            ], check=True)
        
        print("✓ spaCy model downloaded successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"Error downloading spaCy model: {e}")
        print("You can download it manually later with:")
        if use_conda:
            print("  conda run -n ai-doc-env python -m spacy download en_core_web_sm")
        else:
            print("  python -m spacy download en_core_web_sm")
        return False
    
    return True


def create_directories():
    """Create necessary directories."""
    print("\n=== Creating Directories ===")
    
    directories = [
        "data",
        "data/knowledge_bases",
        "data/generated_articles", 
        "data/validation_results",
        "data/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def setup_configuration():
    """Setup configuration files."""
    print("\n=== Setting up Configuration ===")
    
    # Copy environment template
    if not Path(".env").exists() and Path("env.example").exists():
        import shutil
        shutil.copy("env.example", ".env")
        print("✓ Created .env file from template")
        print("⚠ Please edit .env file with your API keys")
    else:
        print("✓ Configuration files already exist")
    
    # Check if model config exists
    if Path("config/model_config.yaml").exists():
        print("✓ Model configuration found")
    else:
        print("⚠ Model configuration not found - using defaults")


def run_tests(use_conda=False):
    """Run basic tests."""
    print("\n=== Running Tests ===")
    
    try:
        if use_conda:
            # Run tests in conda environment
            result = subprocess.run([
                'conda', 'run', '-n', 'ai-doc-env', 'python', '-c', '''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from src.validation.nlp_processor import NLPProcessor
    from src.validation.confidence_scorer import ConfidenceScorer
    from src.llm.model_selector import ModelSelector
    
    print("✓ Core modules can be imported")
    
    # Test NLP processor
    processor = NLPProcessor()
    test_text = "This is a test sentence."
    normalized = processor.normalize_text(test_text)
    assert normalized == "this is a test sentence"
    print("✓ NLP processor working")
    
    # Test confidence scorer
    scorer = ConfidenceScorer()
    print("✓ Confidence scorer working")
    
    # Test model selector
    if Path("config/model_config.yaml").exists():
        selector = ModelSelector(Path("config/model_config.yaml"))
        print("✓ Model selector working")
    
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"⚠ Test failed: {e}")
    exit(1)
'''
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"⚠ Test failed: {result.stderr}")
                return False
        else:
            # Run tests in current environment
            sys.path.insert(0, str(Path.cwd()))
            
            from src.validation.nlp_processor import NLPProcessor
            from src.validation.confidence_scorer import ConfidenceScorer
            from src.llm.model_selector import ModelSelector
            
            print("✓ Core modules can be imported")
            
            # Test NLP processor
            processor = NLPProcessor()
            test_text = "This is a test sentence."
            normalized = processor.normalize_text(test_text)
            assert normalized == "this is a test sentence"
            print("✓ NLP processor working")
            
            # Test confidence scorer
            scorer = ConfidenceScorer()
            print("✓ Confidence scorer working")
            
            # Test model selector
            if Path("config/model_config.yaml").exists():
                selector = ModelSelector(Path("config/model_config.yaml"))
                print("✓ Model selector working")
            
            return True
        
    except Exception as e:
        print(f"⚠ Test failed: {e}")
        return False


def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("AI Document Auditing System Setup Complete!")
    print("="*60)
    
    print("\nNext Steps:")
    print("1. Edit .env file with your API keys (OpenRouter recommended)")
    print("2. Activate the conda environment:")
    print("   conda activate ai-doc-env")
    print("3. Test the system:")
    print("   python -m src.cli.main --help")
    print("4. Build knowledge base from your documents:")
    print("   python -m src.cli.main build -f 'White Papers, Studies, POVs, Conference Pres' -o knowledge_bases/white_papers.json")
    print("5. Generate your first article:")
    print("   python -m src.cli.main generate -kb knowledge_bases/white_papers.json -t 'AI Research Trends'")
    print("6. Validate an article:")
    print("   python -m src.cli.main validate -a generated_article.pdf -kb knowledge_bases/white_papers.json")
    
    print("\nDocumentation:")
    print("- README.md: Complete project documentation")
    print("- examples/: Sample data and usage examples")
    print("- config/: Configuration files")
    
    print("\nConfiguration:")
    print("- API Keys: Edit .env file")
    print("- Models: Edit config/model_config.yaml")
    print("- Settings: Edit config/settings.py")
    
    print("\nTips:")
    print("- Start with the sample knowledge base and article")
    print("- Use OpenRouter for cost-effective access to Anthropic models")
    print("- Check the logs in data/logs/ for debugging")


def main():
    """Main setup function."""
    print("AI Document Auditing System - Quick Start")
    print("="*50)
    
    # Check requirements
    check_python_version()
    has_conda = check_conda()
    
    # Create directories
    create_directories()
    
    # Setup environment
    if has_conda:
        setup_conda_environment()
        # Setup spaCy model in conda environment
        setup_spacy_model(use_conda=True)
    else:
        setup_pip_environment()
        # Setup spaCy model in current environment
        setup_spacy_model(use_conda=False)
    
    # Setup configuration
    setup_configuration()
    
    # Run tests
    run_tests(use_conda=has_conda)
    
    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    main()
