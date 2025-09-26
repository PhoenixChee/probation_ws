# AUV Gate Navigation System# AUV Gate Navigation System



This package implements an autonomous underwater vehicle (AUV) control system for gate detection and navigation using ROS 2 and MAVROS.This package implements an autonomous underwater vehicle (AUV) control system for gate detection and navigation using ROS 2 and MAVROS.



## Features## Features



- **Autonomous Gate Detection**: Uses vision_msgs/BoundingBoxArray to detect gates- **Autonomous Gate Detection**: Uses vision_msgs/BoundingBoxArray to detect gates

- **State Machine Control**: Implements a complete mission logic with multiple states- **State Machine Control**: Implements a complete mission logic with multiple states

- **MAVROS Integration**: Controls vehicle through MAVROS topics and services- **MAVROS Integration**: Controls vehicle through MAVROS topics and services

- **Robust Navigation**: Handles imperfect detection (70% success rate) with search patterns- **Robust Navigation**: Handles imperfect detection (70% success rate) with search patterns

- **Adaptive Approach**: Centers gate and approaches dynamically- **Adaptive Approach**: Centers gate and approaches dynamically



## System Architecture## System Architecture



### Main Components### Main Components



1. **AUV Controller** (`auv_controller.py`): Main control node implementing state machine1. **AUV Controller** (`auv_controller.py`): Main control node implementing state machine

2. **Vision Subscriber** (`subscriber.py`): Processes bounding box detections2. **Vision Subscriber** (`subscriber.py`): Processes bounding box detections

3. **System Tester** (`system_tester.py`): Validates system components3. **System Tester** (`system_tester.py`): Validates system components

4. **Launch File** (`auv_navigation.launch.py`): Easy system startup4. **Launch File** (`auv_navigation.launch.py`): Easy system startup



### State Machine Flow### State Machine Flow



``````

INITIALIZING → SETTING_GUIDED_MODE → DESCENDING → SEARCHING → CENTERING → APPROACHING → PASSING_THROUGH → COMPLETEDINITIALIZING → SETTING_GUIDED_MODE → DESCENDING → SEARCHING → CENTERING → APPROACHING → PASSING_THROUGH → COMPLETED

``````



1. **INITIALIZING**: Waits for MAVROS services1. **INITIALIZING**: Waits for MAVROS services

2. **SETTING_GUIDED_MODE**: Sets vehicle to GUIDED mode for autonomous control2. **SETTING_GUIDED_MODE**: Sets vehicle to GUIDED mode for autonomous control

3. **DESCENDING**: Moves down to target depth for gate visibility3. **DESCENDING**: Moves down to target depth for gate visibility

4. **SEARCHING**: Executes horizontal search pattern to locate gate4. **SEARCHING**: Executes horizontal search pattern to locate gate

5. **CENTERING**: Aligns gate to center of camera view5. **CENTERING**: Aligns gate to center of camera view

6. **APPROACHING**: Moves forward while maintaining gate center6. **APPROACHING**: Moves forward while maintaining gate center

7. **PASSING_THROUGH**: Passes through the gate7. **PASSING_THROUGH**: Passes through the gate

8. **COMPLETED**: Mission accomplished8. **COMPLETED**: Mission accomplished



## Setup## Installation and Setup



### Prerequisites### Prerequisites



- ROS 2 (Humble/Iron/Rolling)- ROS 2 (Humble/Iron/Rolling)

- MAVROS- MAVROS

- vision_msgs- vision_msgs

- Unity simulation with gate detection- Unity simulation with gate detection



### Build the Package### Build the Package



```bash```bash

cd /probation_wscd /probation_ws

colcon build --packages-select probation_wscolcon build --packages-select probation_ws

source install/setup.bashsource install/setup.bash

``````



## Usage## Usage



### 1. Test System Components### 1. Test System Components



Before running the full autonomous system, test individual components:Before running the full autonomous system, test individual components:



```bash```bash

ros2 run probation_ws system_testerros2 run probation_ws system_tester

``````



This will test:This will test:

- MAVROS mode service connectivity- MAVROS mode service connectivity

- Velocity command publishing- Velocity command publishing

- Vision system detection- Vision system detection



### 2. Run Individual Components### 2. Run Individual Components



Test individual nodes:Test individual nodes:



```bash```bash

# Test bounding box subscriber# Test bounding box subscriber

ros2 run probation_ws subscriberros2 run probation_ws subscriber



# Test mode switching client# Test mode switching client

ros2 run probation_ws clientros2 run probation_ws client



# Test velocity publisher# Test velocity publisher

ros2 run probation_ws publisherros2 run probation_ws publisher

``````



### 3. Run Full Autonomous System### 3. Run Full Autonomous System



#### Option A: Using Launch File (Recommended)#### Option A: Using Launch File (Recommended)

```bash```bash

ros2 launch probation_ws auv_navigation.launch.pyros2 launch probation_ws auv_navigation.launch.py

``````



#### Option B: Direct Node Execution#### Option B: Direct Node Execution

```bash```bash

ros2 run probation_ws auv_controllerros2 run probation_ws auv_controller

``````



### 4. Monitor System Status### 4. Monitor System Status



```bash```bash

# View all active topics# View all active topics

ros2 topic listros2 topic list



# Monitor velocity commands# Monitor velocity commands

ros2 topic echo /mavros/setpoint_velocity/cmd_vel_unstampedros2 topic echo /mavros/setpoint_velocity/cmd_vel_unstamped



# Monitor gate detections# Monitor gate detections

ros2 topic echo /main_camera/detection/bounding_boxesros2 topic echo /main_camera/detection/bounding_boxes



# Check node status# Check node status

ros2 node listros2 node list

``````



## Configuration Parameters## Configuration Parameters



### Control Parameters (in `auv_controller.py`)### Control Parameters (in `auv_controller.py`)



```python```python

# Speed settings# Speed settings

self.max_linear_speed = 1.0       # Maximum linear velocity (m/s)self.max_linear_speed = 1.0       # Maximum linear velocity (m/s)

self.max_angular_speed = 0.5      # Maximum angular velocity (rad/s)self.max_angular_speed = 0.5      # Maximum angular velocity (rad/s)

self.target_depth_speed = 0.3     # Descent speedself.target_depth_speed = 0.3     # Descent speed

self.approach_speed = 0.5         # Forward approach speedself.approach_speed = 0.5         # Forward approach speed

self.search_speed = 0.3           # Search pattern speedself.search_speed = 0.3           # Search pattern speed

self.centering_gain = 2.0         # PID gain for centeringself.centering_gain = 2.0         # PID gain for centering



# Mission timing# Mission timing

self.target_depth_time = 10.0     # Descent time (seconds)self.target_depth_time = 10.0     # Descent time (seconds)

self.search_pattern_time = 5.0    # Time per search directionself.search_pattern_time = 5.0    # Time per search direction

self.pass_through_time = 5.0      # Time to pass through gateself.pass_through_time = 5.0      # Time to pass through gate



# Detection thresholds  # Detection thresholds  

self.min_confidence = 0.5         # Minimum detection confidenceself.min_confidence = 0.5         # Minimum detection confidence

self.approach_threshold = 0.6     # Gate width to start passing throughself.approach_threshold = 0.6     # Gate width to start passing through

``````



### Vision Parameters (in `subscriber.py`)### Vision Parameters (in `subscriber.py`)



```python```python

self.min_confidence = 0.5         # Minimum detection confidenceself.min_confidence = 0.5         # Minimum detection confidence

self.center_tolerance = 0.1       # Centering accuracy toleranceself.center_tolerance = 0.1       # Centering accuracy tolerance

``````



## Topics and Services## Topics and Services



### Subscribed Topics### Subscribed Topics

- `/main_camera/detection/bounding_boxes` (vision_msgs/BoundingBoxArray): Gate detection data- `/main_camera/detection/bounding_boxes` (vision_msgs/BoundingBoxArray): Gate detection data



### Published Topics### Published Topics

- `/mavros/setpoint_velocity/cmd_vel_unstamped` (geometry_msgs/Twist): Main velocity commands- `/mavros/setpoint_velocity/cmd_vel_unstamped` (geometry_msgs/Twist): Main velocity commands

- `/mavros/setpoint_velocity/cmd_vel_unstamped/x` (std_msgs/Float32): X-axis velocity- `/mavros/setpoint_velocity/cmd_vel_unstamped/x` (std_msgs/Float32): X-axis velocity

- `/mavros/setpoint_velocity/cmd_vel_unstamped/y` (std_msgs/Float32): Y-axis velocity  - `/mavros/setpoint_velocity/cmd_vel_unstamped/y` (std_msgs/Float32): Y-axis velocity  

- `/mavros/setpoint_velocity/cmd_vel_unstamped/z` (std_msgs/Float32): Z-axis velocity- `/mavros/setpoint_velocity/cmd_vel_unstamped/z` (std_msgs/Float32): Z-axis velocity



### Service Clients### Service Clients

- `/mavros/set_mode` (mavros_msgs/SetMode): Flight mode control- `/mavros/set_mode` (mavros_msgs/SetMode): Flight mode control



## License## Troubleshooting



MIT License - see LICENSE file for details.### Common Issues

1. **"service not available, waiting again..."**
   - Ensure MAVROS is running and connected to vehicle
   - Check if simulation is running

2. **"No gate detected"**
   - Verify camera is working and gate is in view
   - Check lighting and gate visibility
   - Adjust `min_confidence` threshold if needed

3. **Vehicle not responding to commands**
   - Ensure vehicle is in GUIDED mode
   - Check if MAVROS is properly connected
   - Verify velocity topic names

4. **Simulation reset needed**
   - If vehicle starts facing obstacle, reset simulation
   - Adjust initial position in simulation

### Debug Commands

```bash
# Check MAVROS connection
ros2 topic echo /mavros/state

# Monitor vehicle position
ros2 topic echo /mavros/local_position/pose

# Check active flight mode
ros2 service call /mavros/get_mode mavros_msgs/srv/GetMode

# Manually set flight mode
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"
```

## Safety Features

- **Mode Management**: Automatically sets GUIDED mode for autonomous control
- **State Validation**: Checks for gate detection before state transitions  
- **Velocity Limiting**: Enforces maximum speed limits
- **Graceful Shutdown**: Stops all movement on completion or failure

## Customization

### Modifying Search Pattern

Edit the `handle_searching()` method in `auv_controller.py`:

```python
def handle_searching(self, time_in_state):
    # Current: horizontal sweep
    # Modify for different patterns (circular, spiral, etc.)
```

### Adjusting Gate Detection Logic

Modify `subscriber.py` to change detection criteria:

```python
def listener_callback(self, msg):
    # Add custom filtering logic
    # Adjust confidence thresholds
    # Implement object class filtering
```

### Adding Obstacle Avoidance

Extend the state machine to include obstacle detection and avoidance logic in the APPROACHING state.

## Performance Notes

- **Detection Rate**: System handles ~70% detection success rate through continuous searching
- **Update Rate**: 10 Hz control loop for responsive navigation
- **Centering Accuracy**: ±0.1 normalized coordinates (configurable)
- **Mission Time**: Typically 30-60 seconds depending on initial conditions

## License

MIT License - see LICENSE file for details.

## Support

For questions or issues:
1. Check the troubleshooting section above
2. Review ROS 2 logs for error messages
3. Test individual components with system_tester
4. Verify MAVROS and simulation connectivity