# PDF AudioBook Reader

A web-based PDF audiobook reader that converts PDF text to speech using Python Flask and pyttsx3.

## 🌟 Features

- 📄 Upload PDF files through a modern web interface
- 🎵 Text-to-speech conversion with pyttsx3
- 📖 Start reading from any page
- ⏹️ Stop/start controls
- 🌐 Web-based interface accessible from any browser
- 📱 Responsive design for mobile and desktop

## 🚀 Live Demo

Visit the live application: [Your App URL will be here]

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7+
- Git

### Local Development

1. **Clone the repository:**

   ```bash
   git clone https://github.com/abdullahmahfouz/audio-book.git
   cd audio-book
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python main.py
   ```

5. **Open your browser:**

   ```
   http://localhost:3000
   ```

## 🌐 Deployment Options

### Option 1: Render.com (Free & Easy)

1. Fork this repository
2. Create account on [Render.com](https://render.com)
3. Connect your GitHub account
4. Create new Web Service
5. Select this repository
6. Deploy automatically!

### Option 2: Railway

1. Create account on [Railway.app](https://railway.app)
2. Connect GitHub repository
3. Deploy with one click

### Option 3: Heroku

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Deploy: `git push heroku main`

## 📁 Project Structure

```
audio-book/
├── main.py              # Flask application
├── templates/
│   └── index.html       # Web interface
├── requirements.txt     # Python dependencies
├── Procfile            # Deployment configuration
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## 🔧 Configuration

The app uses environment variables for configuration:

- `PORT`: Server port (default: 3000)
- `MAX_CONTENT_LENGTH`: Max file upload size (default: 16MB)

## 🎯 Usage

1. **Upload PDF**: Drag and drop or click to select a PDF file
2. **Choose Start Page**: Optionally select which page to start reading from
3. **Start Reading**: Click the "Start Reading" button
4. **Listen**: The app will read the PDF aloud using text-to-speech
5. **Stop Anytime**: Use the "Stop Reading" button to pause

## 🐛 Troubleshooting

### Common Issues

**Audio not working:**
- Check speaker/headphone volume
- Ensure browser allows audio playbook
- Try refreshing the page

**File upload fails:**
- Ensure PDF is under 16MB
- Check PDF contains readable text (not just images)
- Try a different PDF file

**App not starting:**
- Check Python version (3.7+)
- Verify all dependencies installed
- Check port availability

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature-name`
5. Submit Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**Abdullah Mahfouz**
- GitHub: [@abdullahmahfouz](https://github.com/abdullahmahfouz)

## ⭐ Support

If you found this project helpful, please give it a star on GitHub!

## 🔄 Updates

Check the [Releases](https://github.com/abdullahmahfouz/audio-book/releases) page for latest updates and features.
