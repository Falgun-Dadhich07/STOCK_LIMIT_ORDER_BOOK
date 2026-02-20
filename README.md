# IIM-A-Project-FAC



This project is a web-based trading system that simulates a stock limit order book, allowing users to place, modify, and cancel buy/sell orders. It is designed for educational and demonstration purposes.

## Features

- User registration, login, and password reset
- Place buy and sell limit orders
- Modify or cancel existing orders
- Real-time order book and trade updates using Redis
- Bulk user creation and deletion via CSV upload (admin only)
- Download order book and trade data as CSV

## Prerequisites

- Python 3.8+
- Django 3.x or 4.x
- Redis (for real-time features)
- Node.js & npm (if frontend build is required)

## Docker Setup (Recommended)

1. **Run with Docker Compose:**
   ```sh
   docker-compose up --build
   ```
   The application will be available at `http://localhost:8000`.

2. **Create Admin User (in a new terminal):**
   ```sh
   docker-compose exec web python manage.py createsuperuser
   ```

3. **Stop the services:**
   ```sh
   docker-compose down
   ```

## Installation and Setup (Manual)

1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd STOCK_LIMIT_ORDER_BOOK
   ```
2. **Create a virtual environment and activate it:**
   ```sh
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. **Install the required packages:**
   ```sh
   pip install -r requirements.txt
   ```

4. Redis Server Setup
```sh
   sudo apt update && sudo apt install redis-server
    sudo apt update && sudo apt install redis-server
    redis-cli ping
```

6. **Set up the database:**
   ```sh
   python manage.py migrate
   ```
7. **Create a superuser (admin) account:**
   ```sh
   python manage.py createsuperuser
   ```
8. **Run the development server:**
   ```sh
   python manage.py runserver
   ```
9. **Access the application:**
   Open your web browser and go to `http://127.0.0.1:8000/`.

## Usage

- Register a new account or log in with an existing account.
- Place limit orders for buying or selling stocks.
- Modify or cancel your existing orders as needed.
- Admin users can manage users and view all orders.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add your feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Create a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
