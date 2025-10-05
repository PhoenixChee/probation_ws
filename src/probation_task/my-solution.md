# Table of Contents

- [Table of Contents](#table-of-contents)
- [Tools I Use](#tools-i-use)
  - [Visual Studio \& Docker](#visual-studio--docker)
  - [Watching Tutorials](#watching-tutorials)
  - [Cheatsheet](#cheatsheet)
- [How I Programmed the Task](#how-i-programmed-the-task)
  - [1. Understanding Topics](#1-understanding-topics)
  - [2. My Thought Process](#2-my-thought-process)
  - [2. Control Loop (Main Loop) \& Parameters](#2-control-loop-main-loop--parameters)
  - [3. Bounding Box Detection](#3-bounding-box-detection)
  - [4. Go straight the Gate](#4-go-straight-the-gate)
  - [5. Implement client to change vehicle to GUIDED mode](#5-implement-client-to-change-vehicle-to-guided-mode)
  - [6. Debugging](#6-debugging)
- [Video](#video)

# Tools I Use

## Visual Studio & Docker
I didn’t want to install too much software permanently on my computer, so I decided to use Docker to run `ROS Humble-Desktop` inside VS Code. I got this idea from the Club’s [Docker](https://github.com/NTU-Mecatron/Docker) repository.

Thanks to my past experience with Docker on other projects, the setup was straightforward. The only part that differed was configuring the environment correctly.

## Watching Tutorials
I had no experience with ROS or ROS2, so it was overwhelming at first. Nodes, Services, Publishers—it was all new. I followed a [YouTube tutorial](https://www.youtube.com/watch?v=0aPbWsyENA8&list=PLLSegLrePWgJudpPUof4-nVFHGkB62Izy) to learn and program the probation task at the same time.

This is why in my workspace folder there are multiple `.py` programs.

| File Name     | Description                              |
| :------------ | :--------------------------------------- |
| helloworld.py | Understand programming structure         |
| publisher.py  | Control vehicle's movement               |
| subscriber.py | Read data messages from vehicle's topics |
| client.py     | Change vehicle's state                   |
| servive.py    | Test sum function                        |

## Cheatsheet
I initally had alot of trouble initialising the program so I made myself a cheatsheet.

| Description                      | Shell Program                                                                            |
| :------------------------------- | :--------------------------------------------------------------------------------------- |
| Open Port & Connect to Unity     | `$ ros2 run ros_tcp_endpoint default_server_endpoint`                                    |
| Open Port & Connect to Fox Glove | `$ ros2 launch foxglove_bridge foxglove_bridge_launch.xml`                               |
| Build & Initialise               | `$ colcon build --symlink-install` `$ source ~/.bashrc` OR `$ source install/setup.bash` |
| Run                              | `$ ros2 run <workspace folder> <python file>`                                            |
| Create new python program        | `$ touch <name>.py`                                                                      |
| Give File Access Permission      | `$ chmod +x <name>.py`                                                                   |
| Find Topic Info & Data Type      | `$ ros2 topic info <topic>` `$ ros2 interface show <type>`                               |
| Subscribe to Topic               | `$ ros2 topic echo <topic>`                                                              |

# How I Programmed the Task

## 1. Understanding Topics
I found these useful topics on the GUI on Foxglove:  

- `'/mavros/global_position/compass_hdg'` – to set the vehicle’s heading.  
- `'/mavros/global_position/rel_alt'` – to set the vehicle’s depth.  
- `'/main_camera/detection/bounding_boxes'` – to detect objects like the gate.  

I think of them as sensors that give values when needed. So I subscribe to them like this:

```python
self.box_subscriber_ = self.create_subscription(
    BoundingBoxArray, '/main_camera/detection/bounding_boxes', self.box_callback, 10
)
self.compass_subscriber_ = self.create_subscription(
    Float64, '/mavros/global_position/compass_hdg', self.compass_callback, 10
)
self.position_subscriber_ = self.create_subscription(
    Float64, '/mavros/global_position/rel_alt', self.position_callback, 10
)
```
```python
def box_callback(self, msg: BoundingBoxArray):
    boxes = []
    // rest of the program

def compass_callback(self, msg: Float64):
    self.current_heading = float(msg.data)

def position_callback(self, msg: Float64):
    self.current_depth = float(msg.data)
```
With this I play around with `self.get_logger().info()` to figure out how to program the vehicle.

## 2. My Thought Process 
My thought process is that the robot should first face the gate. 
1. To do this, I use the compass topic to control its yaw `angular_z`. 
2. Next, it needs to adjust its depth, which maps to `linear_z`. 
3. Once the depth is correct, the robot should align itself with the center of the gate by using the bounding box data to control laternal direction `linear_y`. 
4. Finally, when everything is aligned, the robot can move forward through the gate using `linear_x`.

## 2. Control Loop (Main Loop) & Parameters 
With my past competitions experience with PD control, I decided why not use them in this scenario (lmao for fun). I set up the control loop where the main program takes place as well as the parameters.

This timer controls the main loop, which must keep running continuously since the robot’s movements need time to reach their target positions. I found that a loop rate of 100 Hz works well, any lower and the robot starts constantly readjusting itself, causing it to oscillate in place.

While it’s possible to increase the loop rate, I don’t see much reason to. A higher rate could improve the responsiveness of the PD control, but 100 Hz is already stable and effective for this task.

```python
self.dt = 0.01  # Control loop interval in seconds
self.timer = self.create_timer(self.dt, self.control_movement)  # Control loop at 100 Hz
```

```python
# Parameters for Box Detection
self.last_boxes = []
self.target_label_name = self.declare_parameter('target_label_name', 'gate').value
self.target_label_id = int(self.declare_parameter('target_label_id', 3).value)
self.det_conf_threshold = self.declare_parameter('det_conf_threshold', 0.70).value
self.target_box = None

self.kp_linear_y = self.declare_parameter('linear_y_kp', 2.5).value
self.kd_linear_y = self.declare_parameter('linear_y_kd', 0.3).value
self.prev_error_y = 0.0
self.max_y_vel = self.declare_parameter('max_y_vel', 2.0).value
```
```python
# Parameters for Heading Control
self.kp_heading = self.declare_parameter('yaw_kp', 0.8).value
self.kd_heading = self.declare_parameter('yaw_kd', 0.12).value
self.prev_error_deg = 0.0
self.max_yaw_rate = self.declare_parameter('max_yaw_rate', 2.0).value
self.target_heading = self.declare_parameter('target_heading', 180.0).value
self.current_heading = None
```
```python
self.kp_depth = self.declare_parameter('depth_kp', 2.0).value
self.max_z_vel = self.declare_parameter('max_z_vel', 1.0).value
self.depth_positive_down = self.declare_parameter('depth_positive_down', True).value
self.invert_z_cmd = self.declare_parameter('invert_z_cmd', False).value
self.target_depth = self.declare_parameter('target_depth', -1.5).value
self.current_depth = None
```

With the control loop in place, its time to send instructions to move the vehicles. I use `/mavros/setpoint_velocity/cmd_vel_unstamped` as it has all the linear & angular movements. This makes it easy to program. 

```python
def control_movement(self):
    cmd = Twist()

    # PD Control for Lateral Movement (Y-axis)
    if self.target_box is not None:
        // rest of the program
        
    # PD Control for Heading
    if self.current_heading is not None:
        // rest of the program
        
    # P Control for Depth
    if self.current_depth is not None:
        // rest of the program

    # Only publish if at least one control value is set (No need Box detection)
    if self.current_heading is not None and self.current_depth is not None:
        self.cmd_movement_.publish(cmd)
        self.get_logger().info(f'LinearXYZ=({cmd.linear.x:.2f}, {cmd.linear.y:.2f}, {cmd.linear.z:.2f}), AngularXYZ=({cmd.angular.x:.2f}, {cmd.angular.y:.2f}, {cmd.angular.z:.2f})')
```

## 3. Bounding Box Detection
The camera detects all objects in view. We only want the target gate, so we filter by confidence and label. 

First, I extract all the data the array has and store it in a seperate array for filtering.

```python
def box_callback(self, msg: BoundingBoxArray):
    boxes = []
    for box in msg.bounding_boxes:
        boxes.append({
            'x': float(box.x),
            'y': float(box.y),
            'w': float(box.w),
            'h': float(box.h),
            'conf': float(getattr(box, 'conf', 0.0)),
            'label_id': int(box.label_id),
            'label_name': str(box.label_name),
        })
    self.last_boxes = boxes

    candidates = [box for box in boxes if self._is_target_box(box)]
    best = self._select_best(candidates)
```
This filters and get rid of the object that are below 70% confidence. Then record the object's name and label. With the date, it ranks the objects based on the cofidence level.
In the Unity simulation, the confidence is always high. (This is useful in the real world setting).
```python
def _is_target_box(self, boxes: dict):
    if boxes['conf'] < self.det_conf_threshold:
        return False
    if self.target_label_id >= 0:
        return boxes['label_id'] == self.target_label_id
    return boxes['label_name'] == self.target_label_name

def _select_best(self, candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    return max(candidates, key=lambda boxes: boxes['conf'])
```
After filtering, the next step is to check if the object is the correct target. Then, extract data from the target object. The values `bounding_box.x` and `bounding_box.y` give the object’s position relative to the camera window. I then calculate the difference between the window’s center and the bounding box’s center. This offset is used to control the vehicle’s movements.
```python
if best is None:
    self.target_box = None
    return

self.target_box = best
self.dx = best['x'] - 0.5
self.dy = best['y'] - 0.5
```

## 4. Go straight the Gate
I initially decided to have the vehicle simulataneously positioning itself and moving forward. However, I faced an issue where it can sometimes miss due to the bounding box detection affecting the lateral movements of the vehicle when it is too close to the gate. Hence, I added a 10-second delay to properly center the vehicle and avoid missing the gate. Once the vehicle is centered, it then moves forward. 

```python
if self.current_heading is not None and self.current_depth is not None:
    now = self.get_clock().now()
    if self.movement_started is None:
        self.movement_started = now
    elapsed = (now - self.movement_started).nanoseconds / 1e9

    cmd.linear.x = 0.3 if elapsed >= 10.0 else 0.0

    self.cmd_movement_.publish(cmd)
    self.get_logger().info(f'LinearXYZ=({cmd.linear.x:.2f}, {cmd.linear.y:.2f}, {cmd.linear.z:.2f}), AngularXYZ=({cmd.angular.x:.2f}, {cmd.angular.y:.2f}, {cmd.angular.z:.2f})')
else:
    self.movement_started = None
```

## 5. Implement client to change vehicle to GUIDED mode
Last but not least, the last step of the program. I use the solution from `minimal.client.py` from the workshop. However this program can only run only once and destroy the node after setting the State. I use AI to quickly solve this last part of the program.

## 6. Debugging
Since a lot of data is being passed around, it’s helpful to use `self.get_logger().info()` throughout the program. These log messages make it easier to understand what’s happening during execution. When they’re no longer needed, they can simply be commented out.

# Video
Click on this [Link](https://drive.google.com/file/d/13zpISHjrLmNuRIPfnkC_khyGlu2zoVut/view?usp=sharing)