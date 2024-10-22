import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import os
from fpdf import FPDF

# Function to upload and process the file
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.csv")])
    if file_path:
        try:
            global df
            # Read the file into a DataFrame
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            # Perform the calculations for TKM and TON-MILE
            df['TKM'] = (df['Actual Weight (kgs)'] * df['Transport Distance (km)']) / 1000
            df['TON-MILE'] = df['TKM'] * 0.6213
            # Format to 2 decimal places
            df['TKM'] = df['TKM'].round(2)
            df['TON-MILE'] = df['TON-MILE'].round(2)

            # Populate filter dropdown
            carriers = ['All'] + df['Carrier'].unique().tolist()
            carrier_filter['values'] = carriers
            carrier_filter.current(0)
            
            # Display initial table and plot
            display_table(df)
            display_plots(df)

        except Exception as e:
            messagebox.showerror("Error", f"Error processing the file: {e}")

# Function to filter data and update the display
def filter_data(event):
    selected_carrier = carrier_filter.get()
    if selected_carrier == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['Carrier'] == selected_carrier]
    
    display_table(filtered_df)
    display_plots(filtered_df)

# Function to display the pivot table
def display_table(filtered_df):
    # Clear previous table data
    for widget in table_frame.winfo_children():
        widget.destroy()

    # Create a pivot table to group by carrier and sum TKM and TON-MILE
    global pivot_table
    pivot_table = filtered_df.groupby('Carrier').agg({'TON-MILE': 'sum', 'TKM': 'sum'}).reset_index()

    # Create a treeview to display the pivot table
    columns = ['Carrier', 'TON-MILE', 'TKM']
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')
    
    # Format bold headers and center alignment
    for col in columns:
        tree.heading(col, text=col, anchor=tk.CENTER)
        tree.column(col, anchor=tk.CENTER)

    # Insert the data into the table
    for index, row in pivot_table.iterrows():
        tree.insert("", "end", values=row.tolist())
    
    tree.pack(expand=True, fill='both')

# Function to display the plots
def display_plots(filtered_df):
    # Clear previous plot
    for widget in plot_frame.winfo_children():
        widget.destroy()

    # Create a pivot table for plot
    pivot_table = filtered_df.groupby('Carrier').agg({'TON-MILE': 'sum', 'TKM': 'sum'}).reset_index()

    # Create new figures for the plots with larger size
    global fig
    fig = Figure(figsize=(12, 6))  # Increase the figure size
    ax = fig.add_subplot(111)
    
    # Separate bars for TKM and TON-MILE with correct colors and bar positioning
    width = 0.4
    carriers = pivot_table['Carrier']
    x = range(len(carriers))
    
    ax.bar([i - width/2 for i in x], pivot_table['TON-MILE'], width=width, label='TON-MILE', color='navy')
    ax.bar([i + width/2 for i in x], pivot_table['TKM'], width=width, label='TKM', color='orange')
    
    ax.set_xlabel('Carrier')
    ax.set_ylabel('Values')
    ax.set_title('Ton-Mile & TKM by Carrier')
    ax.legend()

    # Rotate x-axis labels by 45 degrees for better readability
    ax.set_xticks(x)
    ax.set_xticklabels(carriers, rotation=45, ha="right", fontsize=10)

    # Adjust the layout to fit labels and make the chart visible
    fig.tight_layout()

    # Add the chart to the tkinter window
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill='both')

# Function to download the table data
def download_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("PDF files", "*.pdf")])
    if file_path:
        if file_path.endswith(".xlsx"):
            df.to_excel(file_path, index=False)
        elif file_path.endswith(".pdf"):
            generate_pdf(file_path)
        messagebox.showinfo("Success", f"File saved to {file_path}")

# Function to generate PDF with pivot table and visualization
def generate_pdf(file_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(200, 10, txt="Smartway Calculator Report", ln=True, align='C')

    # Add Pivot Table data
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, 'Carrier')
    pdf.cell(40, 10, 'TON-MILE')
    pdf.cell(40, 10, 'TKM')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    for index, row in pivot_table.iterrows():
        pdf.cell(40, 10, row['Carrier'])
        pdf.cell(40, 10, str(round(row['TON-MILE'], 2)))
        pdf.cell(40, 10, str(round(row['TKM'], 2)))
        pdf.ln(10)

    # Add Visualization
    pdf.ln(10)
    pdf.cell(200, 10, 'Visualization:', ln=True)
    
    pdf_image_path = "temp_chart.png"
    fig.savefig(pdf_image_path)
    pdf.image(pdf_image_path, x=10, y=None, w=190)
    
    pdf.output(file_path)

    # Clean up the temporary image file
    if os.path.exists(pdf_image_path):
        os.remove(pdf_image_path)

# Main App setup
app = tk.Tk()
app.title("Smartway Calculator")
app.geometry("900x900")

# Make the app scrollable
container = ttk.Frame(app)
canvas_scroll = tk.Canvas(container)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas_scroll.yview)
scrollable_frame = ttk.Frame(canvas_scroll)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
)

canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas_scroll.configure(yscrollcommand=scrollbar.set)

container.pack(fill="both", expand=True)
canvas_scroll.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Welcome label
welcome_label = tk.Label(scrollable_frame, text="Welcome to the Smartway Calculator", font=("Helvetica", 16, "bold"))
welcome_label.pack(pady=20)

# Upload button
upload_button = tk.Button(scrollable_frame, text="Upload your file", command=upload_file, font=("Helvetica", 12))
upload_button.pack(pady=10)

# Filter by Carrier
carrier_label = tk.Label(scrollable_frame, text="Filter by Carrier:", font=("Helvetica", 12))
carrier_label.pack()

carrier_filter = ttk.Combobox(scrollable_frame, state="readonly", font=("Helvetica", 12))
carrier_filter.pack(pady=10)
carrier_filter.bind("<<ComboboxSelected>>", filter_data)

# Frame for the table and plot
table_frame = tk.Frame(scrollable_frame)
table_frame.pack(pady=20, expand=True, fill='both')

plot_frame = tk.Frame(scrollable_frame)
plot_frame.pack(pady=20, expand=True, fill='both')

# Download button
download_button = tk.Button(scrollable_frame, text="Download Results", command=download_file, font=("Helvetica", 12), bg="lightgray")
download_button.pack(pady=20)

# Run the application
app.mainloop()
