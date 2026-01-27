from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
import cv2
import threading
import time
import sys
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Import attempt with error handling
try:
    from pose_estimation.estimation import PoseEstimator
    # NEW: Import Exercise Engine
    from exercises.engine import ExerciseEngine
    from exercises.loader import get_available_exercises, get_exercise_info
    from utils.draw_text_with_background import draw_text_with_background
    logger.info("Successfully imported pose estimation modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Try to import WorkoutLogger with fallback
try:
    from db.workout_logger import WorkoutLogger
    workout_logger = WorkoutLogger()
    logger.info("Successfully initialized workout logger")
except ImportError:
    logger.warning("WorkoutLogger import failed, creating dummy class")
    
    class DummyWorkoutLogger:
        def __init__(self):
            pass
        def log_workout(self, *args, **kwargs):
            return {}
        def get_recent_workouts(self, *args, **kwargs):
            return []
        def get_weekly_stats(self, *args, **kwargs):
            return {}
        def get_exercise_distribution(self, *args, **kwargs):
            return {}
        def get_user_stats(self, *args, **kwargs):
            return {'total_workouts': 0, 'total_exercises': 0, 'streak_days': 0}
    
    workout_logger = DummyWorkoutLogger()

logger.info("Setting up Flask application")
app = Flask(__name__)
app.secret_key = 'fitness_trainer_secret_key'  # Required for sessions

# Global variables
camera = None
output_frame = None
lock = threading.Lock()
exercise_running = False
exercise_engine = ExerciseEngine()  # NEW: Global exercise engine
current_exercise_type = None
exercise_goal = 0
sets_completed = 0
sets_goal = 0
workout_start_time = None

# FPS tracking
fps_counter = 0
fps_start_time = time.time()
current_fps = 0

def initialize_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        # Optimize camera settings
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

def generate_frames():
    global output_frame, lock, exercise_running, exercise_engine
    global exercise_goal, sets_completed, sets_goal
    global fps_counter, fps_start_time, current_fps

    pose_estimator = PoseEstimator()

    # Initialize camera when video feed starts
    initialize_camera()

    while True:
        if camera is None:
            initialize_camera()
            time.sleep(0.1)
            continue
            
        success, frame = camera.read()
        if not success:
            continue
        
        # FPS calculation
        fps_counter += 1
        elapsed = time.time() - fps_start_time
        if elapsed >= 1.0:
            current_fps = fps_counter / elapsed
            fps_counter = 0
            fps_start_time = time.time()
        
        # Only process frames if an exercise is running
        if exercise_running and exercise_engine.exercise:
            # Process with pose estimation
            results = pose_estimator.estimate_pose(frame, exercise_engine.exercise_name)
            
            if results.pose_landmarks:
                # NEW: Use Exercise Engine to process frame
                result = exercise_engine.process_frame(frame, results.pose_landmarks.landmark)
                
                if result["success"]:
                    # Draw status overlay
                    exercise_engine.draw_status_overlay(frame, exercise_goal, sets_goal, sets_completed)
                    
                    # Draw Form Score
                    exercise_engine.draw_form_score(frame)
                    
                    # Check if rep goal is reached for current set
                    current_counter = exercise_engine.get_counter()
                    if current_counter >= exercise_goal:
                        sets_completed += 1
                        exercise_engine.reset()
                        
                        # Check if all sets are completed
                        if sets_completed >= sets_goal:
                            exercise_running = False
                            # Final form score display
                            avg_score = exercise_engine.exercise.avg_form_score if exercise_engine.exercise else 0
                            draw_text_with_background(frame, f"WORKOUT COMPLETE! Avg Score: {avg_score}", 
                                                    (frame.shape[1]//2 - 200, frame.shape[0]//2),
                                                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), (0, 200, 0), 2)
                        else:
                            draw_text_with_background(frame, f"SET {sets_completed} COMPLETE! Rest for 30 sec", 
                                                    (frame.shape[1]//2 - 200, frame.shape[0]//2),
                                                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), (0, 0, 200), 2)
        else:
            # Display welcome message if no exercise is running
            cv2.putText(frame, "Select an exercise to begin", (frame.shape[1]//2 - 180, frame.shape[0]//2),
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            
            # Show available exercises
            exercises = get_available_exercises()
            cv2.putText(frame, f"Available: {len(exercises)} exercises", (frame.shape[1]//2 - 120, frame.shape[0]//2 + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Display FPS
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (frame.shape[1] - 100, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                
        # Encode the frame in JPEG format
        with lock:
            output_frame = frame.copy()
            
        # Yield the frame in byte format
        ret, buffer = cv2.imencode('.jpg', output_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Home page with exercise selection"""
    logger.info("Rendering index page")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return f"Error rendering template: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """Dashboard page with workout statistics"""
    logger.info("Rendering dashboard page")
    try:
        # Get data for the dashboard
        recent_workouts = workout_logger.get_recent_workouts(5)
        weekly_stats = workout_logger.get_weekly_stats()
        exercise_distribution = workout_logger.get_exercise_distribution()
        user_stats = workout_logger.get_user_stats()
        
        # Format workouts for display
        formatted_workouts = []
        for workout in recent_workouts:
            formatted_workouts.append({
                'date': workout['date'],
                'exercise': workout['exercise_type'].replace('_', ' ').title(),
                'sets': workout['sets'],
                'reps': workout['reps'],
                'duration': f"{workout['duration_seconds'] // 60}:{workout['duration_seconds'] % 60:02d}"
            })
        
        # Calculate total workouts this week
        weekly_workout_count = sum(day['workout_count'] for day in weekly_stats.values())
        
        return render_template('dashboard.html',
                              recent_workouts=formatted_workouts,
                              weekly_workouts=weekly_workout_count,
                              total_workouts=user_stats['total_workouts'],
                              total_exercises=user_stats['total_exercises'],
                              streak_days=user_stats['streak_days'])
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        traceback.print_exc()
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_exercise', methods=['POST'])
def start_exercise():
    """Start a new exercise based on user selection"""
    global exercise_running, exercise_engine, current_exercise_type
    global exercise_goal, sets_completed, sets_goal
    global workout_start_time
    
    data = request.json
    exercise_type = data.get('exercise_type')
    sets_goal = int(data.get('sets', 3))
    exercise_goal = int(data.get('reps', 10))
    
    # Initialize camera if not already done
    initialize_camera()
    
    # Reset counters
    sets_completed = 0
    workout_start_time = time.time()
    
    # NEW: Use Exercise Engine to load exercise from YAML
    available = get_available_exercises()
    if exercise_type not in available:
        return jsonify({'success': False, 'error': f'Invalid exercise type. Available: {available}'})
    
    # Load exercise
    if not exercise_engine.set_exercise(exercise_type):
        return jsonify({'success': False, 'error': f'Failed to load exercise: {exercise_type}'})
    
    current_exercise_type = exercise_type
    
    # Start the exercise
    exercise_running = True
    
    logger.info(f"Started exercise: {exercise_type}, goal: {exercise_goal} reps x {sets_goal} sets")
    
    return jsonify({
        'success': True,
        'exercise': exercise_type,
        'info': get_exercise_info(exercise_type)
    })

@app.route('/stop_exercise', methods=['POST'])
def stop_exercise():
    """Stop the current exercise and log the workout"""
    global exercise_running, exercise_engine, current_exercise_type
    global workout_start_time, sets_completed, exercise_goal, sets_goal
    
    if exercise_running and exercise_engine.exercise:
        # Calculate duration
        duration = int(time.time() - workout_start_time) if workout_start_time else 0
        
        # Get final form score
        avg_form_score = exercise_engine.exercise.avg_form_score
        
        # Log the workout
        current_counter = exercise_engine.get_counter()
        workout_logger.log_workout(
            exercise_type=current_exercise_type,
            sets=sets_completed + (1 if current_counter > 0 else 0),
            reps=exercise_goal,
            duration_seconds=duration
        )
        
        logger.info(f"Workout stopped. Avg form score: {avg_form_score}")
    
    exercise_running = False
    return jsonify({'success': True})

@app.route('/get_status', methods=['GET'])
def get_status():
    """Return current exercise status"""
    global exercise_engine, sets_completed, exercise_goal, sets_goal, exercise_running
    
    status = {
        'exercise_running': exercise_running,
        'current_reps': exercise_engine.get_counter() if exercise_engine.exercise else 0,
        'current_set': sets_completed + 1 if exercise_running else 0,
        'total_sets': sets_goal,
        'rep_goal': exercise_goal
    }
    
    # Add form score if exercise is running
    if exercise_running and exercise_engine.exercise:
        ex_status = exercise_engine.get_status()
        status['form_score'] = ex_status.get('form_score', 100)
        status['avg_form_score'] = ex_status.get('avg_form_score', 100)
        status['form_grade'] = ex_status.get('form_grade', 'A')
    
    return jsonify(status)

@app.route('/exercises', methods=['GET'])
def list_exercises():
    """Return list of all available exercises"""
    exercises = get_available_exercises()
    exercises_info = {ex: get_exercise_info(ex) for ex in exercises}
    return jsonify({
        'exercises': exercises,
        'info': exercises_info,
        'count': len(exercises)
    })

@app.route('/profile')
def profile():
    """User profile page - placeholder for future development"""
    return "Profile page - Coming soon!"

if __name__ == '__main__':
    try:
        # List available exercises on startup
        exercises = get_available_exercises()
        logger.info(f"Available exercises: {exercises}")
        
        logger.info("Starting the Flask application on http://127.0.0.1:5000")
        print("=" * 50)
        print("🏋️ FITNESS TRAINER WITH POSE ESTIMATION")
        print("=" * 50)
        print(f"📋 Available exercises: {len(exercises)}")
        for ex in exercises:
            print(f"   • {ex}")
        print("-" * 50)
        print("🌐 Open http://127.0.0.1:5000 in your browser")
        print("=" * 50)
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        traceback.print_exc()
