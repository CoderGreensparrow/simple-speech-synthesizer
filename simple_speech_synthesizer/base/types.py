"""
Base types used for representing more complex, but universal concepts, like an "envelope".
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

Interp = Literal["linear", "polynomial", "exponential"]

@dataclass(frozen=True)
class Point:
    t: float  # time
    v: float  # value

@dataclass(frozen=True)
class Segment:
    """
    An envelope segment between two points. Describes the type of interpolation between the two points.
    THE REQUIRED params OF THE INTERPOLATION TYPES:
    - linear: None
    - polynomial: { "exponent": float } <- This describes the exponent of the polynomial determining the transition. (percentage**exponent)
    """
    interp: Interp
    params: dict | None = None

    def __post_init__(self):
        if self.interp == "polynomial":
            if self.params is None:
                raise ValueError("Polynomial interpolation requires the 'exponent' parameter, therefore params must not be None.")
            if "exponent" not in self.params.keys():
                raise ValueError("Segment's params must include 'exponent' parameter.")
            if self.params["exponent"] <= 0:
                raise ValueError("Exponent of polynomial interpolation must be positive.")


@dataclass(frozen=True)
class Envelope:
    """
    len(segments) = len(points) - 1, because each segment with index i defines the segment interpolation between points i and i + 1.
    min_t and max_t parameters are not to be set. They are only included for linters to work.
    """
    points: tuple[Point, ...]
    segments: tuple[Segment, ...]
    min_t = None
    max_t = None

    def __post_init__(self):
        if len(self.points) < 2:
            raise ValueError("Envelope must contain at least 2 points.")
        if sorted(self.points, key=lambda p: p.t) != list(self.points):
            raise ValueError("Points in Envelopes must be sorted by t time.")
        if len(self.segments) != len(self.points) - 1:
            raise ValueError(
                "Envelope must contain len(points)-1 segments. (Each nth segment describes the segment between the nth and (n+1)th points.)"
            )

        object.__setattr__(self, "min_t", self.points[0].t)
        object.__setattr__(self, "max_t", self.points[-1].t)

    def get_value(self, t: float):
        """
        NOTE: THIS FUNCTION IS ALMOST NEVER USED OUTSIDE OF THE (TO BE CODED) GUI FOR THE SOFTWARE.
        AT THE LOW LEVEL, ALL Envelopes ARE CONVERTED TO PYO'S CLASSES, AND THOSE CLASSES HANDLE EVERYTHING FROM THERE,
        INCLUDING EVALUATING THE ENVELOPE AT SPECIFIC t TIMEPOINTS.
        Evaluate the envelope at time t.
        Interpolation types are explained in detail in the Segment dataclass' docstring.
        """
        if len(self.points) == 0:
            raise ValueError("Envelope contains no points.")

        if t < self.min_t or t > self.max_t:
            raise ValueError("Envelope is out of range.")

        for i in range(len(self.segments)):
            p0 = self.points[i]
            p1 = self.points[i + 1]
            if p0.t == t:
                return p0.v
            elif p1.t == t:
                return p1.v
            elif p0.t < t < p1.t:
                segment = self.segments[i]
                u = (t - p0.t) / (p1.t - p0.t)  # percentage of t between t0 and t1
                if segment.interp == "linear":
                    return p0.v + u * (p1.v - p0.v)
                elif segment.interp == "polynomial":
                    return p0.v + (u**segment.params["exponent"]) * (p1.v - p0.v)
                raise NotImplementedError(
                    f"Interpolation '{segment.interp}' not implemented."
                )

        raise RuntimeError("Failed to evaluate envelope.")


@dataclass(frozen=True)
class NdimensionalParameterSpace:
    """
    Represents multiple parameters coupled together in a phase space, where each parameter is an axis.
    Used for coarticulation simulation, where:
    - there is a dot moving through the phase space, which represents the state of that space at a time t
    - the dot has movement, speed, acceleration, mass, forces applied, max_speed, or other physics constructs applied to it to move it
    to a pre-defined phase space state TARGET

    Simple example:
    - think of the vowel space. It has two axes.
    - now imagine moving a dot through that vowel space, and the current position of the dot is output.
    - to make a diphthong, start from one point, set a target point, and move between the two in a way that makes the point
    seem to have physics applied to it, and it also has intent (so it doesn't just dumbly accelerate toward the point, it slows down towards the end to make sure it doesn't overshoot the target).
    This whole class is basically this concept, generalized to any type of parameter/axis and N-dimensions.

    This class only represents the "current" (at t time) state of the system.
    To run the simulation, pass an instance of this class to the NdimensionalParameterSpaceSimulator class and let it step through the simulation in delta_t (delta time) segments.

    As this phase space is basically a Euclidean space, the Euclidean magnitude is used to calculate the current velocity.
    So it takes all the current velocities along each axis (velocity vectors), and calculates their velocity (magnitude) is calculated.
    Each square under the root of the formula takes a weight too, see below:
    ||v|| = sqrt(w₁ * v₁² + w₂ * v₂² + w₃ * v₃² ...)
    This can be used to make sure that the parameters have different sense of max_velocity for each of them (which may be useful).
    This can be set in the euclidean_magnitude_weights argument, and needs to contain all the weights for all the axes.
    If not given, then all weights are 1 and the calculation is performed without any weights (aka. normally).

    NOTE: This class is actually never modified, it's a frozen dataclass.
    The simulation returns a new instance of this class with the new data instead. This makes saving single states easier.
    """
    param_names: tuple[str, ...]
    """Each parameter name, aka. each axis name."""
    param_pos: np.typing.NDArray[np.float64]
    """Current values (at initialization, initial values) associated with each of the parameters.
    A position vector in the phase space."""
    param_vel: np.typing.NDArray[np.float64]
    """Current parameter velocities (at initialization, initial velocities), associated with each of the parameters.
    A velocity vector in the phase space."""
    '''max_vel: float
    """Maximum velocity through the n-d phase space, indicated in unit/second."""'''
    '''max_vel: float
    """Max velocity through the n-d phase space. (Will be reached.)"""'''  # TODO uncomment once max_vel is well-implemented
    max_acc: float
    """Max acceleration through the n-d phase space. (Will be reached.)"""
    current_t: float
    """Current t time of the simulation"""
    euclidean_magnitude_weights: tuple[float, ...] | None = None
    """*read class docstring for more info
    If None, then it's treated as just no weights in the calculation."""

    def __post_init__(self):
        if not (len(self.param_names) == len(self.param_pos) == len(self.param_vel)):
            raise ValueError("The number of parameters, their number of initial values, and their number of initial velocities must match upon parameter space creation.")
        """for vel in self.param_vel:
            if vel > self.max_vel:
                raise ValueError("The initialization velocity of all parameters must be less than or equal to max_vel.")""" # TODO fix argument checking
        if self.euclidean_magnitude_weights is not None:
            if len(self.param_names) != len(self.euclidean_magnitude_weights):
                raise ValueError("The number of euclidean maginute weights much match the number of axis, aka. the number of parameters.")
            for weight in self.euclidean_magnitude_weights:
                if weight <= 0:
                    raise ValueError(
                        "The weights of the euclidean magnitude calculation must be positive nonzero numbers.")

@dataclass(frozen=True)
class NdimensionalParameterSpaceTarget:
    """
    Read the docstring of NdimensionalParameterSpace for more info.

    Represents a target of the parameter phase space.
    """
    param_pos: np.typing.NDArray[np.float64]
    """Target parameter values. Make sure the length of this list matches the number of parameters in the simulation.
    A position vector in the phase space."""


class NdimensionalParameterSpaceSimulator:
    """
    Read the docstring of NdimensionalParameterSpace for more info.

    Simulates the movement of the parameters through the N-dimensional parameter phase space towards a target
    in delta_t steps.
    """
    def __init__(self, parameter_space: NdimensionalParameterSpace):
        self.parameter_space = parameter_space

    def get_current_parameter_space(self):
        return self.parameter_space

    def simulate(self, target_state: NdimensionalParameterSpaceTarget, delta_t: float, kp: float = 1, kd: float = 1):
        """
        Steps through the simulation with a time step of delta_t.
        It modifies the original instance of NdimensionalParameterSpace.
        kp and kd determine how acceleration is calculated. Roughly kd should be ≳ 2 * sqrt(kp) for stability. These are the controls of a PD controller.
        """
        # decision logic: if the remaining distance is less than the required breaking distance, then start decelerating
        # calculate breaking distance
        # dis = DISPLACEMENT, not distance
        dis_target = target_state.param_pos - self.parameter_space.param_pos
        dis_target_mag = np.linalg.norm(dis_target)
        unit_direction = dis_target / (dis_target_mag + 1e-12)  # no division by zero ever

        vel_mag = np.linalg.norm(self.parameter_space.param_vel)
        #  breaking_distance = vel_mag ** 2 / (2 * self.parameter_space.max_acc)  ---- part of previous system

        acc = unit_direction * dis_target_mag * kp - self.parameter_space.param_vel * kd  # PD controller (not full PID)

        acc_norm = np.linalg.norm(acc)
        if acc_norm > self.parameter_space.max_acc:
            acc *= self.parameter_space.max_acc / acc_norm

        # update velocity, (and hard velocity clamping later maybe)
        new_vel = self.parameter_space.param_vel + acc * delta_t
        '''new_vel_mag = np.linalg.norm(new_vel)
        if new_vel_mag > self.parameter_space.max_vel:  # if new_speed > max_speed
            new_vel = new_vel * (self.parameter_space.max_vel / new_vel_mag)  # new_speed_vec = new_speed_vec * (max_speed / new_speed)"""'''

        # update position
        new_pos = self.parameter_space.param_pos + new_vel * delta_t

        # return new parameter space
        new_parameter_space = NdimensionalParameterSpace(
            param_names=self.parameter_space.param_names,
            param_pos=new_pos,
            param_vel=new_vel,
            #  max_vel=self.parameter_space.max_vel,  # TODO maybe implement max_vel correctly, not just a hard clamp, but a soft clamp
            max_acc=self.parameter_space.max_acc,
            current_t=self.parameter_space.current_t + delta_t,
            euclidean_magnitude_weights=self.parameter_space.euclidean_magnitude_weights
        )
        self.parameter_space = new_parameter_space

        return new_parameter_space


import matplotlib.pyplot as plt

# assumes your classes are imported:
# NdimensionalParameterSpace, NdimensionalParameterSpaceTarget, NdimensionalParameterSpaceSimulator

def run_test():
    # 2D space (e.g. vowel-like plane)
    param_names = ("x", "y")

    init_pos = np.array([0.0, 0.0], dtype=np.float64)
    init_vel = np.array([0.0, 0.0], dtype=np.float64)

    space = NdimensionalParameterSpace(
        param_names=param_names,
        param_pos=init_pos,
        param_vel=init_vel,
        #  max_vel=300000,
        max_acc=4.0,
        current_t=0.0
    )

    targets = [
        NdimensionalParameterSpaceTarget(param_pos=np.array([0.0, 0.0], dtype=np.float64)),
        NdimensionalParameterSpaceTarget(param_pos=np.array([5.0, 1.0], dtype=np.float64)),
        NdimensionalParameterSpaceTarget(param_pos=np.array([0.0, 5.0], dtype=np.float64))
    ]

    sim = NdimensionalParameterSpaceSimulator(space)

    positions = [space.param_pos.copy()]
    times = [0.0]

    dt = 0.01
    length = 100
    target_i = 0
    for _ in range(int(length / dt)):
        #  print((_+1)/length)
        target = targets[target_i]
        new_state = sim.simulate(target, dt)
        positions.append(new_state.param_pos.copy())
        times.append(new_state.current_t)

        if (_+1) % (1.4 / dt) == 0:
            target_i += 1
        if target_i == len(targets):
            target_i = 0

        # next or stop if close enough
        """if np.linalg.norm(new_state.param_pos - target.param_pos) < 0.1:
            if target_i + 1 < len(targets):
                target_i += 1
            else:
                break"""

    positions = np.array(positions)

    # plot trajectory
    plt.figure()
    plt.plot(positions[:, 0], positions[:, 1], marker=".")
    target_pos_x = []
    target_pos_y = []
    for target in targets:
        target_pos_x.append(target.param_pos[0])
        target_pos_y.append(target.param_pos[1])
    plt.scatter(target_pos_x, target_pos_y, c="red")
    plt.title("Phase space trajectory")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.grid(True)
    plt.show()

    # diagnostics
    print("final pos:", positions[-1])
    print("target:", target.param_pos)
    print("final error:", np.linalg.norm(positions[-1] - target.param_pos))

if __name__ == "__main__":
    run_test()