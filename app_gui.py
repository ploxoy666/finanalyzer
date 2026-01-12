import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
import queue
from pathlib import Path
import re
from PIL import Image, ImageTk

# Charting imports
import matplotlib
matplotlib.use('TkAgg') # Crucial for embedding in Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Core imports
from src.models.schemas import AccountingStandard
from src.core.model_engine import ModelEngine
from src.core.forecast_engine import ForecastEngine, ForecastAssumptions
from src.core.report_generator import ReportGenerator
from src.core.pdf_parser import PDFParser
from src.core.gaap_ifrs_classifier import GaapIfrsClassifier
from main import create_sample_statements

class FinancialAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Financial Report Analyzer Pro")
        self.root.geometry("1200x800")
        
        # Setup Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()
        
        # State
        self.pdf_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to analyze")
        self.is_analyzing = False
        self.log_queue = queue.Queue()
        
        # Data
        self.current_model = None
        
        self.create_widgets()
        self.check_queue()

    def _configure_styles(self):
        # Colors
        bg_color = "#f8f9fa"
        primary_color = "#007bff"
        
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabelframe", background=bg_color)
        self.style.configure("TLabelframe.Label", background=bg_color, font=("Helvetica", 12, "bold"), foreground="#495057")
        self.style.configure("TLabel", background=bg_color, font=("Helvetica", 10))
        self.style.configure("Title.TLabel", font=("Helvetica", 18, "bold"), foreground=primary_color)
        self.style.configure("Status.TLabel", font=("Helvetica", 10, "italic"), foreground="#6c757d")
        
        self.style.configure("TButton", font=("Helvetica", 10, "bold"), padding=10)
        self.style.configure("Accent.TButton", background=primary_color, foreground="white")

    def create_widgets(self):
        # Main Container
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="📊 AI Financial Analyzer", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="v2.0", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=10, pady=8)

        # Tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Analysis & Settings
        self.tab_setup = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_setup, text=" 📁 Setup & Analyze ")
        self._build_setup_tab(self.tab_setup)
        
        # Tab 2: Dashboard (Results)
        self.tab_dashboard = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_dashboard, text=" 📈 Dashboard & Results ")
        self._build_dashboard_tab(self.tab_dashboard)
        
        # Tab 3: Logs
        self.tab_logs = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_logs, text=" 📝 Processing Logs ")
        self._build_logs_tab(self.tab_logs)
        
        # Status Bar
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=5)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5)
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)

    def _build_setup_tab(self, parent):
        # Left Column: Upload & Company
        left_panel = ttk.Frame(parent)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 1. File Upload Section
        upload_frame = ttk.LabelFrame(left_panel, text="Input Data", padding=15)
        upload_frame.pack(fill=tk.X, pady=(0, 15))
        
        file_container = ttk.Frame(upload_frame)
        file_container.pack(fill=tk.X)
        
        self.file_entry = ttk.Entry(file_container, textvariable=self.pdf_path)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(file_container, text="Browse PDF...", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        # 2. Company Info
        info_frame = ttk.LabelFrame(left_panel, text="Company Details", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        Grid = ttk.Frame(info_frame)
        Grid.pack(fill=tk.X)
        
        ttk.Label(Grid, text="Company Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.company_name = ttk.Entry(Grid)
        self.company_name.grid(row=0, column=1, sticky='ew', padx=10)
        
        ttk.Label(Grid, text="Ticker:").grid(row=1, column=0, sticky='w', pady=5)
        self.ticker = ttk.Entry(Grid)
        self.ticker.grid(row=1, column=1, sticky='ew', padx=10)
        
        # Right Column: Forecast Settings
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        settings_frame = ttk.LabelFrame(right_panel, text="Forecast Assumptions", padding=15)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Sliders
        self.rev_growth = self._create_slider(settings_frame, "Revenue Growth", 0, 30, 8, "%", 0)
        self.gross_margin = self._create_slider(settings_frame, "Gross Margin", 0, 100, 42, "%", 1)
        self.op_margin = self._create_slider(settings_frame, "Operating Margin", 0, 100, 22, "%", 2)
        self.years = self._create_slider(settings_frame, "Forecast Years", 1, 10, 5, " years", 3)
        
        # Action Buttons
        actions_frame = ttk.Frame(right_panel)
        actions_frame.pack(fill=tk.X)
        
        run_btn = ttk.Button(actions_frame, text="🚀 ANALYZE REPORT", command=self.start_analysis, style="Accent.TButton")
        run_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        demo_btn = ttk.Button(actions_frame, text="⚡ Run Demo", command=self.run_demo)
        demo_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def _create_slider(self, parent, label, vmin, vmax, default, unit, row):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='ew', pady=10)
        parent.columnconfigure(0, weight=1)
        
        # Header
        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        ttk.Label(top, text=label, font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        val_label = ttk.Label(top, text=f"{default}{unit}")
        val_label.pack(side=tk.RIGHT)
        
        # Slider
        var = tk.DoubleVar(value=default)
        scale = ttk.Scale(frame, from_=vmin, to=vmax, variable=var, orient="horizontal")
        scale.pack(fill=tk.X, pady=(5, 0))
        
        # Update label callback
        def update_label(v):
            val = float(v)
            if unit == "%":
                val_label.config(text=f"{val:.1f}%")
            else:
                val_label.config(text=f"{int(val)}{unit}")
        
        scale.configure(command=update_label)
        return var

    def _build_dashboard_tab(self, parent):
        """Create visualizations tab"""
        # KPI Row
        self.kpi_frame = ttk.Frame(parent)
        self.kpi_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Charts Area
        self.charts_frame = ttk.Frame(parent)
        self.charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder
        self.no_data_label = ttk.Label(self.charts_frame, text="Run analysis to view dashboard", font=("Helvetica", 14), foreground="#adb5bd")
        self.no_data_label.place(relx=0.5, rely=0.5, anchor="center")

    def _build_logs_tab(self, parent):
        self.log_text = tk.Text(parent, state='disabled', height=20, font=("Courier New", 12))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text['yscrollcommand'] = scrollbar.set

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.pdf_path.set(filename)

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state='disabled')
        self.root.after(100, self.check_queue)

    def start_analysis(self):
        if not self.company_name.get() and not self.pdf_path.get():
            messagebox.showwarning("Input Required", "Please select a PDF or enter company details")
            return
        
        self._set_analyzing(True)
        threading.Thread(target=self._run_analysis_thread, daemon=True).start()

    def run_demo(self):
        self.company_name.delete(0, tk.END)
        self.company_name.insert(0, "Demo Corp Inc.")
        self._set_analyzing(True)
        threading.Thread(target=self._run_analysis_thread, args=(True,), daemon=True).start()

    def _set_analyzing(self, state):
        self.is_analyzing = state
        if state:
            self.progress.start(10)
            self.status_var.set("Analyzing... Please wait")
            self.log_text.configure(state='normal')
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state='disabled')
        else:
            self.progress.stop()
            self.status_var.set("Ready")

    def _run_analysis_thread(self, is_demo=False):
        try:
            self.log("🚀 Starting verification and analysis...")
            
            # 1. Get/Create Data
            if is_demo:
                self.log("📊 Generating synthetic demo data...")
                # We need to import AccountingStandard from src.models.schemas
                statements = create_sample_statements(AccountingStandard.GAAP)
            else:
                self.log(f"📄 Parsing PDF: {Path(self.pdf_path.get()).name}...")
                self.log("⚠️ Using demo extraction (Extractor module pending)")
                statements = create_sample_statements(AccountingStandard.GAAP)
                statements.company_name = self.company_name.get() or "Analyzed Company"

            # 2. Build Model
            self.log("⚙️ Building 3-statement financial model...")
            model_engine = ModelEngine(statements)
            linked_model = model_engine.build_linked_model()
            
            if linked_model.is_balanced:
                self.log("✅ Model balanced and linked")
            
            # 3. Forecast
            self.log(f"🔮 Generating {int(self.years.get())}-year forecast...")
            assumptions = ForecastAssumptions(
                revenue_growth_rate=self.rev_growth.get()/100,
                gross_margin=self.gross_margin.get()/100,
                operating_margin=self.op_margin.get()/100
            )
            
            forecast_engine = ForecastEngine(linked_model)
            forecast_model = forecast_engine.forecast(
                years=int(self.years.get()),
                assumptions=assumptions
            )
            
            # 4. Generate PDF
            self.log("📑 Rendering PDF report...")
            Path("output").mkdir(exist_ok=True)
            output_file = f"output/analysis_{statements.company_name.replace(' ', '_')}.pdf"
            
            generator = ReportGenerator(forecast_model)
            generator.generate_pdf(output_file)
            
            self.log(f"✨ Success! Report saved to {output_file}")
            
            # 5. Update UI
            self.current_model = forecast_model
            self.root.after(0, self._update_dashboard)
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.root.after(0, lambda: self._set_analyzing(False))

    def _update_dashboard(self):
        """Render charts in the dashboard tab"""
        # Clear previous
        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        for widget in self.charts_frame.winfo_children(): widget.destroy()
        
        if not self.current_model: return
        
        # 1. Render KPIs
        last_hist = self.current_model.historical_income_statements[-1]
        last_fc = self.current_model.forecast_income_statements[-1]
        
        kpis = [
            ("Current Revenue", f"${last_hist.revenue/1e9:.1f}B", "#1f77b4"),
            ("Forecast Revenue", f"${last_fc.revenue/1e9:.1f}B", "#2ca02c"),
            ("Net Margin", f"{last_hist.net_margin*100:.1f}%", "#ff7f0e"),
        ]
        
        for title, value, color in kpis:
            card = ttk.LabelFrame(self.kpi_frame, text=title)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            ttk.Label(card, text=value, font=("Helvetica", 24, "bold"), foreground=color).pack(pady=10)
        

        # 2. Render Charts
        try:
            fig = Figure(figsize=(10, 5), dpi=100)
            ax = fig.add_subplot(111)
            
            # Data
            all_stmts = self.current_model.historical_income_statements + self.current_model.forecast_income_statements
            years = [s.period_end.year for s in all_stmts]
            revs = [s.revenue/1e9 for s in all_stmts]
            net = [s.net_income/1e9 for s in all_stmts]
            
            # Plot
            bars = ax.bar(years, revs, label='Revenue ($B)', alpha=0.7, color='#1f77b4')
            ax2 = ax.twinx()
            line = ax2.plot(years, net, label='Net Income ($B)', color='#ff7f0e', marker='o', linewidth=2)
            
            ax.set_title("Revenue & Profit Trajectory (Historical + Forecast)", fontweight='bold')
            ax.set_xlabel("Year")
            ax.set_ylabel("Revenue ($B)")
            ax2.set_ylabel("Net Income ($B)")
            
            # Legend
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper left')
            
            ax.grid(True, alpha=0.3)
            
            # Embed
            canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Hide placeholder
            self.no_data_label.place_forget()
            
        except Exception as e:
            self.log(f"⚠️ Error rendering charts: {e}")
            messagebox.showerror("Chart Error", f"Could not render dashboard charts: {e}")
        
        # Switch to tab
        self.notebook.select(self.tab_dashboard)

if __name__ == "__main__":
    root = tk.Tk()
    app = FinancialAnalyzerGUI(root)
    root.mainloop()
