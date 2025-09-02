# Dynamic CSV Oscilloscope

A real-time data visualization tool that automatically detects and plots CSV data streams from Arduino or any serial device. Perfect for sensor monitoring, data logging visualization, and real-time signal analysis.

## Features

- **Auto-detection**: Automatically detects CSV column headers and adapts to any data format
- **Real-time plotting**: Captures and displays every single data point with minimal latency
- **Universal compatibility**: Works with any Arduino project that outputs CSV format
- **Oscilloscope-style interface**: Professional black background with green grid and lime trace
- **Flexible scaling**: Auto-scale or manual Y-axis scaling (±1 to ±100)
- **Signal switching**: Toggle between different sensor readings using dropdown menu
- **High-performance**: Optimized for fast data capture without missing samples

## Requirements

```bash
pip install pyserial matplotlib numpy
```

## Quick Start

1. **Prepare your Arduino code** to output CSV format with headers:
   ```cpp
   // In setup()
   Serial.println("AccX,AccY,AccZ,GyroX,GyroY,GyroZ,Temp");
   
   // In loop()
   Serial.print(accelX);
   Serial.print(",");
   Serial.print(accelY);
   // ... continue for all values
   Serial.println(temperature);
   ```

2. **Run the oscilloscope**:
   ```bash
   python dynamic_oscilloscope.py
   ```

3. **Connect and monitor**:
   - Enter your COM port (e.g., COM3, /dev/ttyUSB0)
   - Click "Connect" 
   - The tool automatically detects your CSV format
   - Select signals from the dropdown to visualize
   - Use Y-Scale options for optimal viewing

## Usage Guide

### Connection Setup
1. Upload your CSV-outputting Arduino sketch
2. Note the COM port your Arduino is connected to
3. Launch the oscilloscope application
4. Enter the COM port in the "Port" field
5. Click "Connect"

### Interface Elements
- **Port field**: Enter your serial port (COM3, /dev/ttyUSB0, etc.)
- **Connect button**: Start/stop serial connection
- **Status indicator**: Green dot = connected, Red dot = disconnected  
- **Signal dropdown**: Switch between detected CSV columns
- **Y-Scale dropdown**: Choose between Auto-scale or fixed ranges (±1 to ±100)
- **Clear button**: Reset all data and restart plotting
- **Status bar**: Shows detection status and live data point counter

### Automatic Detection
The oscilloscope automatically:
- Detects CSV header lines (lines containing letters and commas)
- Parses column names and creates dropdown options
- Adapts to any number of columns (3, 7, 10, or more)
- Handles different data types (integers, floats)

### Supported Arduino Output Formats

**MPU6050 Example:**
```
AccX,AccY,AccZ,gyroX,gyroY,gyroZ,temperature
-2.45,0.98,9.81,0.02,-0.01,0.00,25
```

**Temperature Sensors:**
```
Temp1,Temp2,Temp3,Humidity
23.5,24.1,22.8,65
```

**Custom Sensors:**
```
Pressure,Altitude,Light,Sound,Vibration
1013.25,120.5,450,35,0.12
```

## Performance Tips

- Use baud rate 115200 for best performance
- Keep Arduino `delay()` reasonable (100-1000ms)
- The oscilloscope captures ALL transmitted data points
- For high-frequency data (>100Hz), consider reducing the sample window

## Troubleshooting

**"Waiting for CSV header detection..."**
- Ensure your Arduino outputs a header line with column names
- Check that the header contains letters (not just numbers)
- Verify serial connection and baud rate

**Missing data points or lag:**
- Check your Arduino's `delay()` value
- Ensure stable USB connection
- Try different COM ports if connection is unstable

**Connection failed:**
- Verify correct COM port
- Close Arduino IDE Serial Monitor (can't share ports)
- Check if port is in use by other applications

## Example Arduino Code

```cpp
#include <Arduino.h>
#include <MPU6050.h>

MPU6050 mpu;
int16_t ax, ay, az, gx, gy, gz, temp;

void setup() {
  Serial.begin(115200);
  mpu.initialize();
  
  // Send CSV header
  Serial.println("AccX,AccY,AccZ,GyroX,GyroY,GyroZ,Temperature");
}

void loop() {
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  temp = mpu.getTemperature();
  
  // Send CSV data
  Serial.print((ax/16384.0)*9.81);  Serial.print(",");
  Serial.print((ay/16384.0)*9.81);  Serial.print(",");
  Serial.print((az/16384.0)*9.81);  Serial.print(",");
  Serial.print(gx/131.0*(3.14/180)); Serial.print(",");
  Serial.print(gy/131.0*(3.14/180)); Serial.print(",");
  Serial.print(gz/131.0*(3.14/180)); Serial.print(",");
  Serial.println(temp/340.0 + 36.53);
  
  delay(100);  // 10Hz sampling rate
}
```

## License

MIT License - Feel free to use in your projects!
