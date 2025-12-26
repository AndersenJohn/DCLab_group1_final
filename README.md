# DCLab Group 1 Final Project - Buckshot

This repository contains the final project for the Digital Circuit Lab (DCLab). The project integrates an FPGA-based hardware system with a Unity game engine frontend, utilizing Python for communication and a Reinforcement Learning (RL) model.

## Project Overview

The system is designed to run on the **DE2-115 FPGA board**, communicating with a PC running a **Unity** application.
- **Hardware:** Handles real-time processing, game logic, and hardware interfaces.
- **Software:** Python scripts act as a bridge between the FPGA (via UART/RS232) and the Unity game.
- **AI:** Includes a Reinforcement Learning model, potentially for game AI or decision making.

## Repository Structure

### 1. Hardware (FPGA)
Located in the root and subdirectories:
- **`DE2_115/`**: Contains the top-level SystemVerilog modules and pin assignments for the DE2-115 board.
- **`game_logic/`**: Verilog/SystemVerilog modules defining the core rules and state machine of the game.
- **`encoder/`**: Modules for data encoding.
- **`rs232/`**: UART communication modules for data transfer between the FPGA and the PC.
- **`DCLab_Final.qpf` / `.qsf`**: Quartus Prime project files.

### 2. Game Frontend (Unity)
- **`buckshot/`**: The Unity project folder. Contains the game assets, scenes, and C# scripts for the visual interface.

### 3. Software Bridge (Python)
- **`python_code/`**: Scripts for handling communication.
    - `python_uart_to_json.py`: Reads data from the FPGA via UART and converts it to JSON for Unity.
    - `python_json_to_command.py`: Converts Unity commands to a format the FPGA can understand.
- **`python_test/`**: Testing scripts for the Python logic.

### 4. AI Model
- **`RL_Model/`**: Contains the Reinforcement Learning model resources.
    - `model_weight/`: Weights and biases for the neural network.
    - `RL_model.sv`: Hardware implementation of the RL model.

## Getting Started

### Prerequisites
- **Hardware:** Altera DE2-115 Development Board.
- **Software:**
    - Intel Quartus Prime (for FPGA synthesis).
    - Unity Hub & Editor (for the game frontend).
    - Python 3.x (with `pyserial` for UART communication).

### Setup
1.  **FPGA:** Open `DCLab_Final.qpf` in Quartus, compile the project, and program the DE2-115 board.
2.  **Unity:** Add the `buckshot` folder to Unity Hub and open the project.
3.  **Python:** Run the bridge scripts in `python_code/` to establish the connection between the board and the game.

## Team
- Group 1
