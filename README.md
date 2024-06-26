# Althea - Building a Financial Credit Core with Django

## Objective & Planning

Althea is a project focused on developing a basic Credit Core system for simple loans using Django, Python, NumPy, and Pandas. A Credit Core is crucial for financial institutions as it analyzes loan applications and creates amortization schedules. This project will concentrate on building the backend for calculating and managing loan amortizations, providing a flexible and customizable solution for financial institutions.

## Why a Credit Core?

In the fintech space, every financial institution requires a core system to manage credit operations. Institutions face a choice between building this system in-house or leasing it. While building in-house is complex and costly, leasing can be expensive and inflexible. Althea aims to provide a foundational layer for a broader financial infrastructure that is both flexible and customizable.

## System Build Approach

We will use Django for the backend. Some knowledge of Django and Python is required, as the project will cover advanced technical concepts. For those with no programming experience, explanations will be provided in a simple and concise manner.

### Prerequisites

To get started, ensure you have the following installed:

- Python 3
- Django
- Pipenv
- Command-line interface (e.g., Windows PowerShell)
- GitHub account

## Project Setup

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/your-username/althea.git
   cd althea
   ```

2. **Install Dependencies:**

   ```sh
   pipenv install
   ```

3. **Run Migrations:**

   ```sh
   python manage.py migrate
   ```

4. **Start the Development Server:**

   ```sh
   python manage.py runserver
   ```

### Features

- Credit Origination Flow: Onboard the user, approve the credit request, and manage disbursements.
- Amortization Schedule Calculation: Generate amortization schedules for approved loans.

### Contribution

While the codebase for this project is maintained exclusively by me, I welcome and appreciate your contributions in the following ways:

- **Suggestions and Feedback:** Feel free to open issues to propose new features, report bugs, or provide feedback on the project.
- **Documentation:** You can suggest improvements or additions to the documentation by opening issues.
- **Testing:** Report any bugs or issues you encounter to help improve the project.
