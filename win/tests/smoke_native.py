"""Real packaged executable integration tests; no browser or computer automation."""
import argparse
import json
import pathlib
import queue
import subprocess
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cli", type=pathlib.Path)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    cli = args.cli.resolve()
    checks = 0

    def run(*command, source=None, success=True):
        nonlocal checks
        result = subprocess.run([str(cli), *command], input=source, capture_output=True, text=True, encoding="utf-8", timeout=240)
        assert (result.returncode == 0) == success, (command, result.stdout, result.stderr)
        checks += 1
        return json.loads(result.stdout)

    if args.install:
        installed = run("install")
        assert installed["ready"] is True
        assert pathlib.Path(installed["path"]).resolve() == cli.parent / "python_embeded"
    assert run("status")["ready"] is True
    half = run("eval", "1/3+1/6")
    assert half["ok"] and half["exact"] == "1/2", half
    assert run("eval", "sin(30)", "--angle", "DEG")["exact"] == "1/2"
    assert run("eval", r"\frac{1}{2}+\frac{1}{3}")["exact"] == "5/6"
    assert run("eval", "det([[1,2],[3,4]])")["exact"] == "-2"
    assert run("eval", "mean([1,2,3,4])")["exact"] == "5/2"
    assert run("eval", "diff(x^3,x)")["ok"] is True
    assert run("eval", "solve(x^2-5*x+6=0,x)")["ok"] is True
    assert "Hello Alice" in run("python", "-", "--input", "Alice", source="print('Hello', input('Name? '))")["output"]
    missing = run("python", "-", source="print(input('Name? '))", success=False)
    assert missing["ok"] is False
    raw = run("request", "-", source=json.dumps({"action":"constants"}))
    assert raw["ok"] is True
    x = {"kind":"symbol","value":"x"}
    square = {"kind":"binary","value":"^","args":[x,{"kind":"number","value":"2"}]}
    graph = run("request", "-", source=json.dumps({"action":"graph","graphKind":"cartesian","trees":[square],"min":-2,"max":2,"samples":41}))
    assert graph["ok"] and len(graph["curves"][0]) > 2, graph
    surface = run("request", "-", source=json.dumps({"action":"graph","graphKind":"surface","trees":[square],"min":-2,"max":2,"surfaceSamples":12}))
    assert surface["ok"] and len(surface["surface"]) > 2, surface
    probability = run("request", "-", source=json.dumps({"action":"probability","category":"distribution","distribution":"normal","operation":"le","values":{"mu":0,"sigma":1,"x":0}}))
    assert probability["ok"] and abs(float(probability["value"])-0.5)<1e-12, probability
    proc = subprocess.Popen([str(cli), "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
    responses = queue.Queue()
    threading.Thread(target=lambda: [responses.put(line) for line in proc.stdout], daemon=True).start()
    def request(message):
        nonlocal checks
        proc.stdin.write(json.dumps(message) + "\n");proc.stdin.flush()
        value = json.loads(responses.get(timeout=30));checks += 1
        assert value["jsonrpc"] == "2.0" and value["id"] == message["id"], value
        return value
    try:
        init = request({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}})
        assert init["result"]["protocolVersion"] == "2025-11-25"
        proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');proc.stdin.flush()
        listed = request({"jsonrpc":"2.0","id":2,"method":"tools/list"})
        assert {t["name"] for t in listed["result"]["tools"]} == {"evaluate","engine_request","python","runtime_status","search_catalog","statistics","solve_equations","list_statistics_datasets","get_statistics_dataset","save_statistics_dataset","get_usage"}
        calculated = request({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"evaluate","arguments":{"expression":"factor(x^2-1)"}}})
        assert calculated["result"]["isError"] is False, calculated
        content = json.loads(calculated["result"]["content"][0]["text"])
        assert content["ok"] is True
        resource = request({"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"symvacas://skill"}})
        assert "name: symvacas" in resource["result"]["contents"][0]["text"]
        bad = request({"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"python","arguments":{"source":"print(input())"}}})
        assert bad["result"]["isError"] is True
        after = request({"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"evaluate","arguments":{"expression":"2+3"}}})
        assert json.loads(after["result"]["content"][0]["text"])["exact"] == "5"
        proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"python","arguments":{"source":"while True: pass"}}})+'\n');proc.stdin.flush()
        time.sleep(0.5)
        proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":7}}\n');proc.stdin.flush()
        cancelled=json.loads(responses.get(timeout=10));checks+=1
        assert cancelled["id"] == 7 and cancelled["result"]["isError"] is True
        recovered=request({"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"evaluate","arguments":{"expression":"6*7"}}})
        assert json.loads(recovered["result"]["content"][0]["text"])["exact"] == "42"
    finally:
        proc.stdin.close()
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill();proc.wait()
    print(f"{checks} native CLI / install / MCP checks passed")


if __name__ == "__main__":
    main()
