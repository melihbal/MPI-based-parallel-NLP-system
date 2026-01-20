# Multi-Layer Transshipment Optimizer

This project implements a Linear Programming (LP) model to solve a multi-layer transshipment problem. It determines the optimal flow of goods between sources, intermediaries, and destinations to **minimize total transportation costs**.

The solution uses the **PuLP** library to define the decision variables, objective function, and constraints, and includes sensitivity analysis (shadow prices and reduced costs) to evaluate the stability of the optimal solution.

## Project Structure

- **`solution.py`**: The main script that defines the LP model, constraints, and solves for the optimal cost. It also outputs sensitivity analysis reports.
- **`test_cases/`**: Directory containing input data or different scenario configurations for testing the model.

## Getting Started

### Prerequisites

You need Python 3.x installed. The project relies on the `PuLP` library for optimization.

### Installation

1. Clone the repository:
~~~bash
git clone https://github.com/YOUR_USERNAME/PythonProject26.git
~~~

2. Install the required dependencies:
~~~bash
pip install pulp
~~~

## Usage

Run the main solution script from the terminal:

~~~bash
python solution.py
~~~

The script will output:
1. **Optimization Status** (Optimal/Infeasible).
2. **Total Minimum Cost**.
3. **Optimal Flow Quantities** for each route.
4. **Sensitivity Analysis** (Shadow Prices and Reduced Costs).

## Features

- **Cost Minimization**: Uses the Simplex algorithm to find the lowest possible transport cost.
- **Constraint Handling**: Accounts for supply limits, demand requirements, and intermediate node flow conservation.
- **Sensitivity Analysis**: Provides insights into how changes in supply or demand would impact the total cost (Shadow Prices).
