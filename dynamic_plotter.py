import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from collections import deque
import numpy as np
import queue

class DynamicCSVOscilloscope:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic CSV Oscilloscope")
        self.root.geometry("800x600")
        
        # Serial connection
        self.serial_port = None
        self.running = False
        
        # Dynamic data storage
        self.max_points = 500
        self.columns = []  # Will be detected from CSV header
        self.sensor_data = {}  # Will be dynamically created
        self.data_buffer = deque(maxlen=self.max_points)
        self.data_counter = 0
        self.current_feature = None
        
        # Data queue for thread-safe communication
        self.data_queue = queue.Queue()
        
        # Detection state
        self.header_detected = False
        
        self.setup_gui()
        
    def setup_gui(self):
        # Top control frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Connection controls
        conn_frame = ttk.Frame(control_frame)
        conn_frame.pack(side=tk.LEFT)
        
        ttk.Label(conn_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "COM3")
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="●", foreground="red", font=("Arial", 12))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Feature selection frame
        feature_frame = ttk.Frame(control_frame)
        feature_frame.pack(side=tk.RIGHT)
        
        ttk.Label(feature_frame, text="Signal:").pack(side=tk.LEFT, padx=(20,5))
        self.feature_var = tk.StringVar(value="")
        self.feature_combo = ttk.Combobox(feature_frame, textvariable=self.feature_var, 
                                         values=[], state="readonly", width=12)
        self.feature_combo.pack(side=tk.LEFT, padx=5)
        self.feature_combo.bind('<<ComboboxSelected>>', self.on_feature_change)
        
        # Scaling controls
        ttk.Label(feature_frame, text="Y-Scale:").pack(side=tk.LEFT, padx=(20,5))
        self.scale_var = tk.StringVar(value="Auto")
        scale_combo = ttk.Combobox(feature_frame, textvariable=self.scale_var, 
                                 values=["Auto", "±1", "±5", "±10", "±20", "±50", "±100"], 
                                 state="readonly", width=8)
        scale_combo.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = ttk.Button(feature_frame, text="Clear", command=self.clear_data)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.detection_label = ttk.Label(status_frame, text="Waiting for CSV header detection...", 
                                        foreground="orange")
        self.detection_label.pack(side=tk.LEFT)
        
        self.data_count_label = ttk.Label(status_frame, text="Data points: 0")
        self.data_count_label.pack(side=tk.RIGHT)
        
        self.setup_plot()
        
    def setup_plot(self):
        # Create matplotlib figure with explicit subplot adjustments
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.patch.set_facecolor('white')
        
        # Manually adjust subplot to leave room for labels
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        
        # Style the plot like an oscilloscope
        self.ax.set_facecolor('black')
        self.ax.grid(True, color='green', alpha=0.3, linestyle='-', linewidth=0.5)
        self.ax.set_xlim(0, self.max_points)
        self.ax.set_ylim(-1, 1)  # Initial range
        
        # Force initial ticks
        x_ticks = [0, 100, 200, 300, 400, 500]
        y_ticks = [-1, -0.5, 0, 0.5, 1]
        self.ax.set_xticks(x_ticks)
        self.ax.set_yticks(y_ticks)
        
        # Create empty line
        self.line, = self.ax.plot([], [], color='lime', linewidth=2)
        
        # Labels
        self.ax.set_xlabel('Sample Number', color='white', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Value', color='white', fontsize=14, fontweight='bold')
        self.ax.set_title('Dynamic CSV Oscilloscope - Waiting for data...', color='white', fontsize=16, fontweight='bold')
        
        # Force tick parameters
        self.ax.tick_params(axis='x', colors='white', labelsize=12, width=2, length=6)
        self.ax.tick_params(axis='y', colors='white', labelsize=12, width=2, length=6)
        
        # Make sure all spines are white and visible
        for spine in self.ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(2)
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Force initial draw
        self.canvas.draw()
        
        # Start animation
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=20, blit=False)  # Faster update
        
    def detect_csv_header(self, line):
        """Detect CSV header and initialize data structures"""
        try:
            # Parse header line
            self.columns = [col.strip() for col in line.split(',')]
            
            # Initialize data storage for each column
            self.sensor_data = {}
            for col in self.columns:
                self.sensor_data[col] = deque(maxlen=self.max_points)
            
            # Update GUI
            self.feature_combo['values'] = self.columns
            if self.columns:
                self.current_feature = self.columns[0]
                self.feature_var.set(self.current_feature)
            
            # Update status
            self.header_detected = True
            self.detection_label.config(text=f"Detected {len(self.columns)} columns: {', '.join(self.columns)}", 
                                       foreground="green")
            
            # Update plot title
            self.ax.set_title(f'Dynamic CSV Oscilloscope - {len(self.columns)} signals detected', 
                             color='white', fontsize=16, fontweight='bold')
            
            print(f"CSV Header detected: {self.columns}")
            return True
            
        except Exception as e:
            print(f"Error detecting CSV header: {e}")
            return False
    
    def on_feature_change(self, event):
        self.current_feature = self.feature_var.get()
        if self.current_feature:
            self.ax.set_ylabel(f'{self.current_feature}', color='white', fontsize=14, fontweight='bold')
            self.ax.set_title(f'Dynamic CSV Oscilloscope - {self.current_feature}', 
                             color='white', fontsize=16, fontweight='bold')
            self.canvas.draw()
        
    def clear_data(self):
        for key in self.sensor_data:
            self.sensor_data[key].clear()
        self.data_buffer.clear()
        self.data_counter = 0
        
        # Clear the queue
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except:
                break
        
    def toggle_connection(self):
        if not self.running:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        try:
            port = self.port_entry.get()
            self.serial_port = serial.Serial(port, 115200, timeout=0.1)  # Shorter timeout
            time.sleep(2)  # Wait for Arduino to reset
            
            self.running = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(foreground="green")
            
            # Reset detection
            self.header_detected = False
            self.detection_label.config(text="Waiting for CSV header detection...", foreground="orange")
            
            # Clear old data
            self.clear_data()
            
            # Start reading thread with higher priority
            self.read_thread = threading.Thread(target=self.read_serial_data)
            self.read_thread.daemon = True
            self.read_thread.start()
            
        except Exception as e:
            tk.messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
    
    def disconnect(self):
        self.running = False
        if self.serial_port:
            self.serial_port.close()
        
        self.connect_btn.config(text="Connect")
        self.status_label.config(foreground="red")
    
    def read_serial_data(self):
        """High-priority thread to capture ALL serial data"""
        buffer = ""
        
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    # Read all available data at once
                    chunk = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        # Skip Arduino initialization messages
                        if any(word in line.lower() for word in ['initializing', 'successful', 'failed']):
                            continue
                        
                        # Detect header if not already detected
                        if not self.header_detected:
                            # Check if this looks like a header (contains letters/names, not just numbers)
                            if any(char.isalpha() for char in line) and ',' in line:
                                if self.detect_csv_header(line):
                                    continue
                        
                        # Process data if header is detected
                        if self.header_detected:
                            self.process_data_line(line)
                
                time.sleep(0.001)  # Very short sleep to maximize data capture
                
            except Exception as e:
                print(f"Error reading data: {e}")
                time.sleep(0.01)
    
    def process_data_line(self, line):
        """Process a single data line and add to queue"""
        try:
            parts = line.split(',')
            if len(parts) == len(self.columns):
                # Parse all values
                values = []
                for i, part in enumerate(parts):
                    try:
                        # Try to convert to float, fallback to int, then string
                        if '.' in part:
                            values.append(float(part))
                        else:
                            values.append(int(part))
                    except ValueError:
                        values.append(0.0)  # Default value for unparseable data
                
                # Add to queue for GUI thread
                self.data_queue.put(values)
                
        except Exception as e:
            print(f"Error processing data line '{line}': {e}")
    
    def update_plot(self, frame):
        """Update plot from data queue"""
        # Process all queued data points
        points_processed = 0
        while not self.data_queue.empty() and points_processed < 100:  # Limit processing per frame
            try:
                values = self.data_queue.get_nowait()
                
                # Store data
                self.data_buffer.append(self.data_counter)
                for i, col in enumerate(self.columns):
                    self.sensor_data[col].append(values[i])
                
                self.data_counter += 1
                points_processed += 1
                
            except queue.Empty:
                break
        
        # Update data count display
        self.data_count_label.config(text=f"Data points: {self.data_counter}")
        
        # Update plot if we have data and a selected feature
        if (self.current_feature and 
            len(self.data_buffer) > 1 and 
            len(self.sensor_data[self.current_feature]) > 1):
            
            # Get current data
            x_data = list(self.data_buffer)
            y_data = list(self.sensor_data[self.current_feature])
            
            # Update line data
            self.line.set_data(x_data, y_data)
            
            # Handle Y-axis scaling
            scale_option = self.scale_var.get()
            if scale_option == "Auto":
                # Auto-scale Y axis
                if y_data:
                    y_min, y_max = min(y_data), max(y_data)
                    y_range = y_max - y_min
                    if y_range == 0:
                        y_range = 1
                    margin = y_range * 0.1
                    new_y_min = y_min - margin
                    new_y_max = y_max + margin
                    self.ax.set_ylim(new_y_min, new_y_max)
                    
                    # Update Y ticks for auto scale
                    tick_range = new_y_max - new_y_min
                    tick_step = tick_range / 6  # 6 divisions
                    y_ticks = []
                    for i in range(7):  # 7 tick marks
                        tick_val = new_y_min + i * tick_step
                        y_ticks.append(round(tick_val, 2))
                    
                    self.ax.set_yticks(y_ticks)
            else:
                # Manual scaling
                scale_val = float(scale_option.replace('±', ''))
                self.ax.set_ylim(-scale_val, scale_val)
                tick_step = scale_val / 4  # 8 divisions total
                y_ticks = []
                for i in range(9):  # 9 tick marks (-scale to +scale)
                    tick_val = -scale_val + i * tick_step
                    y_ticks.append(round(tick_val, 1))
                self.ax.set_yticks(y_ticks)
            
            # X-axis: always show full buffer range (fixed window)
            if x_data:
                latest_sample = x_data[-1]
                # Keep X axis fixed to buffer size, but shift view if needed
                x_min = max(0, latest_sample - self.max_points + 1)
                x_max = x_min + self.max_points
                self.ax.set_xlim(x_min, x_max)
                
                # Update X ticks (every 100 samples)
                x_tick_step = 100
                x_ticks = []
                current_x = int((x_min // x_tick_step + 1) * x_tick_step)
                while current_x <= x_max:
                    x_ticks.append(current_x)
                    current_x += x_tick_step
                self.ax.set_xticks(x_ticks)
        
        return [self.line]

if __name__ == "__main__":
    root = tk.Tk()
    app = DynamicCSVOscilloscope(root)
    
    def on_closing():
        app.disconnect()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
