import time


class PID:
    def __init__(self, setpoint: float = 90,
                 input_value: float = 20, kp: float = 1,
                 ki: float = 1, kd: float = 0, forward: bool = True) -> None:
        self.desired_value = setpoint
        self.actual_value = input_value
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.bias = 0
        self.forward = forward

        self.error = 0
        self.last_error = 0
        self.integral_value = 0
        self.derivative_value = 0
        self.windup_guard = 20

        self.proportional_term = 0
        self.integral_term = 0
        self.derivative_term = 0

        self.last_measure = 0

        self.output_min = 0
        self.output_max = 100
        self.sample_time = 100  # ms between measurements
        self.agressive_gap = 15  # °C

        self.setTunings(self.kp, self.ki, self.kd)

        self.last_time = time.time() - self.sample_time
        self.elapsed_time = self.sample_time

    def setTunings(self, kp, ki, kd):
        if kp < 0 or ki < 0 or kd < 0:
            return

        self.kp = kp
        self.ki = ki
        self.kd = kd

        if not self.forward:
            self.kp *= -1
            self.ki *= -1
            self.kd *= -1

    def __old_compute(self, input_value):
        if self.last_time is not None:
            if time.time() - self.last_time < self.sample_time:
                # do nothing
                return None

        self.actual_value = input_value
        current_time = time.time()
        error = self.desired_value - input_value
        delta_time = current_time - self.last_time
        delta_error = error - self.last_error

        p_value = self.kp * error

        self.integral_value += error * delta_time
        self.integral_value = min(self.integral_value, self.windup_guard)
        self.integral_value = max(self.integral_value, -self.windup_guard)

        self.derivative_value = delta_error / delta_time

        # Compute PID Output
        output = p_value + self.ki * self.integral_value + self.kd * \
                 self.derivative_value
        output = min(output, self.output_max)
        output = max(output, self.output_min)

        self.last_measure = self.input
        self.last_time = current_time

        return output

    def compute(self, actual_value):
        self.actual_value = actual_value

        if self.last_time is not None:
            if time.time() - self.last_time < self.sample_time:
                # do nothing
                return None

        self.elapsed_time = time.time() - self.last_time

        self._calculate_error()
        self._calculate_integral()
        self._calculate_derivative()

        output = self._calculate_new_output()
        return output

    def _calculate_error(self):
        # error is negative, if it overshoots
        self.error = self.desired_value - self.actual_value
        self.proportional_term = self.kp * self.error

    def _calculate_integral(self):
        self.integral_value += self.error * self.elapsed_time

        # check boundaries
        self.integral_value = min(self.integral_value, self.windup_guard)
        self.integral_value = max(self.integral_value, -self.windup_guard)

        self.integral_term = self.ki * self.integral_value

    def _calculate_derivative(self):
        self.derivative_value = (self.error - self.last_error
                                 ) / self.elapsed_time
        self.derivative_term = self.kd * self.derivative_value

    def _calculate_new_output(self):
        output = (self.proportional_term +
                  self.integral_term +
                  self.derivative_term +
                  self.bias
                  )

        # check boundaries
        output = min(output, self.output_max)
        output = max(output, self.output_min)

        return output
