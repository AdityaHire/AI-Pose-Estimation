# AI Pose Estimation

An AI-powered fitness trainer that tracks your exercise form in real-time using pose estimation.

## Features

- 18 different exercises supported (push-ups, squats, lunges, bicep curls, etc.)
- Real-time form analysis with visual feedback
- Form score calculation
- Workout history tracking
- Video analysis support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AdityaHire/AI-Pose-Estimation.git
cd AI-Pose-Estimation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python app.py
```

Open your browser and navigate to `http://localhost:5000`

## How It Works

- Uses MediaPipe for pose detection
- Analyzes joint angles and body positions
- Provides real-time feedback on exercise form
- Tracks reps and calculates form scores

## Supported Exercises

Bicep Curl, Calf Raise, Deadlift, Glute Bridge, Hammer Curl, High Knees, Jumping Jack, Lateral Raise, Leg Raise, Lunge, Mountain Climber, Plank, Push-up, Shoulder Press, Side Lunge, Squat, Tricep Dip, Wall Sit
