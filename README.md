# Farmer Management System

## Overview

The Farmer Management System is a Django-based web application designed to manage farmer records across different geographical blocks. It provides role-based access control, allowing different types of users (admin, supervisor, surveyor) to perform specific actions based on their permissions.

## Features

- **User Authentication and Role Management**: 
  - Custom user model with roles: Admin, Supervisor, and Surveyor.
  - Role-based access control to ensure secure and appropriate access to features.

- **Block Management**:
  - Admins can add, edit, and delete blocks.
  - Supervisors and Surveyors can view blocks they are assigned to.

- **Farmer Management**:
  - Add, edit, and delete farmer records.
  - Store farmer details including name, Aadhar ID, and associated documents.
  - Track which user added each farmer.

- **Dashboard and Profile Management**:
  - Role-specific dashboards for quick access to relevant information.
  - Users can view and edit their profiles and change passwords.

## Project Structure

- **Models**:
  - `Block`: Represents geographical or administrative units.
  - `User`: Custom user model extending Django's AbstractUser with role-based permissions.
  - `Farmer`: Represents individual farmers with personal details and documents.

- **Views**:
  - Authentication views for login and logout.
  - CRUD operations for blocks and farmers.
  - Profile management views.

- **Templates**:
  - Base templates for consistent styling.
  - Role-specific dashboards and forms for managing blocks and farmers.

- **Static Files**:
  - CSS for styling and layout.
  - JavaScript for interactive features.
  - Media files for user and farmer documents.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/farmer-management-system.git
   cd farmer-management-system
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   Open your browser and go to `http://127.0.0.1:8000/`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
