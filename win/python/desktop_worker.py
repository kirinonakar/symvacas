"""Private newline JSON bridge. Calculation and user output never share stdout."""
import contextlib
import json
import sys


def main():
    protocol_in, protocol_out = sys.stdin, sys.stdout
    sys.set_int_max_str_digits(0)
    with contextlib.redirect_stdout(sys.stderr):
        import calc_engine
        import script_runner
        import sympy

    def send(message):
        protocol_out.write(json.dumps(message, ensure_ascii=False, allow_nan=False) + "\n")
        protocol_out.flush()

    class InputBridge:
        def __init__(self, request_id, values):
            self.request_id = request_id
            self.values = iter(values)
            self.counter = 0

        def request(self, prompt, output):
            value = next(self.values, None)
            if value is not None:
                return str(value)
            self.counter += 1
            send({"type": "input", "id": self.request_id, "inputId": self.counter,
                  "prompt": prompt, "output": output})
            line = protocol_in.readline()
            if not line:
                raise EOFError("Input cancelled")
            reply = json.loads(line)
            if (reply.get("type") != "input" or reply.get("id") != self.request_id
                    or reply.get("inputId") != self.counter):
                raise EOFError("Invalid input response")
            return str(reply["value"])

    send({"type": "ready", "python": sys.version.split()[0], "sympy": sympy.__version__})
    for line in protocol_in:
        request_id = None
        try:
            message = json.loads(line)
            request_id, request = message["id"], message["request"]
            payload = json.dumps(request, ensure_ascii=False)
            with contextlib.redirect_stdout(sys.stderr):
                if request.get("action") == "python":
                    result = script_runner.run(payload, InputBridge(request_id, request.get("inputs") or []))
                else:
                    result = calc_engine.dispatch(payload)
            send({"type": "result", "id": request_id, "result": json.loads(result)})
        except BaseException as error:
            send({"type": "result", "id": request_id, "result": {"ok": False, "error": str(error)}})


if __name__ == "__main__":
    main()
