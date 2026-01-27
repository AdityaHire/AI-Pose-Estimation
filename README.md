# 🏋️ Fitness Trainer with AI Pose Estimation

An AI-powered web application that tracks your exercises using computer vision and provides real-time form feedback with scoring.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Pose-orange.svg)

---

## ✨ Features

- 📷 **Real-time Pose Estimation** using MediaPipe
- 🎯 **18 Built-in Exercises** - Full body workout coverage
- 📊 **Form Score System** (0-100) with A-F grading
- ⚙️ **YAML-based Exercise Definitions** - Add new exercises without writing code!
- 🔄 **Automatic Rep Counting** with state machine logic
- 💬 **Real-time Form Feedback** - Instant correction tips
- 📈 **FPS Tracking** for performance monitoring
- 🌐 **Web Interface** - Works in any modern browser

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Web UI)                             │
│         index.html ← video stream (MJPEG) ← form feedback            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTP/WebSocket
┌────────────────────────────────▼────────────────────────────────────┐
│                         BACKEND (Flask)                              │
│                            app.py                                    │
│   • Video capture & streaming                                        │
│   • REST API endpoints                                               │
│   • Session management                                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                      EXERCISE ENGINE                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  BaseExercise  │  │    Loader      │  │     Engine     │         │
│  │   (FSM Core)   │  │  (YAML→Obj)    │  │   (Wrapper)    │         │
│  │                │  │                │  │                │         │
│  │ • State Machine│  │ • Parse YAML   │  │ • process_frame│         │
│  │ • Rep Counter  │  │ • Validate     │  │ • draw_overlay │         │
│  │ • Form Score   │  │ • Create Obj   │  │ • draw_score   │         │
│  │ • Feedback     │  │                │  │                │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│         ▲                                                            │
│         │ inheritance                                                │
│  ┌──────┴───────┐  ┌────────────────┐                               │
│  │  Bilateral   │  │   Duration     │                               │
│  │  Exercise    │  │   Exercise     │                               │
│  │ (L/R sides)  │  │ (time-based)   │                               │
│  └──────────────┘  └────────────────┘                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ loads
┌────────────────────────────────▼────────────────────────────────────┐
│                    YAML DEFINITIONS (18 exercises)                   │
│  squat.yaml │ push_up.yaml │ plank.yaml │ deadlift.yaml │ ...       │
│                                                                      │
│  Each YAML contains:                                                 │
│  • Angle definitions (landmarks, ranges)                             │
│  • State machine (states, transitions, conditions)                   │
│  • Counter rules (when to count a rep)                               │
│  • Form feedback rules (warnings, priorities)                        │
│  • Tempo guidance (up/down/hold timing)                              │
│  • Visualization config (colors, highlighted joints)                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Form Score System

The app calculates a **Form Score (0-100)** for each exercise session:

| Component | Weight | Description |
|-----------|--------|-------------|
| Angle Accuracy | 40% | How close your angles are to ideal |
| Tempo Compliance | 30% | Following the recommended speed |
| Form Feedback | 30% | Penalty for triggered warnings |

### Grade Scale
| Score | Grade | Color |
|-------|-------|-------|
| 90-100 | A | 🟢 Green |
| 80-89 | B | 🔵 Blue |
| 70-79 | C | 🟡 Yellow |
| 60-69 | D | 🟠 Orange |
| 0-59 | F | 🔴 Red |

---

## 📁 Available Exercises (18)

### Upper Body
- 💪 **Hammer Curl** - Bicep curl with neutral grip
- 💪 **Bicep Curl** - Classic bicep exercise (bilateral)
- 💪 **Tricep Dip** - Chair/bench dips for triceps
- 💪 **Shoulder Press** - Overhead pressing
- 💪 **Lateral Raise** - Side delt raises
- 💪 **Push Up** - Classic chest exercise

### Lower Body
- 🦵 **Squat** - Bodyweight squat
- 🦵 **Lunge** - Forward lunge (bilateral)
- 🦵 **Side Lunge** - Lateral lunge
- 🦵 **Deadlift** - Romanian deadlift for hamstrings
- 🦵 **Glute Bridge** - Hip bridge for glutes
- 🦵 **Calf Raise** - Standing calf raises
- 🦵 **Wall Sit** - Isometric hold (duration)

### Cardio / Full Body
- 🔥 **Mountain Climber** - Dynamic core/cardio
- 🔥 **High Knees** - Running in place
- 🔥 **Jumping Jack** - Classic cardio move
- 🔥 **Leg Raise** - Lying leg raises for abs
- 🧘 **Plank** - Core hold (duration)

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/fitness-trainer-pose-estimation.git
cd fitness-trainer-pose-estimation

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://127.0.0.1:5000**

---

## ➕ Adding New Exercises

**No coding required!** Just create a YAML file:

### Step 1: Create YAML in `exercises/definitions/`

```yaml
# exercises/definitions/my_new_exercise.yaml
name: "My New Exercise"
type: "standard"  # or "bilateral" / "duration"
description: "Description of the exercise"

# Define body angles to track
angles:
  primary_angle:
    landmarks: [11, 13, 15]  # MediaPipe landmark IDs
    range: [30, 170]         # Valid angle range

# State machine definition
states:
  - name: "START"
    condition:
      angle: "primary_angle"
      operator: ">"
      value: 150
    next_state: "MIDDLE"
    feedback: "Starting position"
    
  - name: "MIDDLE"
    condition:
      angle: "primary_angle"
      operator: "<"
      value: 60
    next_state: "END"
    feedback: "Good form!"
    
  - name: "END"
    condition:
      angle: "primary_angle"
      operator: ">"
      value: 150
    next_state: "START"
    feedback: "Rep complete!"

# When to count a rep
counter:
  increment_on: "END"

# Form warnings
feedback:
  - name: "form_warning"
    description: "Bad form detected"
    angle: "primary_angle"
    condition:
      operator: "<"
      value: 30
    message: "Don't go too low!"
    priority: 1

# Tempo in seconds
tempo:
  up_seconds: 1.0
  down_seconds: 2.0
  hold_seconds: 0.5

# Display settings
visualization:
  primary_angle: "primary_angle"
  show_angles: ["primary_angle"]
  highlight_landmarks: [11, 13, 15]
  color_scheme: "green"
```

### Step 2: Test

```bash
python test_engine.py
```

### Step 3: Use

Restart the app - your exercise is now available!

---

## 📍 MediaPipe Landmarks Reference

```
 0  = NOSE                    
11  = LEFT_SHOULDER       12 = RIGHT_SHOULDER
13  = LEFT_ELBOW          14 = RIGHT_ELBOW
15  = LEFT_WRIST          16 = RIGHT_WRIST
23  = LEFT_HIP            24 = RIGHT_HIP
25  = LEFT_KNEE           26 = RIGHT_KNEE
27  = LEFT_ANKLE          28 = RIGHT_ANKLE
31  = LEFT_FOOT_INDEX     32 = RIGHT_FOOT_INDEX
```

---

## 📂 Project Structure

```
fitness-trainer-pose-estimation/
├── 📄 app.py                    # Flask application + video streaming
├── 📄 main.py                   # CLI runner (standalone)
├── 📄 test_engine.py            # Unit tests
├── 📄 requirements.txt
│
├── 📁 exercises/
│   ├── 📄 base_exercise.py      # FSM engine (BaseExercise, Bilateral, Duration)
│   ├── 📄 loader.py             # YAML loader & validator
│   ├── 📄 engine.py             # High-level API wrapper
│   └── 📁 definitions/          # 🎯 YAML exercise files (18 exercises)
│       ├── squat.yaml
│       ├── push_up.yaml
│       ├── hammer_curl.yaml
│       ├── bicep_curl.yaml
│       ├── tricep_dip.yaml
│       ├── shoulder_press.yaml
│       ├── lateral_raise.yaml
│       ├── lunge.yaml
│       ├── side_lunge.yaml
│       ├── deadlift.yaml
│       ├── glute_bridge.yaml
│       ├── calf_raise.yaml
│       ├── wall_sit.yaml
│       ├── plank.yaml
│       ├── mountain_climber.yaml
│       ├── high_knees.yaml
│       ├── jumping_jack.yaml
│       └── leg_raise.yaml
│
├── 📁 pose_estimation/
│   ├── 📄 estimation.py         # MediaPipe wrapper
│   └── 📄 angle_calculation.py  # Angle math
│
├── 📁 feedback/
│   ├── 📄 indicators.py         # UI components
│   ├── 📄 information.py        # Exercise metadata
│   └── 📄 layout.py
│
├── 📁 templates/
│   ├── 📄 index.html            # Main exercise page
│   └── 📄 dashboard.html        # Stats dashboard
│
└── 📁 static/
    ├── 📁 css/
    ├── 📁 js/
    └── 📁 images/
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/video_feed` | GET | MJPEG video stream |
| `/start_exercise` | POST | Start tracking an exercise |
| `/stop_exercise` | POST | Stop current exercise |
| `/get_status` | GET | Get current rep count & form score |
| `/exercises` | GET | List all available exercises |
| `/dashboard` | GET | View workout history |

---

## 🛠️ Technologies

- **Flask** - Web framework
- **OpenCV** - Computer vision & video processing
- **MediaPipe** - Google's pose estimation model
- **PyYAML** - Exercise definition parsing
- **HTML/CSS/JS** - Frontend

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-exercise`)
3. Add your YAML exercise definition
4. Run tests (`python test_engine.py`)
5. Commit changes (`git commit -am 'Add new exercise'`)
6. Push to branch (`git push origin feature/new-exercise`)
7. Create Pull Request

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) by Google
- [OpenCV](https://opencv.org/) community
- [Flask](https://flask.palletsprojects.com/) framework

---

**Made with ❤️ for fitness enthusiasts**
