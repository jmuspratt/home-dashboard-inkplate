# Use the official PHP 8.1 image
FROM php:8.1-apache

# Install necessary PHP extensions
RUN apt-get update && apt-get install -y \
    libssl-dev \
    zlib1g-dev \
    unzip \
    && docker-php-ext-install pdo pdo_mysql

# Install Composer to manage PHP dependencies
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set up Google API Client Library
RUN composer require google/apiclient:^2.0

# Enable Apache rewrite module (optional, useful for routing)
RUN a2enmod rewrite

# Set the working directory in the container
WORKDIR /var/www/html

# Copy local files to container
COPY . /var/www/html

# Expose port 80
EXPOSE 80

# Set the default command to run Apache
CMD ["apache2-foreground"]