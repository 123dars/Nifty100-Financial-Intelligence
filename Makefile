.PHONY: help load ratios test report dashboard api clean

PYTHON ?= python

help:
	@echo "N100 Financial Intelligence Platform — Key Commands"
	@echo "----------------------------------------------------"
	@echo "make load      - Load all Excel files into nifty100.db (Day 05)"
	@echo "make ratios    - Generate and populate the financial_ratios table"
	@echo "make test      - Run all pytest tests and generate reports/pytest_report.html"
	@echo "make report    - Generate all company tearsheets, sector reports, and portfolio report"
	@echo "make dashboard - Launch Streamlit Dashboard on localhost:8501"
	@echo "make api       - Launch FastAPI server on localhost:8000"
	@echo "make clean     - Remove cache (.pyc) and test artifacts. Database remains untouched"

load:
	$(PYTHON) src/etl/loader.py

ratios:
	$(PYTHON) src/analytics/populate_ratios.py

test:
	$(PYTHON) -m pytest --html=reports/pytest_report.html --self-contained-html

report:
	$(PYTHON) src/reports/tearsheet.py
	$(PYTHON) src/reports/sector_report.py
	$(PYTHON) src/reports/portfolio_summary.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	$(PYTHON) src/api/main.py

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache') if p.is_dir()]; [f.unlink() for f in pathlib.Path('.').rglob('*.pyc')]; print('Cleaned caches and test artifacts.')"
