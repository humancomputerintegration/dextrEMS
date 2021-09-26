"""HARIOMHARIBOLJAIMATAJIPITAJIKIJAIJAI"""
# Developed by Mark Tomczak (fixermark@gmail.com)
# Python class to calculate PID values

import numpy as np

def _clamp(value, limits):
    lower, upper = limits
    if value is None:
        return None
    elif upper is not None and abs(value) > upper:
        return upper * np.sign(value)
    elif lower is not None and abs(value) < lower:
        return lower * np.sign(value)
    else:
        return value

class PIDController:
    def __init__(self, P, I, D, freq, min=None, max=None):
        self.KP = P
        self.KI = I
        self.KD = D
        self.target = 0

        self.lastError = 0
        self.integrator = 0

        self.output_limits = (min, max)
        self.dt = 1/freq

    def setTarget(self, newTarget):
        self.target = newTarget
        self.integrator = 0

    def step(self, currentValue):
        error = currentValue - self.target

        output = (
            self.KP * error
            + _clamp(self.KI * self.integrator, self.output_limits)
            + self.KD * (error - self.lastError) / self.dt
        )

        output = _clamp(output, self.output_limits)

        self.lastError = error
        self.integrator += error * self.dt

        return output