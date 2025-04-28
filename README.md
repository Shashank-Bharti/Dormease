# Dormease - Hostel Management System

Dormease is a web-based application designed to automate and streamline the hostel accommodation process at IIT Patna during academic programs like campus immersion. It features automated room allotments, student check-ins, and real-time updates, aiming to reduce administrative overhead and improve student experience.

## Features

- **Automated Room Allotment**: Room assignments based on alphabetical sorting and custom rules.
- **Digital Check-In System**: Students can check in using QR codes, minimizing physical queues and delays.
- **Real-Time Notifications**: Room availability and updates are sent instantly via email or app notifications, keeping students and admins informed.
- **Admin Dashboard**: Provides real-time statistics on room availability, student registrations, and hostel occupancy. It uses visual elements such as Donut graphs and counters for better decision-making.
- **Student Verification**: Each student’s identity is verified before allocation to ensure proper registration.
- **Issue Tracking**: Hostel-related issues (plumbing, inaccessibility, etc.) can be logged and tracked for timely resolution.
- **Scalability**: Currently web-based, but designed to scale with future extensions into mobile apps and QR-code-based services.
- **AI-Powered Error Handling**: Uses the OpenRouter API for intelligent error handling, including managing name typos during verification.
- **Version Control**: Git and GitHub are used for version control, ensuring smooth team collaboration.

## Installation

To run the project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/dormease.git
   cd dormease
   ```

2. **Install the required dependencies**: Make sure you have Python installed, then install the required packages using:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask application**: Start the application using:
   ```bash
   python app.py
   ```

The app will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQL
- **Real-Time Notifications**: Email, App Push Notifications
- **QR Code Verification**: jsQR (JavaScript)
- **AI Integration**: OpenRouter API for error handling
- **Version Control**: Git and GitHub for collaborative development

## Contributing

If you'd like to contribute, follow these steps:

1. **Fork the repository**
2. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Commit your changes**:
   ```bash
   git commit -am 'Add new feature'
   ```
4. **Push to the branch**:
   ```bash
   git push origin feature/your-feature
   ```
5. **Create a new Pull Request**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
