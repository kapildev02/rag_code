# Set the virtual environment activation command
VENV_ACTIVATE = source venv/bin/activate

# create virtual environment
create-venv:
	python3 -m venv venv

# Install dependencies
install:
	$(VENV_ACTIVATE) && pip install -r requirements.txt

# Run the FastAPI server
run:
	$(VENV_ACTIVATE) && uvicorn app.main:socket_app --host 0.0.0.0 --port 8080 --reload

# Check installed dependencies
deps:
	$(VENV_ACTIVATE) && pip list

# Format code using Black
format:
	$(VENV_ACTIVATE) && black .

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +

# Create requirements.txt
freeze:
	$(VENV_ACTIVATE) && pip freeze > requirements.txt