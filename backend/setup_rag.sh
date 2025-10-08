#!/bin/bash
# Resume RAG Setup Script

echo "Setting up Resume RAG System..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy model for NLP processing
echo "Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Download NLTK data
echo "Setting up NLTK data..."
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
print('NLTK setup complete')
"

# Create necessary directories
echo "Creating directories..."
mkdir -p uploads
mkdir -p vectorstore

echo "Resume RAG system setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your Supabase database schema (see SQL commands in readme)"
echo "2. Make sure GOOGLE_API_KEY is set in your .env file"
echo "3. Restart your agent: python agent.py start"
echo ""
echo "Features added:"
echo "- Resume upload and processing"
echo "- Skill extraction from resumes"
echo "- Personalized interview questions"
echo "- Resume-based answer analysis"