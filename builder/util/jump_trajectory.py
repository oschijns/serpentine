"""
    Compute a ballistic trajectory
"""


from math import sqrt


class JumpTrajectory:

    # Compute a trajectory from a set of four parameters
    def __init__(self,
        height  : float | None,
        time    : float | None,
        impulse : float | None,
        gravity : float | None):

        # Check which parameters where provided
        mask = 0b0000

        # check a parameter
        def check(n: float | None, m: int, neg: bool = False) -> bool:
            if n is not None:
                mask |= m
                return (n < 0.0) if neg else (n > 0.0)
            return True
        
        # check each of the parameters
        if not check(height , 0b0001): raise Exception("Height cannot be null or negative")
        if not check(time   , 0b0010): raise Exception("Time cannot be null or negative")
        if not check(impulse, 0b0100): raise Exception("Impulse cannot be null or negative")
        if not check(gravity, 0b1000, True): raise Exception("Gravity cannot be null or positive")

        if   mask == 0b0011:
            self.height  =  height
            self.time    =  time
            self.impulse =  2.0 * height / time
            self.gravity = -2.0 * height / time ** 2

        elif mask == 0b0101:
            self.height  =  height
            self.time    =  2.0 * height / impulse
            self.impulse =  impulse
            self.gravity = -0.5 * impulse ** 2 / height

        elif mask == 0b1001:
            self.height  = height
            self.time    = sqrt(2.0 * height / gravity)
            self.impulse = sqrt(2.0 * height * gravity)
            self.gravity = gravity

        elif mask == 0b0110:
            self.height  =  0.5 * time * impulse
            self.time    =  time
            self.impulse =  impulse
            self.gravity = -impulse / time

        elif mask == 0b1010:
            self.height  = -0.5 * gravity * time ** 2
            self.time    =  time
            self.impulse = -gravity * time
            self.gravity =  gravity

        elif mask == 0b1100:
            self.height  = -0.5 * impulse ** 2 / gravity
            self.time    = -impulse / gravity
            self.impulse =  impulse
            self.gravity =  gravity

        else:
            raise Exception("Unsupported combination of parameters where provided")