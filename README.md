# IwiConnect - IWI Community Management Platform

A comprehensive Django web application for managing Iwi and Hapu communities, consultations, events, and notices in New Zealand.

## 🌟 Features

### Core Functionality
- **User Management**: Registration, authentication, and profile management with document verification
- **IWI & Hapu Management**: Hierarchical organization management with archival capabilities
- **Consultation System**: Create and manage community consultations with proposal submissions and voting
- **Event Management**: Calendar-based event system with attendee tracking
- **Notice Board**: Community announcements and engagement tracking
- **Leadership Management**: Assign and manage IWI and Hapu leaders

### User Roles & Permissions
- **Regular Members**: View consultations, events, and notices
- **Hapu Leaders**: Manage hapu-specific content and members
- **Iwi Leaders**: Manage iwi-wide content and hapu leaders
- **Administrators**: Full system access and user verification

## 🏗️ Architecture

### Django Apps
- **core**: User authentication, IWI/Hapu models, and base functionality
- **usermgmt**: User management and leadership assignments
- **consultation**: Community consultation and proposal system
- **events**: Event creation and management
- **notice**: Community announcements and notices
- **iwimgmt**: IWI management interface
- **hapumgmt**: Hapu management interface

### Database Schema
- **CustomUser**: Extended user model with IWI/Hapu affiliations
- **Iwi/Hapu**: Hierarchical community structure
- **Consultation/Proposal**: Community decision-making system
- **Event**: Community event management
- **Notice**: Community announcements

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd iwi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DB_NAME=iwi_web
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306

   # Email Configuration
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   FROM_EMAIL=IwiConnect <noreply@yourdomain.com>

   # Application Settings
   APP_NAME=IwiConnect
   LOGO_URL=https://your-logo-url.com/logo.png
   ```

5. **Set up MySQL database**
   ```sql
   CREATE DATABASE iwi_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Seed initial data (optional)**
   ```bash
   python seeders/seed_admin.py
   python seeders/seed_iwi_hapu.py
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Main site: http://localhost:8000

## 📁 Project Structure

```
iwi/
├── consultation/          # Consultation and proposal management
├── core/                  # Core models, authentication, and base functionality
├── events/               # Event management system
├── hapumgmt/             # Hapu management interface
├── iwimgmt/              # IWI management interface
├── iwi_web_app/          # Main Django project settings
├── notice/               # Notice board and announcements
├── usermgmt/             # User management and leadership
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
├── logs/                 # Application logs
├── seeders/              # Database seeding scripts
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## 🔧 Configuration

### Database
The application uses MySQL as the primary database. Configure your database settings in the `.env` file.

### Email
Configure SMTP settings for email notifications (password resets, account approvals, etc.) in the `.env` file.

### Timezone
The application is configured for New Zealand timezone (`Pacific/Auckland`).

## 🛠️ Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
```

### Database Backup
```bash
python manage.py dumpdata > backup.json
```

### Database Restore
```bash
python manage.py loaddata backup.json
```

## 📧 Email Features

The application includes several email notifications:
- Welcome emails for new users
- Account approval/rejection notifications
- Password reset emails
- Consultation notifications

## 🔐 Security Features

- Custom user authentication with email verification
- Password reset functionality with secure tokens
- File upload security for citizenship documents
- CSRF protection
- Session management

## 📝 Logging

Application logs are stored in the `logs/` directory:
- `django.log` - General application logs
- `email.log` - Email-related logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the Django documentation for framework-specific questions

## 🔄 Version History

- **v1.0.0** - Initial release with core IWI management features
- Consultation system with proposal voting
- Event management with calendar integration
- Notice board with engagement tracking
- User management with role-based permissions

---

**Built with Django 5.2+ and Python 3.8+** 