#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up development environment...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 and try again."
    exit 1
fi

# Create and activate virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}
pip install --upgrade pip
pip install -r backend/requirements/base.txt
pip install -r backend/requirements/dev.txt

# Install Node.js dependencies
echo -e "${GREEN}Installing Node.js dependencies...${NC}
cd frontend
npm install
cd ..

# Set up environment variables
echo -e "${GREEN}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update the .env file with the generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    else
        # Linux/Unix
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    fi
    
    echo "Generated a new SECRET_KEY in .env"
else
    echo ".env file already exists, skipping creation"
fi

# Initialize the database
echo -e "${GREEN}Initializing database...${NC}"
cd backend
python -m scripts.init_db
cd ..

echo -e "${GREEN}Setup complete!${NC}"
echo -e "To start the development servers, run: ${GREEN}docker-compose up --build${NC}"
echo -e "Access the application at: ${GREEN}http://localhost:3000${NC}"
echo -e "Access the API documentation at: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\nTo stop the application, run: ${GREEN}docker-compose down${NC}"
