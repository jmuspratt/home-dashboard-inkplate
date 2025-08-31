# Home Dashboard Server

A PHP-based server component for the home dashboard that displays weather, calendar events, school lunches, and allowance tracking.

## Prerequisites

- Docker and Docker Compose
- Google Calendar API credentials
- Airtable API key and base ID

## Quick Start with Docker

1. **Clone the repository and navigate to the server directory:**

   ```bash
   cd server
   ```

2. **Set up your credentials:**

   - Place your Google Calendar service account JSON key file in the `creds/` directory
   - Update `config/config.php` with your specific API keys and IDs:
     - Google Calendar ID
     - Airtable API key
     - Airtable Base ID
     - Path to your Google service account key file

3. **Build and run the Docker container:**

   ```bash
   docker build -t home-dashboard-server .
   docker run -p 8080:80 home-dashboard-server
   ```

4. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8080`

## Manual Setup (without Docker)

### Requirements

- PHP 8.1 or higher
- Apache web server
- Composer
- PHP extensions: `pdo`, `pdo_mysql`

### Installation

1. **Install PHP dependencies:**

   ```bash
   composer install
   ```

2. **Configure your web server:**

   - Point your web server's document root to the server directory
   - Ensure Apache's rewrite module is enabled
   - Set appropriate file permissions

3. **Set up credentials and configuration:**
   - Follow step 2 from the Docker setup above

## Configuration

### Environment Variables

The application uses the following configuration files:

- `config/config.php` - Main configuration file containing:
  - Google Calendar ID
  - Google service account key file path
  - Airtable API key and Base ID

### Credentials Setup

1. **Google Calendar API:**

   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Place it in the `creds/` directory
   - Update the path in `config/config.php`

2. **Airtable API:**
   - Generate an API key from your Airtable account
   - Find your Base ID from the Airtable API documentation
   - Update both values in `config/config.php`

## Features

The dashboard displays:

- **Current Date** - Today's date with day of week
- **Weather** - Current weather conditions
- **School Lunch** - Daily lunch menu from Airtable
- **Calendar Events** - Upcoming events from Google Calendar
- **Allowances** - Transaction tracking for family members

## API Endpoints

- `GET /` - Main dashboard view
- `GET /?simple` - Simplified view (reduced formatting)

## Docker Container Details

- **Base Image:** PHP 8.1 with Apache
- **Exposed Port:** 80
- **Working Directory:** `/var/www/html`
- **Dependencies:** Google API Client, Airtable PHP SDK

## Development

To modify the dashboard:

1. Edit `functions.php` for data processing logic
2. Edit `index.php` for display layout
3. Rebuild the Docker container if using Docker

## Troubleshooting

- Ensure all API credentials are valid and have proper permissions
- Check that the Google service account has access to the specified calendar
- Verify Airtable API key has read access to the specified base
- Check Docker logs: `docker logs <container-id>`
