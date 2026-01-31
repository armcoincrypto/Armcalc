"""Safe mathematical expression evaluator with scientific functions."""

import math
import re
from dataclasses import dataclass
from typing import Any, Optional, Union

from armcalc.utils.logging import get_logger

logger = get_logger("safe_calc")


@dataclass
class CalcResult:
    """Result of a calculation."""

    success: bool
    value: Optional[Union[int, float]] = None
    error: Optional[str] = None
    expression: str = ""
    formatted: str = ""

    def __str__(self) -> str:
        if self.success:
            return self.formatted or str(self.value)
        return self.error or "Error"


class SafeCalculator:
    """
    Safe mathematical expression evaluator.

    Supports:
    - Basic arithmetic: +, -, *, /, (), ^
    - Percent operations: 100 + 10%, 200 - 5%, etc.
    - Scientific functions: sqrt, sin, cos, tan, log, ln, abs, round, pow
    - Constants: pi, e
    - Trigonometric functions use DEGREES (sin(90) = 1)
    """

    # Allowed functions and constants
    SAFE_FUNCTIONS = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "pow": pow,
        "log": math.log10,  # log base 10
        "ln": math.log,  # natural log
        "sin": lambda x: math.sin(math.radians(x)),  # degrees
        "cos": lambda x: math.cos(math.radians(x)),  # degrees
        "tan": lambda x: math.tan(math.radians(x)),  # degrees
        "asin": lambda x: math.degrees(math.asin(x)),
        "acos": lambda x: math.degrees(math.acos(x)),
        "atan": lambda x: math.degrees(math.atan(x)),
        "floor": math.floor,
        "ceil": math.ceil,
        "exp": math.exp,
        "factorial": math.factorial,
    }

    SAFE_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
    }

    # Pattern for valid expression characters
    VALID_PATTERN = re.compile(
        r"^[\d\s+\-*/().,%^a-zA-Z_]+$"
    )

    # Pattern for function calls
    FUNC_PATTERN = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")

    def __init__(self):
        """Initialize the calculator."""
        self._build_safe_namespace()

    def _build_safe_namespace(self) -> None:
        """Build safe namespace for eval."""
        self._namespace = {}
        self._namespace.update(self.SAFE_FUNCTIONS)
        self._namespace.update(self.SAFE_CONSTANTS)
        # Add __builtins__ as empty to prevent access
        self._namespace["__builtins__"] = {}

    def _preprocess_expression(self, expr: str) -> str:
        """
        Preprocess expression:
        - Replace ^ with ** for power
        - Handle percent operations
        - Normalize whitespace
        """
        # Normalize whitespace
        expr = " ".join(expr.split())

        # Replace ^ with ** for exponentiation
        expr = expr.replace("^", "**")

        # Handle percent operations
        expr = self._convert_percent(expr)

        return expr

    def _convert_percent(self, expr: str) -> str:
        """
        Convert percent notation to calculations.

        Rules:
        - "100 + 10%" -> "100 + (100 * 10 / 100)" = 110
        - "100 - 10%" -> "100 - (100 * 10 / 100)" = 90
        - "100 * 10%" -> "100 * (10 / 100)" = 10
        - "100 / 10%" -> "100 / (10 / 100)" = 1000
        - "10%" alone -> "(10 / 100)" = 0.1
        """
        # Pattern to find percent values
        percent_pattern = re.compile(r"(\d+\.?\d*)\s*%")

        # Find all percent values and their positions
        result = []
        last_end = 0
        tokens = []

        # Tokenize expression
        token_pattern = re.compile(
            r"(\d+\.?\d*%|\d+\.?\d*|[+\-*/()^]|[a-zA-Z_][a-zA-Z0-9_]*)"
        )

        for match in token_pattern.finditer(expr):
            tokens.append((match.group(), match.start(), match.end()))

        if not tokens:
            return expr

        # Process tokens
        output = []
        i = 0
        cumulative_expr = []

        while i < len(tokens):
            token, start, end = tokens[i]

            if token.endswith("%"):
                # This is a percent value
                num = float(token[:-1])

                # Look back to find the operator and the value before it
                if output and len(output) >= 2:
                    # Check if previous token is an operator
                    prev_op = None
                    for j in range(len(output) - 1, -1, -1):
                        if output[j] in "+-":
                            prev_op = output[j]
                            # For + and -, percent is of the cumulative value
                            # Calculate cumulative expression up to the operator
                            base_expr = "".join(output[:j])
                            if base_expr:
                                try:
                                    # Try to evaluate the base
                                    base_val = self._safe_eval(
                                        base_expr.replace("^", "**")
                                    )
                                    if base_val is not None:
                                        pct_val = f"({base_val} * {num} / 100)"
                                        output.append(pct_val)
                                    else:
                                        output.append(f"({num} / 100)")
                                except Exception:
                                    output.append(f"({num} / 100)")
                            else:
                                output.append(f"({num} / 100)")
                            break
                        elif output[j] in "*/":
                            # For * and /, percent is just the fraction
                            output.append(f"({num} / 100)")
                            break
                    else:
                        # No operator found, just use fraction
                        output.append(f"({num} / 100)")
                else:
                    # Standalone percent or at the beginning
                    output.append(f"({num} / 100)")
            else:
                output.append(token)

            i += 1

        return "".join(output)

    def _safe_eval(self, expr: str) -> Optional[Union[int, float]]:
        """Safely evaluate an expression."""
        try:
            result = eval(expr, {"__builtins__": {}}, self._namespace)
            if isinstance(result, (int, float)) and not isinstance(result, bool):
                return result
            return None
        except Exception:
            return None

    def _validate_expression(self, expr: str) -> Optional[str]:
        """
        Validate expression for safety.
        Returns error message if invalid, None if valid.
        """
        # Check for valid characters
        if not self.VALID_PATTERN.match(expr):
            return "Invalid characters in expression"

        # Check for dangerous patterns
        dangerous = [
            "__",
            "import",
            "exec",
            "eval",
            "open",
            "file",
            "input",
            "globals",
            "locals",
            "getattr",
            "setattr",
            "delattr",
            "compile",
            "dir",
            "vars",
        ]
        expr_lower = expr.lower()
        for pattern in dangerous:
            if pattern in expr_lower:
                return f"Forbidden pattern: {pattern}"

        # Check function calls are allowed
        for match in self.FUNC_PATTERN.finditer(expr):
            func_name = match.group(1).lower()
            if func_name not in self.SAFE_FUNCTIONS and func_name not in self.SAFE_CONSTANTS:
                return f"Unknown function: {func_name}"

        return None

    def _format_result(self, value: Union[int, float]) -> str:
        """Format the result for display."""
        if isinstance(value, float):
            # Check if it's essentially an integer
            if value == int(value) and abs(value) < 1e15:
                return str(int(value))
            # Format with appropriate precision
            if abs(value) < 0.0001 or abs(value) > 1e10:
                return f"{value:.6g}"
            # Round to avoid floating point artifacts
            rounded = round(value, 10)
            if rounded == int(rounded):
                return str(int(rounded))
            # Remove trailing zeros
            formatted = f"{rounded:.10f}".rstrip("0").rstrip(".")
            return formatted
        return str(value)

    def calculate(self, expression: str) -> CalcResult:
        """
        Evaluate a mathematical expression safely.

        Args:
            expression: The mathematical expression to evaluate

        Returns:
            CalcResult with success/failure and value/error
        """
        original_expr = expression.strip()

        if not original_expr:
            return CalcResult(
                success=False,
                error="Empty expression",
                expression=original_expr,
            )

        try:
            # Preprocess
            processed = self._preprocess_expression(original_expr)
            logger.debug(f"Preprocessed: '{original_expr}' -> '{processed}'")

            # Validate
            error = self._validate_expression(processed)
            if error:
                return CalcResult(
                    success=False,
                    error=error,
                    expression=original_expr,
                )

            # Evaluate
            result = eval(processed, {"__builtins__": {}}, self._namespace)

            # Check result type
            if not isinstance(result, (int, float)):
                return CalcResult(
                    success=False,
                    error="Result is not a number",
                    expression=original_expr,
                )

            if isinstance(result, bool):
                return CalcResult(
                    success=False,
                    error="Boolean result not allowed",
                    expression=original_expr,
                )

            # Check for special float values
            if isinstance(result, float):
                if math.isnan(result):
                    return CalcResult(
                        success=False,
                        error="Result is NaN (undefined)",
                        expression=original_expr,
                    )
                if math.isinf(result):
                    return CalcResult(
                        success=False,
                        error="Result is infinite",
                        expression=original_expr,
                    )

            formatted = self._format_result(result)

            return CalcResult(
                success=True,
                value=result,
                expression=original_expr,
                formatted=formatted,
            )

        except ZeroDivisionError:
            return CalcResult(
                success=False,
                error="Division by zero",
                expression=original_expr,
            )
        except ValueError as e:
            return CalcResult(
                success=False,
                error=f"Math error: {str(e)}",
                expression=original_expr,
            )
        except SyntaxError:
            return CalcResult(
                success=False,
                error="Invalid syntax",
                expression=original_expr,
            )
        except TypeError as e:
            return CalcResult(
                success=False,
                error=f"Type error: {str(e)}",
                expression=original_expr,
            )
        except Exception as e:
            logger.exception(f"Unexpected error evaluating '{original_expr}'")
            return CalcResult(
                success=False,
                error="Calculation error",
                expression=original_expr,
            )


# Global calculator instance
_calculator: Optional[SafeCalculator] = None


def get_calculator() -> SafeCalculator:
    """Get or create calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = SafeCalculator()
    return _calculator
