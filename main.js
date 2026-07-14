import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.28.2/full/pyodide.mjs";

const pyodide = await loadPyodide();
await pyodide.loadPackage("numpy");

// Load your python file
const code = await (await fetch("solver.py")).text();
await pyodide.runPythonAsync(code);

window.solve = async () => {

    const positions =
        document.getElementById("positions").value;

    const binds =
        document.getElementById("binds").value;

    pyodide.globals.set("positions_js", JSON.parse("[" + positions + "]"));
    pyodide.globals.set("binds_js", JSON.parse(binds));

    const result = await pyodide.runPythonAsync(`
solve_lock(positions_js, binds_js)
`);

    document.getElementById("output").textContent = result;
}